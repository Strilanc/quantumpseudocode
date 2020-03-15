import random
from typing import List, Union, Callable, Any, Optional, TypeVar, Generic, overload, ContextManager

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
        wrap = qp.little_endian_bits()
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
def measurement_based_uncomputation(val: qp.Qureg) -> ContextManager[List[bool]]:
    pass


def measurement_based_uncomputation(
        val: Union[qp.Qubit, qp.Quint, qp.Qureg]) -> ContextManager[Union[int, bool, List[bool]]]:
    if isinstance(val, qp.Qubit):
        return qp.StartMeasurementBasedUncomputation(val.qureg, lambda e: bool(e[0]))

    if isinstance(val, qp.Qureg):
        return qp.StartMeasurementBasedUncomputation(val, lambda e: e)

    if isinstance(val, (qp.Quint, qp.QuintMod)):
        return qp.StartMeasurementBasedUncomputation(val.qureg, qp.little_endian_int)

    raise NotImplementedError(f"Don't know {val!r}")


class StartMeasurementBasedUncomputation(Generic[T]):
    def __init__(self,
                 targets: qp.Qureg,
                 interpret: Callable[[List[bool]], T]):
        self.targets = targets
        self.interpret = interpret
        self.raw_results = None
        self.captured_phase_degrees = None

    @property
    def results(self) -> T:
        assert self.raw_results is not None
        return self.interpret(self.raw_results)

    def take_default_result(self, bias: float):
        if self.raw_results is None:
            self.raw_results = tuple(random.random() < bias for _ in range(len(self.targets)))

    def __str__(self):
        return "Mxc({})".format(self.targets)

    def __repr__(self):
        return 'qp.StartMeasurementBasedUncomputation({!r}, {!r})'.format(
            self.targets, self.interpret)

    def __bool__(self):
        raise ValueError("Use 'with' on result of qp.measurement_based_uncomputation. "
                         "It returns a context manager, not a boolean.")

    def __enter__(self):
        sink.global_sink.do_start_measurement_based_uncomputation(self)
        return self.results

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self.captured_phase_degrees is not None
        sink.global_sink.do_end_measurement_based_uncomputation(
            qp.EndMeasurementBasedComputationOp(self.targets, self.captured_phase_degrees))


class EndMeasurementBasedComputationOp:
    def __init__(self, targets: qp.Qureg, expected_phase_degrees: int):
        self.targets = targets
        self.expected_phase_degrees = expected_phase_degrees

    def __repr__(self):
        return f'qp.EndMeasurementBasedComputationOp({self.expected_phase_degrees})'
