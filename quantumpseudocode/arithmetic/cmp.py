from typing import Any, Optional

import quantumpseudocode

from quantumpseudocode.rvalue import RValue
from .add import uma_sweep
from quantumpseudocode.ops.signature_gate import SignatureGate


class _IfLessThanThenGateClass(SignatureGate):
    def register_name_prefix(self):
        return '_cmp_'

    def emulate(self,
                forward: bool,
                *,
                lhs: int,
                rhs: int,
                or_equal: bool,
                effect: 'quantumpseudocode.SubEffect'):
        condition = lhs <= rhs if or_equal else lhs < rhs
        if condition:
            effect.op.mutate_state(forward,
                                   *effect.args.args,
                                   **effect.args.kwargs)

    def do(self,
           controls: 'quantumpseudocode.QubitIntersection',
           *,
           lhs: 'quantumpseudocode.Quint',
           rhs: 'quantumpseudocode.Quint',
           or_equal: 'quantumpseudocode.Qubit',
           effect: 'quantumpseudocode.Operation'):
        n = max(len(lhs), len(rhs))

        with quantumpseudocode.pad_all(lhs, rhs, min_len=n) as (lhs, rhs):
            # Propagate carries.
            with quantumpseudocode.invert():
                uma_sweep(lhs, or_equal, rhs, quantumpseudocode.QubitIntersection.EMPTY)

            # Apply effect.
            quantumpseudocode.emit(quantumpseudocode.ControlledOperation(effect, controls & rhs[-1]))

            # Uncompute carries.
            uma_sweep(lhs, or_equal, rhs, quantumpseudocode.QubitIntersection.EMPTY)

    def describe(self, lhs, rhs, or_equal, effect):
        return 'IF {} < {} + {}: {}'.format(
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
        return quantumpseudocode.qmanaged(name='_cmp')

    def phase_flip_if(self, controls: 'quantumpseudocode.QubitIntersection'):
        quantumpseudocode.emit(IfLessThanThenGate(
            lhs=self.lhs,
            rhs=self.rhs,
            or_equal=self.or_equal,
            effect=quantumpseudocode.OP_PHASE_FLIP.controlled_by(controls)))

    def init_storage_location(self,
                              location: Any,
                              controls: 'quantumpseudocode.QubitIntersection'):
        quantumpseudocode.emit(IfLessThanThenGate(
            lhs=self.lhs,
            rhs=self.rhs,
            or_equal=self.or_equal,
            effect=quantumpseudocode.OP_TOGGLE(location).controlled_by(controls)))

    def del_storage_location(self,
                             location: Any,
                             controls: 'quantumpseudocode.QubitIntersection'):
     if quantumpseudocode.measure_x_for_phase_fixup_and_reset(location):
         self.phase_flip_if(controls)



IfLessThanThenGate = _IfLessThanThenGateClass()
