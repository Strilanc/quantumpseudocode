import abc
from typing import Union, Any, Callable

import cirq

import quantumpseudocode as qp


class ClassicalSimState(metaclass=abc.ABCMeta):
    phase_degrees: float

    @abc.abstractmethod
    def alloc(self, name: str, length: int, *, x_basis: bool = False):
        raise NotImplementedError()

    @abc.abstractmethod
    def release(self, name: str, *, dirty: bool = False):
        raise NotImplementedError()

    @abc.abstractmethod
    def measurement_based_uncomputation_result_chooser(self) -> Callable[[], bool]:
        raise NotImplementedError()

    @abc.abstractmethod
    def quint_buf(self, quint: 'qp.Quint') -> 'qp.IntBuf':
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_location(self, loc: Any, allow_mutate: bool) -> Any:
        raise NotImplementedError()


class Operation:
    def validate_controls(self, controls: 'qp.QubitIntersection'):
        pass

    def emit_ops(self, controls: 'qp.QubitIntersection'):
        raise RuntimeError('Unprocessed terminal operation: {!r}'.format(self))

    def mutate_state(self, sim_state: 'qp.ClassicalSimState', forward: bool) -> None:
        raise NotImplementedError('mutate_state not implemented by {!r}'.format(self))

    def controlled_by(self, controls: Union['qp.Qubit',
                                            'qp.QubitIntersection']):
        if isinstance(controls, qp.Qubit):
            return qp.ControlledOperation(self, qp.QubitIntersection((controls,)))
        if controls == qp.QubitIntersection.ALWAYS:
            return self
        return qp.ControlledOperation(self, controls)
