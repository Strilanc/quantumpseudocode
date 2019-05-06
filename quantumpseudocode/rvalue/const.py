from typing import Optional, Any, Tuple, Iterable

import cirq

import quantumpseudocode
from .rvalue import RValue


@cirq.value_equality
class BoolRValue(RValue[bool]):
    def __init__(self, val: bool):
        self.val = val

    def _value_equality_values_(self):
        return self.val

    def permutation_registers(self) -> Iterable['quantumpseudocode.Qureg']:
        return []

    def permutation_registers_from_value(self, val: bool) -> Tuple[int, ...]:
        assert val == self.val
        return ()

    def value_from_permutation_registers(self, args: Tuple[int, ...]
                                         ) -> bool:
        return self.val

    def make_storage_location(self, name: Optional[str] = None):
        return quantumpseudocode.Qubit(name)

    def init_storage_location(self,
                              location: 'quantumpseudocode.Qubit',
                              controls: 'quantumpseudocode.QubitIntersection'):
        with quantumpseudocode.condition(controls):
            location ^= self.val

    # def del_storage_location(self,
    #                          location: 'quantumpseudocode.Qubit',
    #                          controls: 'quantumpseudocode.QubitIntersection'):
    #     if quantumpseudocode.measure_x_for_phase_fixup_and_reset(location):
    #         quantumpseudocode.phase_flip(controls)

    def __str__(self):
        return 'rval({})'.format(self.val)

    def __repr__(self):
        return 'quantumpseudocode.BoolRValue({!r})'.format(self.val)


@cirq.value_equality
class IntRValue(RValue[bool]):
    def __init__(self, val: int):
        self.val = val

    def _value_equality_values_(self):
        return self.val

    def permutation_registers(self) -> Iterable['quantumpseudocode.Qureg']:
        return []

    def value_from_permutation_registers(self, args: Tuple[int, ...]
                                         ) -> int:
        return self.val

    def permutation_registers_from_value(self, val: int) -> Tuple[int, ...]:
        assert val == self.val
        return ()

    def make_storage_location(self, name: str = ''):
        return quantumpseudocode.Quint(quantumpseudocode.NamedQureg(name, self.val.bit_length()))

    def init_storage_location(self,
                              location: 'quantumpseudocode.Quint',
                              controls: 'quantumpseudocode.QubitIntersection'):
        with quantumpseudocode.condition(controls):
            location ^= self.val

    # def del_storage_location(self,
    #                          location: 'quantumpseudocode.Quint',
    #                          controls: 'quantumpseudocode.QubitIntersection'):
    #     r = quantumpseudocode.measure_x_for_phase_fixup_and_reset(location)
    #     if quantumpseudocode.popcnt(r & self.val) & 1:
    #         quantumpseudocode.phase_flip(controls)

    def __str__(self):
        return 'rval({})'.format(self.val)

    def __repr__(self):
        return 'quantumpseudocode.IntRValue({!r})'.format(self.val)
