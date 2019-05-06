from typing import Union, Tuple, Iterable, Any

import cirq

import quantumpseudocode as qp
from .operation import Operation


@cirq.value_equality
class ControlledOperation(Operation):
    def __init__(self,
                 uncontrolled: 'qp.Operation',
                 controls: 'qp.QubitIntersection'):
        self.controls = controls
        self.uncontrolled = uncontrolled

    def _value_equality_values_(self):
        return self.controls, self.uncontrolled

    def permutation_registers(self):
        return (qp.RawQureg(self.controls),) + tuple(
            self.uncontrolled.permutation_registers())

    def permute(self, forward, args):
        n = len(self.controls)
        for i in range(n):
            if args[i] != (1 << len(self.controls[i])) - 1:
                return args
        return args[:n] + self.uncontrolled.permute(forward, args[n:])

    def inverse(self):
        return ControlledOperation(self.uncontrolled.inverse(), self.controls)

    def emit_ops(self, controls: 'qp.QubitIntersection'):
        return self.uncontrolled.emit_ops(self.controls & controls)

    def __str__(self):
        return 'IF {}: {}'.format(self.controls, self.uncontrolled)
    def __repr__(self):
        return 'ControlledOperation({!r}, {!r})'.format(self.uncontrolled,
                                                        self.controls)
