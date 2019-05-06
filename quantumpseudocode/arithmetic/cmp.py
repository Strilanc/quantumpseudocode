from typing import Any, Optional

import quantumpseudocode as qp

from quantumpseudocode.rvalue import RValue
from .add import uma_sweep
from quantumpseudocode.ops import Op


class EffectIfLessThan(Op):
    def alloc_prefix(self):
        return '_cmp_'

    def biemulate(self,
                  forward: bool,
                  *,
                  lhs: int,
                  rhs: int,
                  or_equal: bool,
                  effect: 'qp.SubEffect'):
        condition = lhs <= rhs if or_equal else lhs < rhs
        if condition:
            effect.op.mutate_state(forward, effect.args)

    def do(self,
           controls: 'qp.QubitIntersection',
           *,
           lhs: 'qp.Quint',
           rhs: 'qp.Quint',
           or_equal: 'qp.Qubit',
           effect: 'qp.Operation'):
        n = max(len(lhs), len(rhs))

        with qp.pad_all(lhs, rhs, min_len=n) as (lhs, rhs):
            # Propagate carries.
            with qp.invert():
                uma_sweep(lhs, or_equal, rhs, qp.QubitIntersection.EMPTY)

            # Apply effect.
            qp.emit(qp.ControlledOperation(effect, controls & rhs[-1]))

            # Uncompute carries.
            uma_sweep(lhs, or_equal, rhs, qp.QubitIntersection.EMPTY)

    def describe(self, lhs, rhs, or_equal, effect):
        return 'IF {} < {} + {} THEN {}'.format(
            lhs, rhs, or_equal, effect)


class IfLessThanRVal(RValue[bool]):
    def __init__(self,
                 lhs: RValue[int],
                 rhs: RValue[int],
                 or_equal: RValue[bool]):
        self.lhs = lhs
        self.rhs = rhs
        self.or_equal = or_equal

    def existing_storage_location(self) -> Any:
        return None

    def make_storage_location(self, name: Optional[str] = None) -> Any:
        return qp.qmanaged(name='_cmp')

    def phase_flip_if(self, controls: 'qp.QubitIntersection'):
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
            effect=qp.OP_TOGGLE(location).controlled_by(controls)))

    def del_storage_location(self,
                             location: Any,
                             controls: 'qp.QubitIntersection'):
     if qp.measure_x_for_phase_fixup_and_reset(location):
         self.phase_flip_if(controls)
