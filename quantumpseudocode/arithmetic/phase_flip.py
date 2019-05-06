from typing import Union

import quantumpseudocode
from quantumpseudocode.ops.operation import Operation


class _PhaseFlipOp(Operation):
    def mutate_state(self, forward: bool, *args, **kwargs):
        pass

    def state_locations(self):
        return quantumpseudocode.ArgsAndKwargs([], {})

    def permute(self, forward: bool, *args):
        pass

    def do(self, controls: 'quantumpseudocode.QubitIntersection'):
        raise ValueError("The phase flip gate is fundamental.")

    def inverse(self):
        return self

    def __repr__(self):
        return 'quantumpseudocode.OP_PHASE_FLIP'


def phase_flip(condition: 'Union[bool, quantumpseudocode.Qubit, quantumpseudocode.QubitIntersection, quantumpseudocode.RValue[bool]]' = True):
    if condition is False:
        pass
    elif condition is True:
        quantumpseudocode.emit(OP_PHASE_FLIP)
    elif isinstance(condition, (quantumpseudocode.Qubit, quantumpseudocode.QubitIntersection)):
        quantumpseudocode.emit(OP_PHASE_FLIP.controlled_by(condition))
    elif isinstance(condition, quantumpseudocode.RValue):
        with quantumpseudocode.hold(condition) as q:
            quantumpseudocode.emit(OP_PHASE_FLIP.controlled_by(q))
    else:
        raise NotImplementedError("Unknown phase flip condition: {!r}".format(condition))


OP_PHASE_FLIP = _PhaseFlipOp()
