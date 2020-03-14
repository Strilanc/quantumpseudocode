from typing import Any, Optional

import quantumpseudocode as qp

from quantumpseudocode.rvalue import RValue
from quantumpseudocode.ops import Operation


def _forward_sweep(*,
                   lhs: qp.Quint,
                   rhs: qp.Quint,
                   carry: qp.Qubit):
    assert len(lhs) == len(rhs)
    carry_then_rhs = [carry] + list(rhs)

    for i in range(len(lhs)):
        a = carry_then_rhs[i]
        b = rhs[i]
        c = lhs[i]

        c ^= a
        a ^= b
        b ^= a & c


def _backward_sweep(lhs: qp.Quint,
                    rhs: qp.Quint,
                    carry: qp.Qubit):
    assert len(lhs) == len(rhs)
    carry_then_rhs = [carry] + list(rhs)

    for i in range(len(lhs))[::-1]:
        a = carry_then_rhs[i]
        b = rhs[i]
        c = lhs[i]

        b ^= a & c
        a ^= b
        c ^= a


class EffectIfLessThan(Operation):
    def __init__(self,
                 *,
                 lhs: 'qp.RValue[int]',
                 rhs: 'qp.RValue[int]',
                 or_equal: 'qp.RValue[bool]',
                 effect: 'qp.Operation'):
        self.lhs = lhs
        self.rhs = rhs
        self.or_equal = or_equal
        self.effect = effect

    def emit_ops(self, controls: 'qp.QubitIntersection'):
        with qp.hold(self.lhs) as lhs:
            with qp.hold(self.rhs) as rhs:
                with qp.hold(self.or_equal) as or_equal:
                    n = max(len(lhs), len(rhs))
                    if n == 0:
                        self.effect.emit_ops(controls & or_equal)
                        return

                    with qp.pad_all(lhs, rhs, min_len=n) as (pad_lhs, pad_rhs):
                        _forward_sweep(lhs=pad_lhs, rhs=pad_rhs, carry=or_equal)
                        self.effect.emit_ops(controls & pad_rhs[-1])
                        _backward_sweep(lhs=pad_lhs, rhs=pad_rhs, carry=or_equal)

    def mutate_state(self, sim_state: 'qp.ClassicalSimState', forward: bool) -> None:
        a = sim_state.resolve_location(self.lhs, allow_mutate=False)
        b = sim_state.resolve_location(self.rhs, allow_mutate=False)
        e = sim_state.resolve_location(self.or_equal, e)
        condition = a <= b if e else a < b
        if condition:
            self.effect.mutate_state(sim_state, forward=forward)

    def inverse(self) -> 'Operation':
        return EffectIfLessThan(self.lhs, self.rhs, self.or_equal, self.effect.inverse())

    def __repr__(self):
        return f'qp.EffectIfLessThan({self.lhs!r}, {self.rhs!r}, {self.or_equal!r}, {self.effect!r})'


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
        EffectIfLessThan(
            lhs=self.lhs,
            rhs=self.rhs,
            or_equal=self.or_equal,
            effect=qp.OP_PHASE_FLIP).emit_ops(controls)

    def init_storage_location(self,
                              location: 'qp.Qubit',
                              controls: 'qp.QubitIntersection'):
        EffectIfLessThan(
            lhs=self.lhs,
            rhs=self.rhs,
            or_equal=self.or_equal,
            effect=qp.Toggle(lvalue=qp.RawQureg([location]))
        ).emit_ops(controls)

    def del_storage_location(self,
                             location: 'qp.Qubit',
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
