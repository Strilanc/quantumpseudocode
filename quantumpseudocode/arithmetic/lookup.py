from typing import Optional, Tuple, Iterable, List

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
        if qp.popcnt(int(lvalue) & mask) & 1:
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
    address = address[:qp.ceil_lg2(len(table))]

    # Base case: single distinct value in table.
    if all(e == table[0] for e in table):
        if phase_instead_of_toggle:
            for k in range(len(lvalue)):
                if table[0] & (1 << k):
                    qp.emit(qp.OP_PHASE_FLIP, control & lvalue[k])
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
        do_xor_lookup(lvalue=lvalue,
                      table=low_table,
                      address=rest,
                      phase_instead_of_toggle=phase_instead_of_toggle,
                      control=q)
        q ^= control

        # Do lookup for half of table where high_bit is 1.
        do_xor_lookup(lvalue=lvalue,
                      table=high_table,
                      address=rest,
                      phase_instead_of_toggle=phase_instead_of_toggle,
                      control=q)


@semi_quantum(alloc_prefix='_qrom_', classical=do_classical_xor_lookup)
def del_xor_lookup(*,
                   lvalue: 'qp.Quint',
                   table: 'qp.LookupTable',
                   address: 'qp.Quint.Borrowed',
                   control: 'qp.Qubit.Control' = True):
    """Uncomputes a table lookup using measurement based uncomputation."""
    assert isinstance(lvalue, qp.Quint)
    assert isinstance(address, qp.Quint)
    assert isinstance(control, qp.QubitIntersection) and len(control.qubits) <= 1
    table = table[:1 << len(address)]
    address = address[:qp.ceil_lg2(len(table))]

    if all(e == table[0] for e in table):
        qp.IntRValue(table[0]).del_storage_location(lvalue, control)
        return

    split = min(
        qp.floor_lg2(len(lvalue)),  # Point of no-more-workspace-available.
        len(address) // 2  # Point of optimal operation count.
    )
    low = address[:split]
    high = address[split:]

    with qp.measurement_based_uncomputation(lvalue) as result:
        # Infer whether or not each address has a phase flip.
        raw_fixups = [bool(qp.popcnt(result & table[k]) & 1)
                      for k in range(len(table))]
        fixup_table = qp.LookupTable(_chunk_bits(raw_fixups, 1 << split))

        # Fix address phase flips using a smaller table lookup.
        unary_storage = lvalue[:1 << split]
        unary_storage.init(1 << low)
        do_xor_lookup(
            lvalue=unary_storage,
            table=fixup_table,
            address=high,
            phase_instead_of_toggle=True,
            control=control)
        unary_storage.clear(1 << low)


def _chunk_bits(bits: List[bool], size: int) -> List[int]:
    return [
        qp.little_endian_int(bits[k:k + size])
        for k in range(0, len(bits), size)
    ]


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
        other, controls = qp.ControlledLValue.split(other)
        if controls == qp.QubitIntersection.NEVER:
            return other

        if isinstance(other, qp.Quint):
            qp.arithmetic.do_xor_lookup(
                lvalue=other,
                table=self.table,
                address=self.address,
                phase_instead_of_toggle=False,
                control=controls)
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
        do_xor_lookup(
            lvalue=location,
            table=self.table,
            address=self.address,
            phase_instead_of_toggle=False,
            control=controls)

    def del_storage_location(self,
                             location: 'qp.Quint',
                             controls: 'qp.QubitIntersection'):
        del_xor_lookup(
            lvalue=location,
            table=self.table,
            address=self.address,
            control=controls)

    def __str__(self):
        return 'T(len={})[{}]'.format(len(self.table), self.address)

    def __repr__(self):
        return 'qp.LookupRValue({!r}, {!r})'.format(self.table, self.address)
