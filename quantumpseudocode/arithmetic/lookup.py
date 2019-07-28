from typing import Optional, Union, Tuple, Iterable, Iterator

import quantumpseudocode as qp
from quantumpseudocode.ops import Op


def _flatten(x: Union[int, Iterable]) -> Iterator[int]:
    if isinstance(x, int):
        yield x
    else:
        for item in x:
            yield from _flatten(item)


class LookupTable:
    """A classical list that supports quantum addressing."""

    def __init__(self,
                 values: Union[Iterable[int], Iterable[Iterable[int]]]):
        self.values = tuple(_flatten(values))
        assert len(self.values) > 0
        assert all(e >= 0 for e in self.values)

    def output_len(self) -> int:
        return max(e.bit_length() for e in self.values)

    def __len__(self):
        return len(self.values)

    def __getitem__(self, item):
        if isinstance(item, bool):
            return self.values[int(item)]
        if isinstance(item, int):
            return self.values[item]
        if isinstance(item, slice):
            return LookupTable(self.values[item])
        if isinstance(item, tuple):
            if all(isinstance(e, qp.Quint) for e in item):
                reg = qp.RawQureg(q for e in item[::-1] for q in e)
                return LookupRValue(self, qp.Quint(reg))
        if isinstance(item, qp.Quint):
            return LookupRValue(self, item)
        if isinstance(item, qp.Qubit):
            return LookupRValue(self, qp.Quint(qp.RawQureg([item])))
        raise NotImplementedError('Strange index: {}'.format(item))

    def __repr__(self):
        return 'qp.LookupTable({!r})'.format(self.values)


class XorLookup(Op):
    @staticmethod
    def emulate(*,
                lvalue: 'qp.IntBuf',
                table: 'qp.LookupTable',
                address: 'int',
                phase_instead_of_toggle: bool):
        if not phase_instead_of_toggle:
            lvalue ^= table[address]

    @staticmethod
    def do(controls: 'qp.QubitIntersection',
           *,
           lvalue: 'qp.Quint',
           table: 'qp.LookupTable',
           address: 'qp.Quint',
           phase_instead_of_toggle: bool):
        table = table[:1 << len(address)]

        # Base case: single distinct value in table.
        if all(e == table[0] for e in table):
            address ^= -1
            with qp.controlled_by(controls):
                lvalue ^= table[0]
            address ^= -1
            return ()

        # Recursive case: divide and conquer.
        high_bit = address[-1]
        rest = address[:-1]
        h = 1 << (len(address) - 1)
        low_table = table[:h]
        high_table = table[h:]
        with qp.hold(controls & high_bit, name='_lookup_prefix') as q:
            # Do lookup for half of table where high_bit is 0.
            q ^= controls  # Flip q to storing 'controls & ~high_bit'.
            op = XorLookup(lvalue=lvalue,
                           table=low_table,
                           address=rest,
                           phase_instead_of_toggle=phase_instead_of_toggle)
            qp.emit(op.controlled_by(q))
            q ^= controls

            # Do lookup for half of table where high_bit is 1.
            op = XorLookup(lvalue=lvalue,
                           table=high_table,
                           address=rest,
                           phase_instead_of_toggle=phase_instead_of_toggle)
            qp.emit(op.controlled_by(q))

    @staticmethod
    def describe(*, lvalue, table, address, phase_instead_of_toggle):
        return '{} ^{}= {}[{}]'.format(
            lvalue,
            'Z' if phase_instead_of_toggle else '',
            table,
            address)

    def inverse(self):
        return self


class LookupRValue(qp.RValue[int]):
    """Represents the temporary result of a table lookup."""

    def __init__(self, table: LookupTable, address: 'qp.Quint'):
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
        fixup_table = LookupTable(fixups)

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
