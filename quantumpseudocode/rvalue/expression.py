from typing import Optional, Tuple, Iterable, Any

import cirq

import quantumpseudocode
from .rvalue import RValue


@cirq.value_equality
class ScaledIntRValue(RValue[int]):
    """An rvalue for expressions like `quint * int`."""

    def __init__(self, coherent: 'quantumpseudocode.Quint', constant: int):
        self.coherent = coherent
        self.constant = constant

    def _value_equality_values_(self):
        return self.coherent, self.constant

    def __str__(self):
        return 'rval({} * {})'.format(self.coherent, self.constant)

    def __repr__(self):
        return 'quantumpseudocode.ScaledIntRValue({!r}, {!r})'.format(
            self.coherent, self.constant)

    def __riadd__(self, other):
        if isinstance(other, quantumpseudocode.Quint):
            quantumpseudocode.emit(quantumpseudocode.PlusEqualTimesGate(
                lvalue=other,
                quantum_factor=self.coherent,
                const_factor=self.constant,
            ))
            return other

        return NotImplemented

    def permutation_registers(self) -> Iterable['quantumpseudocode.Qureg']:
        return [self.coherent.qureg]

    def value_from_permutation_registers(self, args: Tuple[int, ...]
                                         ) -> int:
        return args[0]

    def permutation_registers_from_value(self, val: int) -> Tuple[int, ...]:
        return val,

    def make_storage_location(self, name: Optional[str] = None):
        return quantumpseudocode.Quint(quantumpseudocode.NamedQureg(
            name, len(self.coherent) + self.constant.bit_length()))

    def init_storage_location(self,
                              location: 'quantumpseudocode.Quint',
                              controls: 'quantumpseudocode.QubitIntersection'):
        quantumpseudocode.emit(quantumpseudocode.PlusEqualTimesGate(
            lvalue=location,
            quantum_factor=self.coherent,
            const_factor=self.constant,
        ).controlled_by(controls))


@cirq.value_equality
class QubitIntersection(RValue[bool]):
    """The logical-and of several qubits."""

    EMPTY = None # type: QubitIntersection

    def __init__(self, qubits: Tuple['quantumpseudocode.Qubit', ...]):
        self.qubits = tuple(qubits)

    def _value_equality_values_(self):
        return frozenset(self.qubits)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.qubits[item]
        return NotImplemented

    def __len__(self):
        return len(self.qubits)

    def __rand__(self, other):
        return self.__and__(other)

    def __and__(self, other):
        if isinstance(other, QubitIntersection):
            return QubitIntersection(self.qubits + other.qubits)
        if isinstance(other, quantumpseudocode.Qubit):
            return QubitIntersection(self.qubits + (other,))
        return NotImplemented

    def permutation_registers(self) -> Iterable['quantumpseudocode.Qureg']:
        return quantumpseudocode.RawQureg(self.qubits)

    def value_from_permutation_registers(self, args: Tuple[int, ...]) -> bool:
        return all(args)

    def permutation_registers_from_value(self, val: bool) -> Tuple[int, ...]:
        raise NotImplementedError("Irreversible.")

    def __rixor__(self, other):
        if isinstance(other, quantumpseudocode.Qubit):
            quantumpseudocode.emit(quantumpseudocode.OP_TOGGLE(quantumpseudocode.RawQureg([other])).controlled_by(self))
            return self
        return NotImplemented

    def make_storage_location(self, name: Optional[str] = None):
        return quantumpseudocode.Qubit(name)

    def init_storage_location(self,
                              location: 'quantumpseudocode.Qubit',
                              controls: 'quantumpseudocode.QubitIntersection'):
        quantumpseudocode.emit(quantumpseudocode.LetAnd(lvalue=location).controlled_by(self & controls))

    def __str__(self):
        return ' & '.join(str(e) for e in self)

    def __repr__(self):
        return 'quantumpseudocode.QubitIntersection({!r})'.format(self.qubits)


QubitIntersection.EMPTY = QubitIntersection(())
