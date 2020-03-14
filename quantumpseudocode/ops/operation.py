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
