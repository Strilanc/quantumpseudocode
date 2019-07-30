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

    def mutate_state(self, sim_state: 'qp.ClassicalSimState', forward: bool) -> None:
        c = sim_state.quint_buf(qp.Quint(qp.RawQureg(self.controls.qubits)))
        controls_satisfied = int(c) == (1 << len(c)) - 1
        if controls_satisfied:
            self.uncontrolled.mutate_state(sim_state=sim_state, forward=forward)

    def inverse(self):
        return ControlledOperation(self.uncontrolled.inverse(), self.controls)

    def emit_ops(self, controls: 'qp.QubitIntersection'):
        return self.uncontrolled.emit_ops(self.controls & controls)

    def __str__(self):
        return 'IF {}: {}'.format(self.controls, self.uncontrolled)
    def __repr__(self):
        return 'ControlledOperation({!r}, {!r})'.format(self.uncontrolled,
                                                        self.controls)
