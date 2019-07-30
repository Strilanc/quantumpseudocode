import math
import random
from typing import Optional, Union, Tuple, Iterable, Iterator

import cirq

import quantumpseudocode as qp
from quantumpseudocode.ops import Operation, semi_quantum


def do_classical_xor_lookup(sim_state: 'qp.ClassicalSimState',
                            *,
                            lvalue: 'qp.IntBuf',
                            table: 'qp.LookupTable',
                            address: int,
                            phase_instead_of_toggle: bool = False):
    mask = table.values[address]
    assert 0 <= address < len(table)
    if phase_instead_of_toggle:
        if popcnt(int(lvalue) & mask) & 1:
            sim_state.phase_degrees += 180
    else:
        lvalue ^= mask


@semi_quantum(classical=do_classical_xor_lookup, alloc_prefix='_qrom_')
def do_xor_lookup(*,
                  lvalue: 'qp.Quint',
                  table: 'qp.LookupTable',
                  address: 'qp.Quint.Borrowed',
                  phase_instead_of_toggle: bool = False,
                  control: 'qp.Qubit.Control' = True):
    assert isinstance(lvalue, qp.Quint)
    assert isinstance(address, qp.Quint)
    assert isinstance(control, qp.QubitIntersection) and len(control.qubits) <= 1
    table = table[:1 << len(address)]
    max_active_address_bits = qp.ceil_lg2(len(table))
    address = address[:max_active_address_bits]

    # Base case: single distinct value in table.
    if all(e == table[0] for e in table):
        if phase_instead_of_toggle:
            for k in range(len(lvalue)):
                if table[0] & (1 << k):
                    qp.emit(qp.OP_PHASE_FLIP.controlled_by(control & lvalue[k]))
        else:
            lvalue ^= table[0] & qp.controlled_by(control)
        return

    # Recursive case: divide and conquer.
    high_bit = address[-1]
    rest = address[:-1]
    h = 1 << (len(address) - 1)
    low_table = table[:h]
    high_table = table[h:]
    with qp.hold(control & high_bit, name='_lookup_prefix') as q:
        # Do lookup for half of table where high_bit is 0.
        q ^= control  # Flip q to storing 'controls & ~high_bit'.
        op = XorLookup(lvalue=lvalue,
                       table=low_table,
                       address=rest,
                       phase_instead_of_toggle=phase_instead_of_toggle)
        qp.emit(op.controlled_by(q))
        q ^= control

        # Do lookup for half of table where high_bit is 1.
        op = XorLookup(lvalue=lvalue,
                       table=high_table,
                       address=rest,
                       phase_instead_of_toggle=phase_instead_of_toggle)
        qp.emit(op.controlled_by(q))


@cirq.value_equality
class XorLookup(Operation):
    def __init__(self, lvalue: 'qp.Quint', table: 'qp.LookupTable', address: 'qp.Quint.Borrowed', phase_instead_of_toggle: bool):
        self.lvalue = lvalue
        self.table = table
        self.address = address
        self.phase_instead_of_toggle = phase_instead_of_toggle

    def _value_equality_values_(self):
        return self.lvalue, self.table, self.address, self.phase_instead_of_toggle

    def emit_ops(self, controls: 'qp.QubitIntersection'):
        do_xor_lookup(lvalue=self.lvalue,
                      table=self.table,
                      address=self.address,
                      phase_instead_of_toggle=self.phase_instead_of_toggle,
                      control=controls)

    def mutate_state(self, sim_state: 'qp.ClassicalSimState', forward: bool) -> None:
        do_xor_lookup.classical(
            lvalue=self.lvalue,
            table=self.table,
            address=self.address,
            phase_instead_of_toggle=self.phase_instead_of_toggle)

    def __str__(self):
        return '{} ^{}= {}[{}]'.format(
            self.lvalue,
            'Z' if self.phase_instead_of_toggle else '',
            self.table,
            self.address)

    def __repr__(self):
        return 'qp.XorTableLookup({!r}, {!r}, {!r}, {!r})'.format(self.lvalue, self.table, self.address, self.phase_instead_of_toggle)

    def inverse(self):
        return self


class LookupRValue(qp.RValue[int]):
    """Represents the temporary result of a table lookup."""

    def __init__(self, table: qp.LookupTable, address: 'qp.Quint'):
        # Drop high bits that would place us beyond the range of the table.
        max_address_len = qp.ceil_lg2(len(table))
        # Drop inaccessible parts of table.
        max_table_len = 1 << len(address)

        self.table = table[:max_table_len]
        self.address = address[:max_address_len]

    def resolve(self, sim_state: 'qp.ClassicalSimState', allow_mutate: bool):
        address = self.address.resolve(sim_state, False)
        return self.table.values[address]

    def __rixor__(self, other):
        if isinstance(other, qp.Quint):
            qp.emit(XorLookup(lvalue=other,
                              table=self.table,
                              address=self.address,
                              phase_instead_of_toggle=False))
            return other

        return NotImplemented

    def qureg_deps(self) -> Iterable['qp.Qureg']:
        return [self.address.qureg]

    def value_from_resolved_deps(self, args: Tuple[int]) -> int:
        return self.table[args[0]]

    def make_storage_location(self,
                              name: Optional[str] = None) -> 'qp.Quint':
        return qp.Quint(qp.NamedQureg(name, self.table.output_len()))

    def init_storage_location(self,
                              location: 'qp.Quint',
                              controls: 'qp.QubitIntersection'):
        qp.emit(XorLookup(
            lvalue=location,
            table=self.table,
            address=self.address,
            phase_instead_of_toggle=False
        ).controlled_by(controls))

    def del_storage_location(self,
                             location: 'qp.Quint',
                             controls: 'qp.QubitIntersection'):
        if len(location) == 0:
            return

        address_count = min(1 << len(self.address), len(self.table))
        if address_count == 1:
            location ^= self.table[0] & qp.controlled_by(controls)
            return

        n = qp.ceil_lg2(address_count)
        k = min(n >> 1, qp.floor_lg2(len(location)))
        low = self.address[:k]
        high = self.address[k:n]
        assert len(low) >= 0
        assert len(high) >= 0

        # Determine fixups by performing eager measurements.
        fixups = [0] * (1 << len(high))
        for i in range(len(location)):
            if qp.measure_x_for_phase_fixup_and_reset(location[i]):
                for j in range(address_count):
                    if self.table[j] & (1 << i):
                        fixup_index = j >> k
                        fixup_bit = j & ((1 << k) - 1)
                        fixups[fixup_index] ^= 1 << fixup_bit
        fixup_table = qp.LookupTable(fixups)

        # Phase fixups.
        unary_storage = location[:1<<k]
        unary_storage.init(1 << low)
        qp.emit(XorLookup(
            lvalue=unary_storage,
            table=fixup_table,
            address=high,
            phase_instead_of_toggle=True
        ).controlled_by(controls))
        unary_storage.clear(1 << low)

    def __str__(self):
        return 'T(len={})[{}]'.format(len(self.table), self.address)

    def __repr__(self):
        return 'qp.LookupRValue({!r}, {!r})'.format(self.table, self.address)


def popcnt(v: int) -> int:
    assert v >= 0
    t = 0
    while v:
        v &= v - 1
        t += 1
    return t
