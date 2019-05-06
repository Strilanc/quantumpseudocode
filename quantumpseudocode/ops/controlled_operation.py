from typing import Union, Tuple, Iterable, Any

import cirq

import quantumpseudocode
from .operation import Operation


@cirq.value_equality
class ControlledOperation(Operation):
    def __init__(self,
                 uncontrolled: 'quantumpseudocode.Operation',
                 controls: 'quantumpseudocode.QubitIntersection'):
        self.controls = controls
        self.uncontrolled = uncontrolled

    def _value_equality_values_(self):
        return self.controls, self.uncontrolled

    def permutation_registers(self):
        return (quantumpseudocode.RawQureg(self.controls),) + tuple(
            self.uncontrolled.permutation_registers())

    def permute(self, forward, args):
        n = len(self.controls)
        for i in range(n):
            if args[i] != (1 << len(self.controls[i])) - 1:
                return args
        return args[:n] + self.uncontrolled.permute(forward, args[n:])

    def inverse(self):
        return ControlledOperation(self.uncontrolled.inverse(), self.controls)

    def do(self, controls: 'quantumpseudocode.QubitIntersection'):
        return self.uncontrolled.do(self.controls & controls)

    def __str__(self):
        return 'IF {}: {}'.format(self.controls, self.uncontrolled)
    def __repr__(self):
        return 'ControlledOperation({!r}, {!r})'.format(self.uncontrolled,
                                                        self.controls)
