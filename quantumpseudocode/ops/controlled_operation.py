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

    def state_locations(self) -> 'qp.ArgsAndKwargs':
        return qp.ArgsAndKwargs([
            qp.RawQureg(self.controls),
            self.uncontrolled.state_locations()
        ], {})

    def mutate_state(self, forward: bool, args: 'qp.ArgsAndKwargs') -> None:
        c, v = args.args
        if isinstance(c, qp.Mutable):
            c = c.val
        if all(c):
            self.uncontrolled.mutate_state(forward, v)

    def inverse(self):
        return ControlledOperation(self.uncontrolled.inverse(), self.controls)

    def emit_ops(self, controls: 'qp.QubitIntersection'):
        return self.uncontrolled.emit_ops(self.controls & controls)

    def __str__(self):
        return 'IF {}: {}'.format(self.controls, self.uncontrolled)
    def __repr__(self):
        return 'ControlledOperation({!r}, {!r})'.format(self.uncontrolled,
                                                        self.controls)
