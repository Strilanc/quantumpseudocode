import abc
from typing import List, Optional, ContextManager, cast, Tuple, Union

import quantumpseudocode as qp

lens_stack: List['qp.Logger'] = []


def emit(operation: 'qp.Operation', controls: 'qp.QubitIntersection'):
    for logger in lens_stack:
        logger.log(operation, controls)


def capture(out: 'Optional[List[qp.Operation]]' = None,
            measure_bias: Optional[float] = None) -> ContextManager[List['qp.Operation']]:
    return cast(ContextManager, CaptureLens([] if out is None else out, measure_bias=measure_bias))


class EmptyManager:
    def __init__(self, value=None):
        self.value = value

    def __enter__(self):
        return self.value

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class Logger(metaclass=abc.ABCMeta):
    def __init__(self):
        self.used = False

    def log(self, op: 'qp.Operation', cnt: 'qp.QubitIntersection'):
        if isinstance(op, qp.AllocQuregOperation):
            assert cnt == qp.QubitIntersection.ALWAYS
            self.do_allocate_qureg(op)
        elif isinstance(op, qp.ReleaseQuregOperation):
            assert cnt == qp.QubitIntersection.ALWAYS
            self.do_release_qureg(op)
        elif isinstance(op, qp.Toggle):
            self.do_toggle_qureg(op, cnt)
        elif op == qp.OP_PHASE_FLIP:
            self.do_phase_flip(op, cnt)
        elif isinstance(op, qp.MeasureOperation):
            assert cnt == qp.QubitIntersection.ALWAYS
            self.do_measure_qureg(op)
        elif isinstance(op, qp.StartMeasurementBasedUncomputation):
            assert cnt == qp.QubitIntersection.ALWAYS
            self.do_start_measurement_based_uncomputation(op)
        elif isinstance(op, qp.EndMeasurementBasedComputationOp):
            assert cnt == qp.QubitIntersection.ALWAYS
            self.do_end_measurement_based_uncomputation(op)
        else:
            raise NotImplementedError(f"Unrecognized operation: {op!r}")

    @abc.abstractmethod
    def do_allocate_qureg(self, op: 'qp.AllocQuregOperation'):
        pass

    @abc.abstractmethod
    def do_release_qureg(self, op: 'qp.ReleaseQuregOperation'):
        pass

    @abc.abstractmethod
    def do_phase_flip(self, op, controls: 'qp.QubitIntersection'):
        pass

    @abc.abstractmethod
    def do_toggle_qureg(self, op: 'qp.Toggle', controls: 'qp.QubitIntersection'):
        pass

    @abc.abstractmethod
    def do_measure_qureg(self, op: 'qp.MeasureOperation'):
        pass

    @abc.abstractmethod
    def do_start_measurement_based_uncomputation(self, op: 'qp.StartMeasurementBasedUncomputation'):
        pass

    @abc.abstractmethod
    def do_end_measurement_based_uncomputation(self, op: 'qp.EndMeasurementBasedComputationOp'):
        pass

    def _val(self):
        return self

    def _succeeded(self):
        pass

    def __enter__(self):
        assert not self.used
        self.used = True
        lens_stack.append(self)
        return self._val()

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert lens_stack[-1] is self
        lens_stack.pop()
        if exc_type is None:
            self._succeeded()


class CaptureLens(Logger):
    def __init__(self, out: List[Union['qp.Operation', Tuple['qp.Operation', 'qp.QubitIntersection']]], measure_bias: Optional[float]):
        super().__init__()
        self.out = out
        self.measure_bias = measure_bias

    def __enter__(self):
        super().__enter__()
        return self.out

    def do_allocate_qureg(self, op: 'qp.AllocQuregOperation'):
        self.out.append(op)

    def do_release_qureg(self, op: 'qp.ReleaseQuregOperation'):
        self.out.append(op)

    def do_phase_flip(self, op, controls: 'qp.QubitIntersection'):
        if controls == qp.QubitIntersection.ALWAYS:
            self.out.append(op)
        else:
            self.out.append((op, controls))

    def do_toggle_qureg(self, op: 'qp.Toggle', controls: 'qp.QubitIntersection'):
        if controls == qp.QubitIntersection.ALWAYS:
            self.out.append(op)
        else:
            self.out.append((op, controls))

    def do_measure_qureg(self, op: 'qp.MeasureOperation'):
        if self.measure_bias is not None:
            op.take_default_result(bias=self.measure_bias)

    def do_start_measurement_based_uncomputation(self, op: 'qp.StartMeasurementBasedUncomputation'):
        if self.measure_bias is not None:
            op.captured_phase_degrees = 0
            op.take_default_result(bias=self.measure_bias)

    def do_end_measurement_based_uncomputation(self, op: 'qp.EndMeasurementBasedComputationOp'):
        pass
