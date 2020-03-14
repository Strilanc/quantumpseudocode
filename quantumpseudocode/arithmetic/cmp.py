from typing import Any, Optional, Union, Callable

import quantumpseudocode as qp
from quantumpseudocode import semi_quantum
from quantumpseudocode.rvalue import RValue


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


@semi_quantum
def do_if_less_than(*,
                    control: 'qp.Qubit.Control' = True,
                    lhs: 'qp.Quint.Borrowed',
                    rhs: 'qp.Quint.Borrowed',
                    or_equal: 'qp.Qubit.Borrowed' = False,
                    effect: Callable[['qp.QubitIntersection'], None]):
    n = max(len(lhs), len(rhs))
    if n == 0:
        effect(control & or_equal)
        return

    with qp.pad_all(lhs, rhs, min_len=n) as (pad_lhs, pad_rhs):
        _forward_sweep(lhs=pad_lhs, rhs=pad_rhs, carry=or_equal)
        effect(control & pad_rhs[-1])
        _backward_sweep(lhs=pad_lhs, rhs=pad_rhs, carry=or_equal)


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
                 lhs: Union[int, qp.Quint, RValue[int]],
                 rhs: Union[int, qp.Quint, RValue[int]],
                 or_equal: Union[bool, qp.Qubit, RValue[bool]]):
        self.lhs = lhs
        self.rhs = rhs
        self.or_equal = or_equal

    def make_storage_location(self, name: Optional[str] = None) -> Any:
        return qp.Qubit(name)

    def phase_flip_if(self, controls: 'qp.QubitIntersection'):
        if controls == qp.QubitIntersection.NEVER:
            return
        do_if_less_than(
            control=controls,
            lhs=self.lhs,
            rhs=self.rhs,
            or_equal=self.or_equal,
            effect=lambda c: qp.emit(qp.OP_PHASE_FLIP, c))

    def init_storage_location(self,
                              location: 'qp.Qubit',
                              controls: 'qp.QubitIntersection'):
        location ^= self & qp.controlled_by(controls)

    def del_storage_location(self,
                             location: 'qp.Qubit',
                             controls: 'qp.QubitIntersection'):
        with qp.measurement_based_uncomputation(location) as b:
            self.phase_flip_if(controls & b)

    def __rixor__(self, other):
        other, controls = qp.ControlledLValue.split(other)
        if controls == qp.QubitIntersection.NEVER:
            return other

        if isinstance(other, qp.Qubit):
            do_if_less_than(
                control=controls,
                lhs=self.lhs,
                rhs=self.rhs,
                or_equal=self.or_equal,
                effect=lambda c: qp.emit(qp.Toggle(lvalue=qp.RawQureg([other])), c))
            return other

        return NotImplemented

    def __str__(self):
        if isinstance(self.or_equal, qp.BoolRValue):
            return '{} {} {}'.format(
                self.lhs,
                '<=' if self.or_equal else '<',
                self.rhs)

        return f'{self.lhs} <= {self.rhs} if {self.or_equal} else {self.lhs} < {self.rhs}'
