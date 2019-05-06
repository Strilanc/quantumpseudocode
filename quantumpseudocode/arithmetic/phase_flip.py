from typing import Union

import quantumpseudocode as qp
from quantumpseudocode.ops.operation import Operation


class _PhaseFlipOp(Operation):
    def mutate_state(self, forward: bool, args: 'qp.ArgsAndKwargs'):
        pass

    def state_locations(self):
        return qp.ArgsAndKwargs([], {})

    def permute(self, forward: bool, *args):
        pass

    def do(self, controls: 'qp.QubitIntersection'):
        raise ValueError("The phase flip gate is fundamental.")

    def inverse(self):
        return self

    def __repr__(self):
        return 'qp.OP_PHASE_FLIP'


def phase_flip(condition: 'Union[bool, qp.Qubit, qp.QubitIntersection, qp.RValue[bool]]' = True):
    if condition is False:
        pass
    elif condition is True:
        qp.emit(OP_PHASE_FLIP)
    elif isinstance(condition, (qp.Qubit, qp.QubitIntersection)):
        qp.emit(OP_PHASE_FLIP.controlled_by(condition))
    elif isinstance(condition, qp.RValue):
        with qp.hold(condition) as q:
            qp.emit(OP_PHASE_FLIP.controlled_by(q))
    else:
        raise NotImplementedError("Unknown phase flip condition: {!r}".format(condition))


OP_PHASE_FLIP = _PhaseFlipOp()
