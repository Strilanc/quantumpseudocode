import collections
from typing import List, Union, Callable, Any, Optional, Tuple

import cirq
import quantumpseudocode


def separate_controls(op: 'quantumpseudocode.Operation') -> 'Tuple[quantumpseudocode.Operation, quantumpseudocode.QubitIntersection]':
    if isinstance(op, quantumpseudocode.ControlledOperation):
        return op.uncontrolled, op.controls
    return op, quantumpseudocode.QubitIntersection.EMPTY


def _toggle_targets(lvalue: 'quantumpseudocode.Qureg') -> 'quantumpseudocode.Qureg':
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


class LogCirqCircuit(quantumpseudocode.Lens):
    def __init__(self):
        super().__init__()
        self.circuit = cirq.Circuit()

    def _val(self):
        return self.circuit

    def modify(self, operation: 'quantumpseudocode.Operation'):
        unknown = False

        op, controls = separate_controls(operation)
        if isinstance(op, quantumpseudocode.MeasureOperation):
            qubits = [cirq.NamedQubit(str(q)) for q in op.targets]
            if op.reset:
                self.circuit.append(MeasureResetGate()(*qubits),
                                    cirq.InsertStrategy.NEW_THEN_INLINE)
            else:
                self.circuit.append(cirq.measure(*qubits),
                                    cirq.InsertStrategy.NEW_THEN_INLINE)

        elif isinstance(op, quantumpseudocode.MeasureXForPhaseKickOperation):
            q = op.target
            q2 = cirq.NamedQubit(str(q))
            self.circuit.append(MeasureXFixupGate()(q2),
                                cirq.InsertStrategy.NEW_THEN_INLINE)

        elif op == quantumpseudocode.OP_PHASE_FLIP:
            if len(controls):
                g = cirq.Z
                for _ in range(len(controls) - 1):
                    g = cirq.ControlledGate(g)
                ctrls = [cirq.NamedQubit(str(q)) for q in controls]
                self.circuit.append(g(*ctrls),
                                    cirq.InsertStrategy.NEW_THEN_INLINE)

        elif isinstance(op, quantumpseudocode.SignatureOperation):
            if op.gate == quantumpseudocode.OP_TOGGLE:
                ctrls = [cirq.NamedQubit(str(q)) for q in controls]
                targets = op.args.pass_into(_toggle_targets)
                if len(targets):
                    targs = [cirq.NamedQubit(str(q)) for q in targets]
                    self.circuit.append(MultiNot(targs).controlled_by(*ctrls),
                                        cirq.InsertStrategy.NEW_THEN_INLINE)
            else:
                unknown = True

        elif isinstance(op, quantumpseudocode.AllocQuregOperation):
            pass
        elif isinstance(op, quantumpseudocode.ReleaseQuregOperation):
            pass
        else:
            unknown = True

        # if unknown:
        #     raise NotImplementedError("Unrecognized operation: {!r}".format(operation))

        return [operation]


class CountNots(quantumpseudocode.Lens):
    def __init__(self):
        super().__init__()
        self.counts = collections.Counter()

    def _val(self):
        return self.counts

    def modify(self, operation: 'quantumpseudocode.Operation'):
        op, controls = separate_controls(operation)

        if isinstance(op, quantumpseudocode.SignatureOperation):
            if op.gate == quantumpseudocode.OP_TOGGLE:
                targets = op.args.pass_into(_toggle_targets)
                if len(controls) > 1:
                    self.counts[1] += 2 * (len(targets) - 1)
                    self.counts[len(controls)] += 1
                else:
                    self.counts[len(controls)] += len(targets)

        return [operation]
