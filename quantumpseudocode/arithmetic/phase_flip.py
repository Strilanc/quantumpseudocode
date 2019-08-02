from typing import Union

import quantumpseudocode as qp
from quantumpseudocode.ops import Operation, Op


class _PhaseFlipOp(Operation):
    def mutate_state(self, sim_state: 'qp.ClassicalSimState', forward: bool) -> None:
        sim_state.phase_degrees += 180
        sim_state.phase_degrees %= 360

    def emit_ops(self, controls: 'qp.QubitIntersection'):
        raise ValueError("The phase flip gate is fundamental.")

    def inverse(self):
        return self

    def __repr__(self):
        return 'qp.OP_PHASE_FLIP'


def phase_flip(condition: 'Union[bool, qp.Qubit, qp.QubitIntersection, qp.RValue[bool]]' = True):
    if condition is False or condition == qp.QubitIntersection.NEVER:
        pass
    elif condition is True or condition == qp.QubitIntersection.ALWAYS:
        qp.emit(OP_PHASE_FLIP)
    elif isinstance(condition, (qp.Qubit, qp.QubitIntersection)):
        qp.emit(OP_PHASE_FLIP.controlled_by(condition))
    elif isinstance(condition, qp.RValue):
        with qp.hold(condition) as q:
            qp.emit(OP_PHASE_FLIP.controlled_by(q))
    else:
        raise NotImplementedError("Unknown phase flip condition: {!r}".format(condition))


OP_PHASE_FLIP = _PhaseFlipOp()
