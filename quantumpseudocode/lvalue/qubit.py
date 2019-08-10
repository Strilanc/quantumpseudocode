from typing import Optional, Union, Any

import cirq
from typing_extensions import Protocol

import quantumpseudocode as qp
from .lvalue import LValue
from quantumpseudocode.rvalue import RValue


@cirq.value_equality
class Qubit(RValue[bool], LValue[bool]):
    class Borrowed(Protocol):
        # Union[int, 'qp.Qubit', 'qp.RValue[bool]']
        pass

    class Control(Protocol):
        # Union[None, 'qp.QubitIntersection', 'qp.Qubit', bool, 'qp.RValue[bool]']
        pass

    def __init__(self,
                 name: 'Union[qp.UniqueHandle, str]' = '',
                 index: Optional[int] = None):
        self.name = name if isinstance(name, qp.UniqueHandle) else qp.UniqueHandle(name)
        self.index = index

    def resolve(self, sim_state: 'qp.ClassicalSimState', allow_mutate: bool):
        buf = sim_state.quint_buf(qp.Quint(qp.RawQureg([self])))
        return buf if allow_mutate else bool(int(buf))

    def existing_storage_location(self) -> Any:
        return self

    def make_storage_location(self, name: Optional[str] = None):
        return qp.Qubit(name)

    def init_storage_location(self,
                              location: 'qp.Qubit',
                              controls: 'qp.QubitIntersection'):
        location ^= self & qp.controlled_by(controls)

    def del_storage_location(self,
                             location: 'qp.Qubit',
                             controls: 'qp.QubitIntersection'):
        with qp.measurement_based_uncomputation(location) as bit:
            qp.phase_flip(bit & self & controls)

    def _value_equality_values_(self):
        return self.name, self.index

    def __str__(self):
        if self.index is None:
            return str(self.name)
        return '{}[{}]'.format(self.name, self.index)

    def __repr__(self):
        return 'qp.Qubit({!r}, {!r})'.format(self.name, self.index)

    def __and__(self, other):
        if isinstance(other, Qubit):
            return qp.QubitIntersection((self, other))
        if other in [False, 0]:
            return qp.QubitIntersection.NEVER
        if other in [True, 1]:
            return self
        return NotImplemented

    def __rand__(self, other):
        return self.__and__(other)

    def init(self,
             value: Union[bool, 'qp.RValue[bool]'],
             controls: 'qp.QubitIntersection' = None):
        if controls is None:
            controls = qp.QubitIntersection.ALWAYS
        qp.rval(value).init_storage_location(self, controls)

    def clear(self,
              value: Union[bool, 'qp.RValue[bool]'],
              controls: 'qp.QubitIntersection' = None):
        if controls is None:
            controls = qp.QubitIntersection.ALWAYS
        qp.rval(value).del_storage_location(self, controls)

    def __ixor__(self, other):
        other, controls = qp.ControlledRValue.split(other)
        if controls == qp.QubitIntersection.NEVER:
            return self

        if other in [False, 0]:
            return self

        if other in [True, 1]:
            qp.cnot(qp.QubitIntersection.ALWAYS, self)
            return self

        if isinstance(other, Qubit):
            qp.cnot(other, self)
            return self

        rev = getattr(other, '__rixor__', None)
        if rev is not None:
            return rev(qp.ControlledLValue(controls, self))

        return NotImplemented
