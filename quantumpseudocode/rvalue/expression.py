from typing import Optional, Tuple, Iterable, Any

import cirq

import quantumpseudocode as qp
from .rvalue import RValue
from quantumpseudocode import sink


@cirq.value_equality
class ScaledIntRValue(RValue[int]):
    """An rvalue for expressions like `quint * int`."""

    def __init__(self, coherent: 'qp.Quint', constant: int):
        self.coherent = coherent
        self.constant = constant

    def _value_equality_values_(self):
        return self.coherent, self.constant

    def __str__(self):
        return 'rval({} * {})'.format(self.coherent, self.constant)

    def __repr__(self):
        return 'qp.ScaledIntRValue({!r}, {!r})'.format(
            self.coherent, self.constant)

    def __riadd__(self, other):
        other, controls = qp.ControlledLValue.split(other)
        if controls == qp.QubitIntersection.NEVER:
            return other

        if isinstance(other, qp.Quint):
            qp.arithmetic.do_plus_product(
                lvalue=other,
                quantum_factor=self.coherent,
                const_factor=self.constant,
                control=controls,
            )
            return other

        return NotImplemented

    def __risub__(self, other):
        other, controls = qp.ControlledLValue.split(other)
        if controls == qp.QubitIntersection.NEVER:
            return other

        if isinstance(other, qp.Quint):
            qp.arithmetic.do_plus_product(
                lvalue=other,
                quantum_factor=self.coherent,
                const_factor=self.constant,
                control=controls,
                forward=False,
            )
            return other

        return NotImplemented

    def alloc_storage_location(self, name: Optional[str] = None):
        return qp.qalloc(len=len(self.coherent) + self.constant.bit_length(), name=name)

    def init_storage_location(self,
                              location: 'qp.Quint',
                              controls: 'qp.QubitIntersection'):
        qp.arithmetic.do_plus_product(
            control=controls,
            lvalue=location,
            quantum_factor=self.coherent,
            const_factor=self.constant,
        )

    def clear_storage_location(self,
                               location: Any,
                               controls: 'qp.QubitIntersection'):
        qp.arithmetic.do_plus_product(
            control=controls,
            lvalue=location,
            quantum_factor=self.coherent,
            const_factor=self.constant,
            forward=False
        )


@cirq.value_equality
class QubitIntersection(RValue[bool]):
    """The logical-and of several qubits and bits."""

    ALWAYS = None # type: QubitIntersection
    NEVER = None # type: QubitIntersection

    def __init__(self, qubits: Tuple['qp.Qubit', ...] = (), bit: bool = True):
        assert all(isinstance(e, qp.Qubit) for e in qubits)
        self.qubits = tuple(qubits) if bit else ()
        assert len(self.qubits) == len(set(self.qubits))
        self.bit = bool(bit)

    def resolve(self, sim_state: 'qp.ClassicalSimState', allow_mutate: bool) -> bool:
        v = qp.Quint(qp.RawQureg(self.qubits)).resolve(sim_state, False)
        return self.bit and v == (1 << len(self.qubits)) - 1

    @staticmethod
    def try_from(val: Any) -> Optional['qp.QubitIntersection']:
        if isinstance(val, (bool, int)):
            if val in [False, 0]:
                return qp.QubitIntersection.NEVER

            if val in [True, 1]:
                return qp.QubitIntersection.ALWAYS

        if isinstance(val, qp.Qubit):
            return qp.QubitIntersection((val,))

        if isinstance(val, qp.QubitIntersection):
            return val

        return None

    def _value_equality_values_(self):
        return self.bit and frozenset(self.qubits)

    def __rand__(self, other):
        return self.__and__(other)

    def __and__(self, other):
        if isinstance(other, QubitIntersection):
            return QubitIntersection(self.qubits + other.qubits, bit=self.bit and other.bit)
        if isinstance(other, qp.Qubit):
            return QubitIntersection(self.qubits + (other,), bit=self.bit)
        if other in [False, 0]:
            return qp.QubitIntersection.NEVER
        if other in [True, 1]:
            return self
        return NotImplemented

    def alloc_storage_location(self, name: Optional[str] = None):
        return qp.qalloc(name=name)

    def init_storage_location(self,
                              location: 'qp.Qubit',
                              controls: 'qp.QubitIntersection'):
        location ^= self & controls

    def clear_storage_location(self,
                               location: Any,
                               controls: 'qp.QubitIntersection'):
        with qp.measurement_based_uncomputation(location) as b:
            qp.phase_flip(self & controls & b)

    def __str__(self):
        if not self.bit:
            return 'never'
        if not self.qubits:
            return 'always'
        return ' & '.join(str(e) for e in self.qubits)

    def __repr__(self):
        if not self.bit:
            return 'qp.QubitIntersection(bit=False)'
        return 'qp.QubitIntersection({!r})'.format(self.qubits)


QubitIntersection.ALWAYS = QubitIntersection()
QubitIntersection.NEVER = QubitIntersection(bit=False)
