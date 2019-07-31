from typing import Union, Any, Optional, Tuple

import cirq

import quantumpseudocode as qp


@cirq.value_equality
class ControlledRValue(qp.RValue):
    def __init__(self,
                 controls: 'qp.QubitIntersection',
                 rvalue: 'qp.RValue'):
        self.controls = controls
        self.rvalue = rvalue

    @staticmethod
    def split(op: Any) -> Tuple[Any, 'qp.QubitIntersection']:
        if isinstance(op, qp.ControlledRValue):
            return op.rvalue, op.controls
        return op, qp.QubitIntersection.ALWAYS

    def resolve(self, sim_state: 'qp.ClassicalSimState', allow_mutate: bool):
        if not self.controls.resolve(sim_state, False):
            return 0
        return sim_state.resolve_location(self.rvalue, False)

    def make_storage_location(self, name: Optional[str] = None):
        return self.rvalue.make_storage_location(name)

    def init_storage_location(self,
                              location: Any,
                              controls: 'qp.QubitIntersection'):
        self.rvalue.init_storage_location(location, controls & self.controls)

    def del_storage_location(self,
                             location: Any,
                            controls: 'qp.QubitIntersection'):
        self.rvalue.del_storage_location(location, controls & self.controls)

    def __str__(self):
        return 'controlled({}, {})'.format(self.rvalue, self.controls)

    def _value_equality_values_(self):
        return self.rvalue, self.controls

    def __repr__(self):
        return 'qp.ControlledRValue({!r}, {!r})'.format(self.controls,
                                                           self.rvalue)


@cirq.value_equality
class ControlledLValue:
    def __init__(self,
                 controls: 'qp.QubitIntersection',
                 lvalue: Union['qp.Qubit', 'qp.Quint', 'qp.Qureg', 'qp.ControlledLValue']):
        if isinstance(lvalue, ControlledLValue):
            lvalue = lvalue.lvalue
            controls = controls & lvalue.controls
        self.lvalue = lvalue
        self.controls = controls

    @staticmethod
    def split(op: Any) -> Tuple[Any, 'qp.QubitIntersection']:
        if isinstance(op, qp.ControlledLValue):
            return op.lvalue, op.controls
        return op, qp.QubitIntersection.ALWAYS

    def _value_equality_values_(self):
        return self.lvalue, self.controls

    def __repr__(self):
        return 'qp.ControlledLValue({!r}, {!r})'.format(self.controls, self.lvalue)


class _ControlledByWithoutRValue:
    def __init__(self, controls: qp.QubitIntersection):
        self.controls = controls
        self._cond = qp.condition(self.controls)

    def __enter__(self):
        return self._cond.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._cond.__exit__(exc_type, exc_val, exc_tb)

    def __and__(self, other):
        if isinstance(other, ControlledRValue):
            return ControlledRValue(self.controls & other.controls,
                                    other.rvalue)
        if isinstance(other, (int, qp.Quint, qp.RValue)):
            return ControlledRValue(self.controls, qp.rval(other))
        return NotImplemented

    def __rand__(self, other):
        return self.__and__(other)


def controlled_by(qubits: Union[qp.Qubit, qp.QubitIntersection]):
    if isinstance(qubits, qp.Qubit):
        qubits = qp.QubitIntersection((qubits,))
    return _ControlledByWithoutRValue(qubits)
