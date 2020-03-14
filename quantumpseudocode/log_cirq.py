import collections
from typing import List, Union, Callable, Any, Optional, Tuple

import cirq
import quantumpseudocode as qp


def separate_controls(op: 'qp.Operation') -> 'Tuple[qp.Operation, qp.QubitIntersection]':
    if isinstance(op, qp.ControlledOperation):
        return op.uncontrolled, op.controls
    return op, qp.QubitIntersection.ALWAYS


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

    def log(self, op: 'qp.Operation', cnt: 'qp.QubitIntersection'):
        unknown = False

        if isinstance(op, qp.MeasureOperation):
            qubits = [cirq.NamedQubit(str(q)) for q in op.targets]
            if op.reset:
                self.circuit.append(MeasureResetGate().on_each(*qubits),
                                    cirq.InsertStrategy.NEW_THEN_INLINE)
            else:
                self.circuit.append(cirq.measure(*qubits),
                                    cirq.InsertStrategy.NEW_THEN_INLINE)

        elif isinstance(op, qp.StartMeasurementBasedUncomputation):
            if self.measure_bias is not None:
                op.captured_phase_degrees = 0
                op.take_default_result(bias=self.measure_bias)
            qubits = [cirq.NamedQubit(str(q)) for q in op.targets]
            self.circuit.append(CirqLabelOp(qubits, 'Mxc'), cirq.InsertStrategy.NEW_THEN_INLINE)

        elif op == qp.OP_PHASE_FLIP:
            if cnt.bit:
                if len(cnt.qubits):
                    g = cirq.Z
                    for _ in range(len(cnt.qubits) - 1):
                        g = cirq.ControlledGate(g)
                    ctrls = [cirq.NamedQubit(str(q)) for q in cnt.qubits]
                    self.circuit.append(g(*ctrls),
                                        cirq.InsertStrategy.NEW_THEN_INLINE)
                else:
                    self.circuit.append(cirq.GlobalPhaseOperation(-1), cirq.InsertStrategy.NEW_THEN_INLINE)

        elif isinstance(op, qp.Toggle):
            ctrls = [cirq.NamedQubit(str(q)) for q in cnt.qubits]
            targets = op.lvalue
            if len(targets) and cnt.bit:
                targs = [cirq.NamedQubit(str(q)) for q in targets]
                self.circuit.append(MultiNot(targs).controlled_by(*ctrls),
                                    cirq.InsertStrategy.NEW_THEN_INLINE)

        elif isinstance(op, qp.AllocQuregOperation):
            targs = [cirq.NamedQubit(str(q)) for q in op.qureg]
            self.circuit.append(CirqLabelOp(targs, 'alloc'), cirq.InsertStrategy.NEW_THEN_INLINE)
        elif isinstance(op, qp.ReleaseQuregOperation):
            targs = [cirq.NamedQubit(str(q)) for q in op.qureg]
            self.circuit.append(CirqLabelOp(targs, 'release'), cirq.InsertStrategy.NEW_THEN_INLINE)
        elif isinstance(op, qp.EndMeasurementBasedComputationOp):
            targs = [cirq.NamedQubit(str(q)) for q in op.targets]
            self.circuit.append(CirqLabelOp(targs, 'cxM'), cirq.InsertStrategy.NEW_THEN_INLINE)
        else:
            unknown = True

        if unknown:
            raise NotImplementedError("Unrecognized operation: {!r}".format(op))


class CountNots(qp.Logger):
    def __init__(self):
        super().__init__()
        self.counts = collections.Counter()

    def _val(self):
        return self.counts

    def log(self, op: 'qp.Operation', cnt: 'qp.QubitIntersection'):
        if isinstance(op, qp.Toggle) and cnt.bit:
            targets = op.lvalue
            if len(cnt.qubits) > 1:
                self.counts[1] += 2 * (len(targets) - 1)
                self.counts[len(cnt.qubits)] += 1
            else:
                self.counts[len(cnt.qubits)] += len(targets)
