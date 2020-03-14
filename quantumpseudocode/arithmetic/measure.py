import random
from typing import List, Union, Callable, Any, Optional, TypeVar, Generic, overload, ContextManager

import quantumpseudocode as qp


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
        op = MeasureOperation(qp.RawQureg([val]), lambda e: bool(e[0]), reset)
    elif isinstance(val, qp.Qureg):
        op = MeasureOperation(val, lambda e: e, reset)
    elif isinstance(val, (qp.Quint, qp.QuintMod)):
        op = MeasureOperation(val.qureg, qp.little_endian_int, reset)
    else:
        raise NotImplementedError(f"Don't know how to measure {val!r}.")

    qp.global_logger.do_measure_qureg(op)
    assert op.results is not None
    return op.results


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
    return _measure_op_x(val)


def _measure_op_x(
        val: Union[qp.RValue[T], qp.Qubit, qp.Qureg, qp.Quint] = None
        ) -> Union['qp.MeasureXForPhaseKickOperation[bool]',
                   'qp.MeasureXForPhaseKickOperation[int]',
                   'qp.MeasureXForPhaseKickOperation[List[bool]]']:
    if isinstance(val, qp.Qubit):
        return qp.StartMeasurementBasedUncomputation(qp.RawQureg([val]), lambda e: bool(e[0]))

    if isinstance(val, qp.Qureg):
        return qp.StartMeasurementBasedUncomputation(val, lambda e: e)

    if isinstance(val, (qp.Quint, qp.QuintMod)):
        return qp.StartMeasurementBasedUncomputation(val.qureg, qp.little_endian_int)

    raise NotImplementedError("Don't know {!r}".format(val))


class MeasureOperation(Generic[T]):
    def __init__(self,
                 targets: qp.Qureg,
                 interpret: Callable[[List[bool]], T],
                 reset: bool):
        self.targets = targets
        self.interpret = interpret
        self.reset = reset
        self.raw_results = None

    def take_default_result(self, bias: float):
        if self.raw_results is None:
            self.raw_results = tuple(random.random() < bias for _ in range(len(self.targets)))

    @property
    def results(self) -> T:
        assert self.raw_results is not None
        return self.interpret(self.raw_results)

    def __repr__(self):
        return 'qp.MeasureOperation({!r}, {!r}, {!r})'.format(
            self.targets, self.interpret, self.reset)


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
        qp.global_logger.do_start_measurement_based_uncomputation(self)
        return self.results

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self.captured_phase_degrees is not None
        qp.global_logger.do_end_measurement_based_uncomputation(
            qp.EndMeasurementBasedComputationOp(self.targets, self.captured_phase_degrees))


class EndMeasurementBasedComputationOp:
    def __init__(self, targets: qp.Qureg, expected_phase_degrees: int):
        self.targets = targets
        self.expected_phase_degrees = expected_phase_degrees

    def __repr__(self):
        return f'qp.EndMeasurementBasedComputationOp({self.expected_phase_degrees})'
