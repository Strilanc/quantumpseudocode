import random
from typing import List, Union, Callable, Any, Optional, TypeVar, Generic, overload, ContextManager

import quantumpseudocode as qp
from quantumpseudocode.ops import Operation, FlagOperation


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
    op = _measure_op(val, reset=reset)
    qp.emit(op)
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


def _measure_op(
        val: Union[qp.RValue[T], qp.Qubit, qp.Qureg, qp.Quint] = None,
        *,
        reset: bool = False
        ) -> Union['MeasureOperation[bool]',
                   'MeasureOperation[int]',
                   'MeasureOperation[List[bool]]',
                   '_MeasureRValueOperation[T]']:
    if isinstance(val, qp.Qubit):
        return MeasureOperation(qp.RawQureg([val]),
                                lambda e: bool(e[0]),
                                reset)

    if isinstance(val, qp.Qureg):
        return MeasureOperation(val, lambda e: e, reset)

    if isinstance(val, (qp.Quint, qp.QuintMod)):
        return MeasureOperation(val.qureg, qp.little_endian_int, reset)

    if isinstance(val, qp.RValue):
        return _MeasureRValueOperation(val, reset)

    raise NotImplementedError("Don't know {!r}".format(val))


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


class _MeasureRValueOperation(Generic[T], Operation):
    def __init__(self,
                 target: qp.RValue[T],
                 reset: bool):
        self.target = target
        self.reset = reset
        self.results = None

    def permute(self, forward: bool, args):
        pass

    def emit_ops(self, controls: 'qp.QubitIntersection'):
        assert controls == qp.QubitIntersection.ALWAYS, "Not allowed to control measurement."

        with qp.hold(self.target) as target:
            self.results = measure(target)


class MeasureOperation(Generic[T], Operation):
    def __init__(self,
                 targets: qp.Qureg,
                 interpret: Callable[[List[bool]], T],
                 reset: bool):
        self.targets = targets
        self.interpret = interpret
        self.reset = reset
        self.raw_results = None

    def validate_controls(self, controls: 'qp.QubitIntersection'):
        assert controls == qp.QubitIntersection.ALWAYS

    def emit_ops(self, controls: 'qp.QubitIntersection'):
        raise ValueError(f"{self} must be emulated.")

    def mutate_state(self, sim_state: 'qp.ClassicalSimState', forward: bool) -> None:
        assert self.raw_results is None
        reg = sim_state.quint_buf(qp.Quint(self.targets))
        self.raw_results = tuple(reg[i] for i in range(len(reg)))
        if self.reset:
            reg[:] = 0

    @property
    def results(self) -> T:
        assert self.raw_results is not None
        return self.interpret(self.raw_results)

    def __repr__(self):
        return 'qp.MeasureOperation({!r}, {!r}, {!r})'.format(
            self.targets, self.interpret, self.reset)


class StartMeasurementBasedUncomputation(Generic[T], Operation):
    def __init__(self,
                 targets: qp.Qureg,
                 interpret: Callable[[List[bool]], T]):
        self.targets = targets
        self.interpret = interpret
        self.raw_results = None
        self.captured_phase_degrees = None

    def validate_controls(self, controls: 'qp.QubitIntersection'):
        assert controls == qp.QubitIntersection.ALWAYS

    @property
    def results(self) -> T:
        assert self.raw_results is not None
        return self.interpret(self.raw_results)

    def emit_ops(self, controls: 'qp.QubitIntersection'):
        raise ValueError(f"{self} must be emulated.")

    def mutate_state(self, sim_state: 'qp.ClassicalSimState', forward: bool) -> None:
        assert forward

        self.raw_results = []
        self.captured_phase_degrees = sim_state.phase_degrees
        reg = sim_state.quint_buf(qp.Quint(self.targets))
        chooser = sim_state.measurement_based_uncomputation_result_chooser()

        # Simulate X basis measurements.
        for i in range(len(self.targets)):
            result = chooser()
            self.raw_results.append(result)
            if result and reg[i]:
                sim_state.phase_degrees += 180

        # Reset target.
        reg[:] = 0

    def __str__(self):
        return "Mxc({})".format(self.targets)

    def __repr__(self):
        return 'qp.StartMeasurementBasedUncomputation({!r}, {!r})'.format(
            self.targets, self.interpret)

    def __bool__(self):
        raise ValueError("Use 'with' on result of qp.measurement_based_uncomputation. "
                         "It returns a context manager, not a boolean.")

    def __enter__(self):
        qp.emit(self)
        return self.results

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self.captured_phase_degrees is not None
        qp.emit(qp.EndMeasurementBasedComputationOp(self.captured_phase_degrees))


class EndMeasurementBasedComputationOp(Operation):
    def __init__(self, expected_phase_degrees: int):
        self.expected_phase_degrees = expected_phase_degrees

    def validate_controls(self, controls: 'qp.QubitIntersection'):
        assert controls == qp.QubitIntersection.ALWAYS

    def mutate_state(self, sim_state: 'qp.ClassicalSimState', forward: bool) -> None:
        if sim_state.phase_degrees != self.expected_phase_degrees:
            raise AssertionError('Failed to uncompute. Measurement based uncomputation failed to fix phase flips.')

    def emit_ops(self, controls: 'qp.QubitIntersection'):
        raise ValueError(f"{self} must be emulated.")

    def __repr__(self):
        return f'qp.EndMeasurementBasedComputationOp({self.expected_phase_degrees})'
