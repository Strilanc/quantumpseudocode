from typing import Iterable, Union

import cirq

import quantumpseudocode as qp
from quantumpseudocode.ops import Operation


def cnot(controls: Union['qp.Qubit', Iterable['qp.Qubit'], 'qp.QubitIntersection'],
         targets: Union['qp.Qubit', Iterable['qp.Qubit']]):
    if isinstance(controls, qp.Qubit):
        controls = qp.QubitIntersection((controls,))
    elif not isinstance(controls, qp.QubitIntersection):
        controls = qp.QubitIntersection(tuple(controls))
    qp.do_atom(qp.Toggle(targets).controlled_by(controls))


@cirq.value_equality
class Toggle(Operation):
    def __init__(self, lvalue: Union[qp.Qubit, Iterable[qp.Qubit]]):
        if isinstance(lvalue, qp.Qubit):
            lvalue = qp.RawQureg((lvalue,))
        elif isinstance(lvalue, qp.Quint):
            lvalue = lvalue.qureg
        elif not isinstance(lvalue, qp.Qureg):
            lvalue = qp.RawQureg(lvalue)
        self.targets = lvalue

    def validate_controls(self, controls: 'qp.QubitIntersection'):
        assert set(self.targets).isdisjoint(controls.qubits)

    def mutate_state(self, sim_state: 'qp.ClassicalSimState', forward: bool) -> None:
        sim_state.quint_buf(qp.Quint(self.targets))[:] ^= -1

    def __repr__(self):
        return f'qp.Toggle({self.targets})'

    def _value_equality_values_(self):
        return self.targets
