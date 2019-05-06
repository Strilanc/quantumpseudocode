from typing import List, Optional, Union, Tuple, Callable, Any, Iterable

import numpy as np

import quantumpseudocode
from quantumpseudocode.ops.operation import Operation


def _flatten(x):
    if isinstance(x, int):
        return [x]
    return tuple(item
                 for sub_list in x
                 for item in _flatten(sub_list))

class LookupTable:
    def __init__(self, values: Union[Iterable[int], Iterable[Iterable[int]]]):
        self.values = _flatten(values)
        assert len(self.values) > 0
        assert all(e >= 0 for e in self.values)

    def output_len(self):
        return max(e.bit_length() for e in self.values)

    def __len__(self):
        return len(self.values)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.values[item]
        if isinstance(item, slice):
            return LookupTable(self.values[item])
        if isinstance(item, tuple):
            if all(isinstance(e, quantumpseudocode.Quint) for e in item):
                reg = quantumpseudocode.RawQureg(q for e in item[::-1] for q in e)
                return LookupRValue(self, quantumpseudocode.Quint(reg))
        if isinstance(item, quantumpseudocode.Quint):
            return LookupRValue(self, item)
        return NotImplemented

    def __repr__(self):
        return 'quantumpseudocode.LookupTable({!r})'.format(self.values)


class XorLookupOperation(Operation):
    def __init__(self,
                 lvalue: 'quantumpseudocode.Quint',
                 lookup: 'quantumpseudocode.LookupRValue',
                 phase_instead_of_toggle: bool = False):
        self.lvalue = lvalue
        self.lookup = lookup
        self.phase_instead_of_toggle = phase_instead_of_toggle

    def __str__(self):
        return '{} ^{}= {}'.format(
            self.lvalue,
            'Z' if self.phase_instead_of_toggle else '',
            self.lookup)

    def __repr__(self):
        return 'quantumpseudocode.XorLookupOperation({!r}, {!r}, {!r})'.format(
            self.lvalue,
            self.lookup,
            self.phase_instead_of_toggle)

    def permutation_registers(self):
        return self.lookup.address, self.lvalue.qureg

    def permute(self, forward: bool, args: Tuple[int, ...]) -> Tuple[int, ...]:
        return args[0], args[1] ^ self.lookup.table[args[0]]

    def inverse(self):
        return self

    def do(self, controls: quantumpseudocode.QubitIntersection):
        # Base case: single distinct value in table.
        if all(e == self.lookup.table[0] for e in self.lookup.table):
            self.lookup.address ^= -1
            with quantumpseudocode.condition(controls):
                self.lvalue ^= self.lookup.table[0]
            self.lookup.address ^= -1
            return ()

        # Recursive case: divide and conquer.
        high_bit = self.lookup.address[-1]
        rest = self.lookup.address[:-1]
        h = 1 << (len(self.lookup.address) - 1)
        low_table = self.lookup.table[:h]
        high_table = self.lookup.table[h:]
        with quantumpseudocode.hold(controls & high_bit, name='_lookup_prefix') as q:
            # Do lookup for half of table where highBit is 0.
            q ^= controls  # Flip q to storing 'controls & ~high_bit'.
            op = XorLookupOperation(self.lvalue,
                                    low_table[rest],
                                    self.phase_instead_of_toggle)
            quantumpseudocode.emit(op.controlled_by(q))
            q ^= controls

            # Do lookup for half of table where highBit is 1.
            op = XorLookupOperation(self.lvalue,
                                    high_table[rest],
                                    self.phase_instead_of_toggle)
            quantumpseudocode.emit(op.controlled_by(q))


class LookupRValue(quantumpseudocode.RValue):
    def __init__(self, table: LookupTable, address: 'quantumpseudocode.Quint'):
        # Drop high bits that would place us beyond the range of the table.
        max_address_len = quantumpseudocode.ceil_lg2(len(table))
        # Drop inaccessible parts of table.
        max_table_len = 1 << len(address)

        self.table = table[:max_table_len]
        self.address = address[:max_address_len]

    def __rixor__(self, other):
        if isinstance(other, quantumpseudocode.Quint):
            quantumpseudocode.emit(XorLookupOperation(other, self))
            return other

        return NotImplemented

    def make_storage_location(self,
                              name: Optional[str] = None) -> 'quantumpseudocode.Quint':
        return quantumpseudocode.Quint(quantumpseudocode.NamedQureg(name, self.table.output_len()))

    def init_storage_location(self,
                              location: 'quantumpseudocode.Quint',
                              controls: 'quantumpseudocode.QubitIntersection'):
        with quantumpseudocode.condition(controls):
            location ^= self

    def del_storage_location(self,
                             location: 'quantumpseudocode.Quint',
                             controls: 'quantumpseudocode.QubitIntersection'):
        address_count = min(1 << len(self.address), len(self.table))
        n = quantumpseudocode.ceil_lg2(address_count)
        k = min(n >> 1, quantumpseudocode.floor_lg2(len(location)))
        low = self.address[:k]
        high = self.address[k:n]

        # Determine fixups by performing eager measurements.
        fixups = [0] * address_count
        for i in range(len(location)):
            if quantumpseudocode.measure_x_for_phase_fixup_and_reset(location[i]):
                for j in range(address_count):
                    if self.table[j] & (1 << i):
                        fixup_index = j >> k
                        fixup_bit = j & ((1 << k) - 1)
                        fixups[fixup_index] ^= 1 << fixup_bit
        fixup_table = LookupTable(fixups)

        # Phase fixups.
        unary_storage = location[:1<<k]
        quantumpseudocode.emit(quantumpseudocode.LetUnary(lvalue=unary_storage, binary=low))
        quantumpseudocode.emit(XorLookupOperation(
            lvalue=unary_storage,
            lookup=fixup_table[high],
            phase_instead_of_toggle=True
        ).controlled_by(controls))
        quantumpseudocode.emit(quantumpseudocode.LetUnary(lvalue=unary_storage, binary=low).inverse())

    def __str__(self):
        return 'T(len={})[{}]'.format(len(self.table), self.address)

    def __repr__(self):
        return 'quantumpseudocode.LookupRValue({!r}, {!r})'.format(self.table, self.address)
