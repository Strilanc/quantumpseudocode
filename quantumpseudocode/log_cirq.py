import collections
from typing import List, Union, Callable, Any, Optional, Tuple

import cirq
import quantumpseudocode as qp


def separate_controls(op: 'qp.Operation') -> 'Tuple[qp.Operation, qp.QubitIntersection]':
    if isinstance(op, qp.ControlledOperation):
        return op.uncontrolled, op.controls
    return op, qp.QubitIntersection.ALWAYS


def _toggle_targets(lvalue: 'qp.Qureg') -> 'qp.Qureg':
    return lvalue


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


class MeasureXFixupGate(cirq.SingleQubitGate):
    def _circuit_diagram_info_(self, args):
        return 'Mxc'


class MeasureResetGate(cirq.SingleQubitGate):
    def _circuit_diagram_info_(self, args):
        return 'Mr'


class LogCirqCircuit(qp.OperatingContext):
    def __init__(self):
        super().__init__()
        self.circuit = cirq.Circuit()

    def __enter__(self):
        super().__enter__()
        return self.circuit

    def do(self, operation: 'qp.Operation'):
        unknown = False

        op, controls = separate_controls(operation)
        if isinstance(op, qp.MeasureOperation):
            qubits = [cirq.NamedQubit(str(q)) for q in op.targets]
            if op.reset:
                self.circuit.append(MeasureResetGate().on_each(*qubits),
                                    cirq.InsertStrategy.NEW_THEN_INLINE)
            else:
                self.circuit.append(cirq.measure(*qubits),
                                    cirq.InsertStrategy.NEW_THEN_INLINE)

        elif isinstance(op, qp.StartMeasurementBasedUncomputation):
            qubits = [cirq.NamedQubit(str(q)) for q in op.targets]
            self.circuit.append(MeasureXFixupGate().on_each(*qubits),
                                cirq.InsertStrategy.NEW_THEN_INLINE)

        elif isinstance(op, qp.GlobalPhaseOp):
            if controls.bit and len(controls.qubits):
                g = cirq.Z**(180 / op.phase)
                for _ in range(len(controls.qubits) - 1):
                    g = cirq.ControlledGate(g)
                ctrls = [cirq.NamedQubit(str(q)) for q in controls.qubits]
                self.circuit.append(g(*ctrls),
                                    cirq.InsertStrategy.NEW_THEN_INLINE)

        elif isinstance(op, qp.Toggle):
            ctrls = [cirq.NamedQubit(str(q)) for q in controls.qubits]
            if len(op.targets) and controls.bit:
                targs = [cirq.NamedQubit(str(q)) for q in op.targets]
                self.circuit.append(MultiNot(targs).controlled_by(*ctrls),
                                    cirq.InsertStrategy.NEW_THEN_INLINE)

        elif isinstance(op, qp.AllocQuregOperation):
            pass
        elif isinstance(op, qp.ReleaseQuregOperation):
            pass
        else:
            unknown = True

        # if unknown:
        #     raise NotImplementedError("Unrecognized operation: {!r}".format(operation))

        if self._outer_context is not None:
            self._outer_context.do(operation)


class CountNots(qp.OperatingContext):
    def __init__(self):
        super().__init__()
        self.counts = collections.Counter()

    def __enter__(self):
        super().__enter__()
        return self.counts

    def do(self, operation: 'qp.Operation'):
        op, controls = separate_controls(operation)

        if isinstance(op, qp.Toggle):
            if len(controls.qubits) > 1:
                self.counts[1] += 2 * (len(op.targets) - 1)
                self.counts[len(controls.qubits)] += 1
            else:
                self.counts[len(controls.qubits)] += len(op.targets)

        if self._outer_context is not None:
            self._outer_context.do(operation)
