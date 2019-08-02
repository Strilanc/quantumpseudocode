from typing import Optional, Any, Tuple, Iterable

import cirq

import quantumpseudocode as qp
from .rvalue import RValue


@cirq.value_equality
class BoolRValue(RValue[bool]):
    def __init__(self, val: bool):
        self.val = val

    def trivial_unwrap(self):
        return self.val

    def resolve(self, sim_state: 'qp.ClassicalSimState', allow_mutate: bool):
        return self.val

    def _value_equality_values_(self):
        return self.val

    def qureg_deps(self) -> Iterable['qp.Qureg']:
        return []

    def value_from_resolved_deps(self, args: Tuple[int, ...]
                                 ) -> bool:
        return self.val

    def make_storage_location(self, name: Optional[str] = None):
        return qp.Qubit(name)

    def init_storage_location(self,
                              location: 'qp.Qubit',
                              controls: 'qp.QubitIntersection'):
        location ^= self.val & qp.controlled_by(controls)

    def del_storage_location(self,
                             location: 'qp.Qubit',
                             controls: 'qp.QubitIntersection'):
        with qp.measurement_based_uncomputation(location) as b:
            if self.val and b:
                qp.phase_flip(controls)

    def __str__(self):
        return 'rval({})'.format(self.val)

    def __repr__(self):
        return 'qp.BoolRValue({!r})'.format(self.val)


@cirq.value_equality
class IntRValue(RValue[bool]):
    def __init__(self, val: int):
        self.val = val

    def trivial_unwrap(self):
        return self.val

    def resolve(self, sim_state: 'qp.ClassicalSimState', allow_mutate: bool):
        return self.val

    def _value_equality_values_(self):
        return self.val

    def qureg_deps(self) -> Iterable['qp.Qureg']:
        return []

    def value_from_resolved_deps(self, args: Tuple[int, ...]
                                 ) -> int:
        return self.val

    def make_storage_location(self, name: str = ''):
        return qp.Quint(qp.NamedQureg(name, self.val.bit_length()))

    def __int__(self):
        return self.val

    def init_storage_location(self,
                              location: 'qp.Quint',
                              controls: 'qp.QubitIntersection'):
        location ^= self.val & qp.controlled_by(controls)

    def del_storage_location(self,
                             location: 'qp.Quint',
                             controls: 'qp.QubitIntersection'):
        with qp.measurement_based_uncomputation(location) as r:
            if qp.popcnt(r & self.val) & 1:
                qp.phase_flip(controls)

    def __riadd__(self, other):
        other, controls = qp.ControlledLValue.split(other)
        if controls == qp.QubitIntersection.NEVER:
            return other

        if isinstance(other, qp.Quint):
            if self.val == 0:
                return other
            k = qp.leading_zero_bit_count(self.val)
            qp.arithmetic.do_addition(
                lvalue=other[k:],
                offset=self.val >> k,
                carry_in=False,
                control=controls)
            return other
        return NotImplemented

    def __rimul__(self, other):
        if isinstance(other, qp.Quint):
            qp.emit(qp.TimesEqual(lvalue=other,
                                  factor=self.val))
            return other
        return NotImplemented

    def __str__(self):
        return 'rval({})'.format(self.val)

    def __repr__(self):
        return 'qp.IntRValue({!r})'.format(self.val)
