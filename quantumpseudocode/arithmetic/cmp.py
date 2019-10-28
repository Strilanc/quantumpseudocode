from typing import Any, Optional

import quantumpseudocode as qp

from quantumpseudocode.rvalue import RValue
from .add import uma_sweep
from quantumpseudocode.ops import semi_quantum


def do_classical_if_less_than(sim_state: 'qp.ClassicalSimState',
                              *,
                              lhs: int,
                              rhs: int,
                              or_equal: bool = False,
                              effect: 'qp.Operation'):
    condition = lhs <= rhs if or_equal else lhs < rhs
    if condition:
        effect.mutate_state(sim_state, forward=True)


@semi_quantum(classical=do_classical_if_less_than, alloc_prefix='_cmp_')
def do_if_less_than(*,
                    control: 'qp.Qubit.Control' = True,
                    lhs: 'qp.Quint.Borrowed',
                    rhs: 'qp.Quint.Borrowed',
                    or_equal: 'qp.Qubit.Borrowed' = False,
                    effect: 'qp.Operation'):
    assert isinstance(control, qp.QubitIntersection) and len(control.qubits) <= 1
    assert isinstance(lhs, qp.Quint)
    assert isinstance(rhs, qp.Quint)
    assert isinstance(or_equal, qp.Qubit)

    n = max(len(lhs), len(rhs))
    if n == 0:
        qp.do_atom(effect.controlled_by(control & or_equal))
        return

    with qp.pad_all(lhs, rhs, min_len=n) as (lhs, rhs):
        # Propagate carries.
        uma_sweep(lhs, or_equal, rhs, qp.QubitIntersection.ALWAYS, forward=False)

        # Apply effect.
        qp.do_atom(effect.controlled_by(control & rhs[-1]))

        # Uncompute carries.
        uma_sweep(lhs, or_equal, rhs, qp.QubitIntersection.ALWAYS)


class IfLessThanRVal(RValue[bool]):
    def __init__(self,
                 lhs: RValue[int],
                 rhs: RValue[int],
                 or_equal: RValue[bool]):
        self.lhs = lhs
        self.rhs = rhs
        self.or_equal = or_equal

    def make_storage_location(self, name: Optional[str] = None) -> Any:
        return qp.Qubit.lonely(name)

    def phase_flip_if(self, controls: 'qp.QubitIntersection'):
        if controls == qp.QubitIntersection.NEVER:
            return
        do_if_less_than(
            lhs=self.lhs,
            rhs=self.rhs,
            or_equal=self.or_equal,
            control=controls,
            effect=qp.OP_PHASE_FLIP)

    def init_storage_location(self,
                              location: Any,
                              controls: 'qp.QubitIntersection'):
        do_if_less_than(
            lhs=self.lhs,
            rhs=self.rhs,
            or_equal=self.or_equal,
            control=controls,
            effect=qp.Toggle(lvalue=qp.RawQureg([location])))

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
