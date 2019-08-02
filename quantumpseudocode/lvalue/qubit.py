from typing import Optional, Union

import cirq
from typing_extensions import Protocol

import quantumpseudocode as qp
from .lvalue import LValue


@cirq.value_equality
class Qubit(LValue[bool]):
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

    def _rval_(self):
        return qp.QubitRValue(self)

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
             value: 'qp.RValue[bool]',
             controls: 'qp.QubitIntersection' = None):
        if controls is None:
            controls = qp.QubitIntersection.ALWAYS
        qp.emit(
            qp.LetRValueOperation(value, self).controlled_by(controls))

    def clear(self,
              value: 'qp.RValue[bool]',
              controls: 'qp.QubitIntersection' = None):
        if controls is None:
            controls = qp.QubitIntersection.ALWAYS
        qp.emit(
            qp.DelRValueOperation(value, self).controlled_by(controls))

    def __ixor__(self, other):
        other, controls = qp.ControlledRValue.split(other)
        if controls == qp.QubitIntersection.NEVER:
            return self

        if other in [False, 0]:
            return self

        if other in [True, 1]:
            qp.emit(qp.Toggle(lvalue=qp.RawQureg([self])))
            return self

        if isinstance(other, Qubit):
            qp.emit(qp.Toggle(lvalue=qp.RawQureg([self])).controlled_by(other))
            return self

        rev = getattr(other, '__rixor__', None)
        if rev is not None:
            return rev(qp.ControlledLValue(controls, self))

        return NotImplemented
