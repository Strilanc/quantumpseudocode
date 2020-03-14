import collections
from typing import List, Union, Callable, Any, Optional, Tuple

import cirq
import quantumpseudocode as qp


class MultiNot(cirq.Operation):
    def __init__(self, qubits):
        self._qubits = tuple(qubits)

    def with_qubits(self, *new_qubits):
        return MultiNot(new_qubits)

    @property
    def qubits(self):
        return self._qubits

    def _circuit_diagram_info_(self, args: cirq.CircuitDiagramInfoArgs):
        return ['X'] * args.known_qubit_count

    def __repr__(self):
        return f'qp.MultiNot({self._qubits!r})'


class MeasureResetGate(cirq.SingleQubitGate):
    def _circuit_diagram_info_(self, args):
        return 'Mr'


class CirqLabelOp(cirq.Operation):
    def __init__(self, qubits, label: str):
        self._qubits = tuple(qubits)
        self.label = label

    @property
    def qubits(self) -> Tuple['cirq.Qid', ...]:
        return self._qubits

    def with_qubits(self, *new_qubits: 'cirq.Qid') -> 'cirq.Operation':
        raise NotImplementedError()

    def _circuit_diagram_info_(self, args):
        return (self.label,) * len(self.qubits)


class LogCirqCircuit(qp.Logger):
    def __init__(self, measure_bias: Optional[float] = None):
        super().__init__()
        self.circuit = cirq.Circuit()
        self.measure_bias = measure_bias

    def _val(self):
        return self.circuit

    def do_allocate_qureg(self, op: 'qp.AllocQuregOperation'):
        targets = [cirq.NamedQubit(str(q)) for q in op.qureg]
        self.circuit.append(CirqLabelOp(targets, 'alloc'), cirq.InsertStrategy.NEW_THEN_INLINE)

    def do_release_qureg(self, op: 'qp.ReleaseQuregOperation'):
        targets = [cirq.NamedQubit(str(q)) for q in op.qureg]
        self.circuit.append(CirqLabelOp(targets, 'release'), cirq.InsertStrategy.NEW_THEN_INLINE)

    def do_phase_flip(self, op, controls: 'qp.QubitIntersection'):
        if controls.bit:
            if len(controls.qubits):
                g = cirq.Z
                for _ in range(len(controls.qubits) - 1):
                    g = cirq.ControlledGate(g)
                ctrls = [cirq.NamedQubit(str(q)) for q in controls.qubits]
                self.circuit.append(g(*ctrls),
                                    cirq.InsertStrategy.NEW_THEN_INLINE)
            else:
                self.circuit.append(cirq.GlobalPhaseOperation(-1), cirq.InsertStrategy.NEW_THEN_INLINE)

    def do_toggle_qureg(self, op: 'qp.Toggle', controls: 'qp.QubitIntersection'):
        ctrls = [cirq.NamedQubit(str(q)) for q in controls.qubits]
        targets = op.lvalue
        if len(targets) and controls.bit:
            targs = [cirq.NamedQubit(str(q)) for q in targets]
            self.circuit.append(MultiNot(targs).controlled_by(*ctrls),
                                cirq.InsertStrategy.NEW_THEN_INLINE)

    def do_measure_qureg(self, op: 'qp.MeasureOperation'):
        qubits = [cirq.NamedQubit(str(q)) for q in op.targets]
        if op.reset:
            self.circuit.append(MeasureResetGate().on_each(*qubits),
                                cirq.InsertStrategy.NEW_THEN_INLINE)
        else:
            self.circuit.append(cirq.measure(*qubits),
                                cirq.InsertStrategy.NEW_THEN_INLINE)

    def do_start_measurement_based_uncomputation(self, op: 'qp.StartMeasurementBasedUncomputation'):
        if self.measure_bias is not None:
            op.captured_phase_degrees = 0
            op.take_default_result(bias=self.measure_bias)
        qubits = [cirq.NamedQubit(str(q)) for q in op.targets]
        self.circuit.append(CirqLabelOp(qubits, 'Mxc'), cirq.InsertStrategy.NEW_THEN_INLINE)

    def do_end_measurement_based_uncomputation(self, op: 'qp.EndMeasurementBasedComputationOp'):
        targets = [cirq.NamedQubit(str(q)) for q in op.targets]
        self.circuit.append(CirqLabelOp(targets, 'cxM'), cirq.InsertStrategy.NEW_THEN_INLINE)


class CountNots(qp.Logger):
    def __init__(self):
        super().__init__()
        self.counts = collections.Counter()

    def _val(self):
        return self.counts

    def do_allocate_qureg(self, op: 'qp.AllocQuregOperation'):
        pass

    def do_release_qureg(self, op: 'qp.ReleaseQuregOperation'):
        pass

    def do_phase_flip(self, op, controls: 'qp.QubitIntersection'):
        if controls.bit:
            if len(controls.qubits) > 0:
                self.counts[len(controls.qubits) - 1] += 1

    def do_toggle_qureg(self, op: 'qp.Toggle', controls: 'qp.QubitIntersection'):
        if controls.bit:
            targets = op.lvalue
            if len(controls.qubits) > 1:
                self.counts[1] += 2 * (len(targets) - 1)
                self.counts[len(controls.qubits)] += 1
            else:
                self.counts[len(controls.qubits)] += len(targets)

    def do_measure_qureg(self, op: 'qp.MeasureOperation'):
        pass

    def do_start_measurement_based_uncomputation(self, op: 'qp.StartMeasurementBasedUncomputation'):
        pass

    def do_end_measurement_based_uncomputation(self, op: 'qp.EndMeasurementBasedComputationOp'):
        pass
