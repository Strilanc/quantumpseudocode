import random
from typing import List, Union, Callable, Any, Optional, TypeVar, Generic, overload, ContextManager, Tuple

import quantumpseudocode as qp
from quantumpseudocode import sink

T = TypeVar('T')


@overload
def measure(val: qp.RValue[T], *, reset: bool = False) -> T:
    pass


@overload
def measure(val: qp.Quint, *, reset: bool = False) -> int:
    pass


@overload
def measure(val: qp.Qubit, *, reset: bool = False) -> bool:
    pass


@overload
def measure(val: qp.Qureg, *, reset: bool = False) -> List[bool]:
    pass


def measure(val: Union[qp.RValue[T], qp.Quint, qp.Qureg, qp.Qubit],
            *,
            reset: bool = False) -> Union[bool, int, List[bool], T]:
    if isinstance(val, qp.RValue):
        with qp.hold(val) as target:
            return measure(target)

    if isinstance(val, qp.Qubit):
        qureg = val.qureg
        wrap = bool
    elif isinstance(val, qp.Qureg):
        qureg = val
        wrap = lambda e: qp.little_endian_bits(e, len(val))
    elif isinstance(val, (qp.Quint, qp.QuintMod)):
        qureg = val.qureg
        wrap = lambda e: e
    else:
        raise NotImplementedError(f"Don't know how to measure {val!r}.")

    result = sink.global_sink.do_measure(qureg, reset)
    return wrap(result)


@overload
def measurement_based_uncomputation(val: qp.Quint) -> ContextManager[int]:
    pass


@overload
def measurement_based_uncomputation(val: qp.Qubit) -> ContextManager[bool]:
    pass


@overload
def measurement_based_uncomputation(val: qp.Qureg) -> ContextManager[Tuple[bool, ...]]:
    pass


def measurement_based_uncomputation(
        val: Union[qp.Qubit, qp.Quint, qp.Qureg]) -> ContextManager[Union[int, bool, Tuple[bool, ...]]]:
    if isinstance(val, qp.Qubit):
        return MeasurementBasedUncomputationContext(val.qureg, bool)

    if isinstance(val, qp.Qureg):
        return MeasurementBasedUncomputationContext(val, lambda e: qp.little_endian_bits(e, len(val)))

    if isinstance(val, (qp.Quint, qp.QuintMod)):
        return MeasurementBasedUncomputationContext(val.qureg, lambda e: e)

    raise NotImplementedError(f"Don't know how to perform measurement based uncomputation on {val!r}")


class MeasurementBasedUncomputationContext(Generic[T]):
    def __init__(self, qureg: qp.Qureg, interpret: Callable[[int], T]):
        self.qureg = qureg
        self.interpret = interpret
        self._start_result = None

    def __bool__(self):
        raise ValueError("Used `qp.measurement_based_uncomputation` like a value instead of like a context manager.\n"
                         "Correct usage:\n"
                         "\n"
                         "    with qp.measurement_based_uncomputation(qureg) as x_basis_result:\n"
                         "        # Undo phase kickbacks caused by the measurement.\n"
                         "        ...\n"
                         "\n")

    def __enter__(self) -> T:
        assert self._start_result is None
        self._start_result = sink.global_sink.do_start_measurement_based_uncomputation(self.qureg)
        return self.interpret(self._start_result.measurement)

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self._start_result is not None
        sink.global_sink.do_end_measurement_based_uncomputation(
            self.qureg, self._start_result)
