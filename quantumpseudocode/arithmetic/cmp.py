from typing import Any, Optional

import quantumpseudocode as qp

from quantumpseudocode.rvalue import RValue
from .add import uma_sweep
from quantumpseudocode.ops import Op


class EffectIfLessThan(Op):
    def alloc_prefix(self):
        return '_cmp_'

    @staticmethod
    def biemulate(forward: bool,
                  *,
                  lhs: int,
                  rhs: int,
                  or_equal: bool,
                  effect: 'qp.SubEffect'):
        condition = lhs <= rhs if or_equal else lhs < rhs
        if condition:
            effect.op.mutate_state(forward, effect.args)

    @staticmethod
    def do(controls: 'qp.QubitIntersection',
           *,
           lhs: 'qp.Quint',
           rhs: 'qp.Quint',
           or_equal: 'qp.Qubit',
           effect: 'qp.Operation'):
        n = max(len(lhs), len(rhs))
        if n == 0:
            qp.emit(qp.ControlledOperation(effect, controls & or_equal))
            return

        with qp.pad_all(lhs, rhs, min_len=n) as (lhs, rhs):
            # Propagate carries.
            with qp.invert():
                uma_sweep(lhs, or_equal, rhs, qp.QubitIntersection.ALWAYS)

            # Apply effect.
            qp.emit(qp.ControlledOperation(effect, controls & rhs[-1]))

            # Uncompute carries.
            uma_sweep(lhs, or_equal, rhs, qp.QubitIntersection.ALWAYS)

    @staticmethod
    def describe(lhs, rhs, or_equal, effect):
        return 'IF {} < {} + {} THEN {}'.format(
            lhs, rhs, or_equal, effect)


class QuintEqConstRVal(RValue[bool]):
    def __init__(self,
                 lhs: 'qp.Quint',
                 rhs: int,
                 invert: bool = False):
        self.lhs = lhs
        self.rhs = rhs
        self.invert = invert

    def make_storage_location(self, name: Optional[str] = None) -> Any:
        return qp.Qubit(name)

    def init_storage_location(self,
                              location: Any,
                              controls: 'qp.QubitIntersection'):
        if self.rhs & (-1 << len(self.lhs)):
            location ^= self.invert
            return
        self.lhs ^= ~self.rhs
        location ^= qp.QubitIntersection(tuple(self.lhs)) & controls
        location ^= self.invert
        self.lhs ^= ~self.rhs

    def del_storage_location(self,
                             location: Any,
                             controls: 'qp.QubitIntersection'):
        if self.rhs & (-1 << len(self.lhs)):
            with qp.measurement_based_uncomputation(location) as b:
                if b:
                    qp.phase_flip(self.invert)
            return
        with qp.measurement_based_uncomputation(location) as b:
            if b:
                self.lhs ^= ~self.rhs
                qp.phase_flip(qp.QubitIntersection(tuple(self.lhs)) & controls & b)
                qp.phase_flip(self.invert)
                self.lhs ^= ~self.rhs

    def __str__(self):
        return f'{self.lhs} == {self.rhs}'

    def __repr__(self):
        return f'qp.QuintEqConstRVal({self.lhs!r}, {self.rhs!r})'


class IfLessThanRVal(RValue[bool]):
    def __init__(self,
                 lhs: RValue[int],
                 rhs: RValue[int],
                 or_equal: RValue[bool]):
        self.lhs = lhs
        self.rhs = rhs
        self.or_equal = or_equal

    def make_storage_location(self, name: Optional[str] = None) -> Any:
        return qp.Qubit(name)

    def phase_flip_if(self, controls: 'qp.QubitIntersection'):
        if controls == qp.QubitIntersection.NEVER:
            return
        qp.emit(EffectIfLessThan(
            lhs=self.lhs,
            rhs=self.rhs,
            or_equal=self.or_equal,
            effect=qp.OP_PHASE_FLIP.controlled_by(controls)))

    def init_storage_location(self,
                              location: Any,
                              controls: 'qp.QubitIntersection'):
        qp.emit(EffectIfLessThan(
            lhs=self.lhs,
            rhs=self.rhs,
            or_equal=self.or_equal,
            effect=qp.Toggle(lvalue=qp.RawQureg([location])).controlled_by(controls)))

    def del_storage_location(self,
                             location: Any,
                             controls: 'qp.QubitIntersection'):
        with qp.measurement_based_uncomputation(location) as b:
            self.phase_flip_if(controls & b)

    def __str__(self):
        if isinstance(self.or_equal, qp.BoolRValue):
            return '{} {} {}'.format(
                self.lhs,
                '<=' if self.or_equal else '<',
                self.rhs)

        return '{} <= {} if {} else {} < {}'.format(
            self.lhs,
            self.rhs,
            self.or_equal,
            self.lhs,
            self.rhs)
