import cirq

import quantumpseudocode
from .operation import Operation


@cirq.value_equality
class InverseOperation(Operation):
    def __init__(self, inverse: 'quantumpseudocode.Operation'):
        self.sub = inverse

    def _value_equality_values_(self):
        return self.sub

    def do(self, controls):
        with quantumpseudocode.invert():
            self.sub.do(controls)

    def state_locations(self):
        return self.sub.state_locations()

    def mutate_state(self, forward: bool, *args, **kwargs):
        self.sub.mutate_state(not forward, *args, **kwargs)

    def inverse(self):
        return self.sub

    def __str__(self):
        return 'inverse({})'.format(self.sub)

    def __repr__(self):
        return 'quantumpseudocode.InverseOperation({!r})'.format(self.sub)
