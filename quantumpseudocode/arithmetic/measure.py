from typing import List, Union, Callable, Any, Optional, TypeVar, Generic, overload

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


def measure_x_for_phase_fixup_and_reset(val: qp.Qubit) -> bool:
    op = qp.MeasureXForPhaseKickOperation(val)
    qp.emit(op)
    return op.result


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

    if isinstance(val, qp.Quint):
        def little_endian_int(e: List[bool]):
            t = 0
            for b in reversed(e):
                t <<= 1
                if b:
                    t |= 1
            return t
        return MeasureOperation(val.qureg, little_endian_int, reset)

    if isinstance(val, qp.RValue):
        return _MeasureRValueOperation(val, reset)

    raise NotImplementedError("Don't know {!r}".format(val))


class _MeasureRValueOperation(Generic[T], Operation):
    def __init__(self,
                 target: qp.RValue[T],
                 reset: bool):
        self.target = target
        self.reset = reset
        self.results = None

    def permutation_registers(self):
        return []

    def permute(self, forward: bool, args):
        pass

    def emit_ops(self, controls: 'qp.QubitIntersection'):
        assert len(controls) == 0, "Not allowed to control measurement."

        with qp.hold(self.target) as target:
            self.results = measure(target)


class MeasureOperation(Generic[T], FlagOperation):
    def __init__(self,
                 targets: qp.Qureg,
                 interpret: Callable[[List[bool]], T],
                 reset: bool):
        self.targets = targets
        self.interpret = interpret
        self.reset = reset
        self.raw_results = None

    @property
    def results(self):
        assert self.raw_results is not None
        return self.interpret(self.raw_results)

    def __repr__(self):
        return 'qp.MeasureOperation({!r}, {!r}, {!r})'.format(
            self.targets, self.interpret, self.reset)


class MeasureXForPhaseKickOperation(FlagOperation):
    def __init__(self, target: qp.Qubit):
        self.target = target
        self.result = None  # type: Optional[bool]

    def __str__(self):
        return "Mxc({})".format(self.target)

    def __repr__(self):
        return 'qp.MeasureXForPhaseKickOperation({!r})'.format(
            self.target)
