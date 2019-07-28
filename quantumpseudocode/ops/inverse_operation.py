import cirq

import quantumpseudocode as qp
from .operation import Operation


@cirq.value_equality
class InverseOperation(Operation):
    def __init__(self, inverse: 'qp.Operation'):
        self.sub = inverse

    def _value_equality_values_(self):
        return self.sub

    def emit_ops(self, controls):
        with qp.invert():
            self.sub.emit_ops(controls)

    def mutate_state(self, sim_state: 'qp.ClassicalSimState', forward: bool) -> None:
        self.sub.mutate_state(sim_state=sim_state, forward=not forward)

    def inverse(self):
        return self.sub

    def __str__(self):
        return 'inverse({})'.format(self.sub)

    def __repr__(self):
        return 'qp.InverseOperation({!r})'.format(self.sub)
