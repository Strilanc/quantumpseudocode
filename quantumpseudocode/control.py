from typing import Union, Any, Optional

import quantumpseudocode as qp


class ControlledRValue(qp.RValue):
    def __init__(self,
                 controls: qp.QubitIntersection,
                 rvalue: qp.RValue):
        self.controls = controls
        self.rvalue = rvalue

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

    def __repr__(self):
        return 'qp.ControlledRValue({!r}, {!r})'.format(self.controls,
                                                           self.rvalue)


class _ControlledByWithoutRValue:
    def __init__(self, controls: qp.QubitIntersection):
        self.controls = controls

    def __and__(self, other):
        if isinstance(other, ControlledRValue):
            return ControlledRValue(self.controls & other.controls, other.rvalue)
        if isinstance(other, qp.RValue):
            return ControlledRValue(self.controls, other)
        if isinstance(other, int):
            return ControlledRValue(self.controls, qp.IntRValue(other))
        return NotImplemented

    def __rand__(self, other):
        return self.__and__(other)


def controlled_by(qubits: Union[qp.Qubit, qp.QubitIntersection]):
    if isinstance(qubits, qp.Qubit):
        qubits = qp.QubitIntersection((qubits,))
    return _ControlledByWithoutRValue(qubits)
