import abc
from typing import Union, Any, Callable

import quantumpseudocode as qp


class ClassicalSimState:
    phase_degrees: float

    def measurement_based_uncomputation_result_chooser(self) -> Callable[[], bool]:
        raise NotImplementedError()

    def quint_buf(self, quint: 'qp.Quint') -> 'qp.IntBuf':
        raise NotImplementedError()

    def resolve_location(self, loc: Any, allow_mutate: bool) -> Any:
        pass


class Operation(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def mutate_state(self, sim_state: 'qp.ClassicalSimState', forward: bool) -> None:
        pass

    def controlled_by(self, controls: Union['qp.Qubit',
                                            'qp.QubitIntersection']):
        if isinstance(controls, qp.Qubit):
            return qp.ControlledOperation(self, qp.QubitIntersection((controls,)))
        if controls == qp.QubitIntersection.ALWAYS:
            return self
        return qp.ControlledOperation(self, controls)
