from typing import Optional, Tuple, Iterable, Union

import cirq

import quantumpseudocode


@cirq.value_equality
class Qubit:
    def __init__(self,
                 name: 'Union[quantumpseudocode.UniqueHandle, str]' = '',
                 index: Optional[int] = None):
        self.name = name if isinstance(name, quantumpseudocode.UniqueHandle) else quantumpseudocode.UniqueHandle(name)
        self.index = index

    def _value_equality_values_(self):
        return self.name, self.index

    def __str__(self):
        if self.index is None:
            return str(self.name)
        return '{}[{}]'.format(self.name, self.index)

    def __repr__(self):
        return 'quantumpseudocode.Qubit({!r}, {!r})'.format(self.name, self.index)

    def __and__(self, other):
        if isinstance(other, Qubit):
            return quantumpseudocode.QubitIntersection((self, other))
        return NotImplemented

    def __ixor__(self, other):
        if other in [False, 0]:
            return self

        if other in [True, 1]:
            quantumpseudocode.emit(quantumpseudocode.OP_TOGGLE(quantumpseudocode.RawQureg([self])))
            return self

        if isinstance(other, (Qubit, quantumpseudocode.QubitIntersection)):
            quantumpseudocode.emit(quantumpseudocode.OP_TOGGLE(quantumpseudocode.RawQureg([self])).controlled_by(other))
            return self

        rev = getattr(other, '__rixor__', None)
        if rev is not None:
            return rev(self)

        return NotImplemented
