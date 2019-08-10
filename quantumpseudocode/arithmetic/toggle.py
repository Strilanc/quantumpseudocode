import cirq

import quantumpseudocode as qp
from quantumpseudocode.ops import Operation


@cirq.value_equality
class Toggle(Operation):
    def __init__(self, lvalue: qp.Qureg):
        self.targets = lvalue

    def validate_controls(self, controls: 'qp.QubitIntersection'):
        assert set(self.targets).isdisjoint(controls.qubits)

    def mutate_state(self, sim_state: 'qp.ClassicalSimState', forward: bool) -> None:
        sim_state.quint_buf(qp.Quint(self.targets))[:] ^= -1

    def emit_ops(self, controls: 'qp.QubitIntersection'):
        raise ValueError(f"{self} must be emulated.")

    def __repr__(self):
        return f'qp.Toggle({self.targets})'

    def _value_equality_values_(self):
        return self.targets
