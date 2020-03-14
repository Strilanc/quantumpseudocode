from typing import Union

import quantumpseudocode as qp


def phase_flip(condition: 'Union[bool, qp.Qubit, qp.QubitIntersection, qp.RValue[bool]]' = True):
    if condition is False or condition == qp.QubitIntersection.NEVER:
        pass
    elif condition is True or condition == qp.QubitIntersection.ALWAYS:
        qp.global_logger.do_phase_flip(qp.QubitIntersection.ALWAYS)
    elif isinstance(condition, qp.QubitIntersection):
        qp.global_logger.do_phase_flip(condition)
    elif isinstance(condition, qp.Qubit):
        qp.global_logger.do_phase_flip(qp.QubitIntersection((condition,)))
    elif isinstance(condition, (qp.Qubit, qp.RValue)):
        with qp.hold(condition) as q:
            qp.global_logger.do_phase_flip(qp.QubitIntersection((q,)))
    else:
        raise NotImplementedError("Unknown phase flip condition: {!r}".format(condition))
