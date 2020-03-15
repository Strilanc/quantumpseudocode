from typing import Union

import quantumpseudocode as qp
from quantumpseudocode import sink


def phase_flip(condition: 'Union[bool, qp.Qubit, qp.QubitIntersection, qp.RValue[bool]]' = True):
    if isinstance(condition, qp.QubitIntersection):
        sink.global_sink.do_phase_flip(condition)
    elif condition is False or condition == qp.QubitIntersection.NEVER:
        pass
    elif condition is True:
        phase_flip(qp.QubitIntersection.ALWAYS)
    elif isinstance(condition, qp.Qubit):
        phase_flip(qp.QubitIntersection((condition,)))
    elif isinstance(condition, (qp.Qubit, qp.RValue)):
        with qp.hold(condition) as q:
            qp.phase_flip(q)
    else:
        raise NotImplementedError("Unknown phase flip condition: {!r}".format(condition))
