from typing import Union

import cirq

import quantumpseudocode as qp
from quantumpseudocode.ops import Operation


@cirq.value_equality
class GlobalPhaseOp(Operation):
    def __init__(self, phase: float):
        self.phase = phase % 360

    def mutate_state(self, sim_state: 'qp.ClassicalSimState', forward: bool) -> None:
        sim_state.phase_degrees += self.phase

    def _value_equality_values_(self):
        return self.phase

    def __repr__(self):
        return 'qp.GlobalPhaseOp({!r})'.format(self.phase)


def phase_flip(condition: 'Union[bool, qp.Qubit, qp.QubitIntersection, qp.RValue[bool]]' = True):
    if condition is False or condition == qp.QubitIntersection.NEVER:
        pass
    elif condition is True or condition == qp.QubitIntersection.ALWAYS:
        qp.do_atom(OP_PHASE_FLIP)
    elif isinstance(condition, (qp.Qubit, qp.QubitIntersection)):
        qp.do_atom(OP_PHASE_FLIP.controlled_by(condition))
    elif isinstance(condition, qp.RValue):
        with qp.hold(condition) as q:
            qp.do_atom(OP_PHASE_FLIP.controlled_by(q))
    else:
        raise NotImplementedError("Unknown phase flip condition: {!r}".format(condition))


OP_PHASE_FLIP = GlobalPhaseOp(180)
