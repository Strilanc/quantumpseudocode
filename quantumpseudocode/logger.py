import abc
from typing import List, Optional, ContextManager, cast, Tuple, Union, Any

import quantumpseudocode as qp


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

    def do_allocate_qureg(self, args: 'qp.AllocArgs') -> 'qp.Qureg':
        result = qp.NamedQureg(args.qureg_name or '', length=args.qureg_length)
        self.did_allocate_qureg(args, result)
        return result

    @abc.abstractmethod
    def did_allocate_qureg(self, args: 'qp.AllocArgs', qureg: 'qp.Qureg'):
        pass

    @abc.abstractmethod
    def do_release_qureg(self, op: 'qp.ReleaseQuregOperation'):
        pass

    @abc.abstractmethod
    def do_phase_flip(self, controls: 'qp.QubitIntersection'):
        pass

    @abc.abstractmethod
    def do_toggle_qureg(self, targets: 'qp.Qureg', controls: 'qp.QubitIntersection'):
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
        global_logger.loggers.append(self)
        return self._val()

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert global_logger.loggers[-1] is self
        global_logger.loggers.pop()
        if exc_type is None:
            self._succeeded()


class CaptureLens(Logger):
    def __init__(self, out: List[Tuple[str, Any]], measure_bias: Optional[float]):
        super().__init__()
        self.out = out
        self.measure_bias = measure_bias

    def __enter__(self):
        super().__enter__()
        return self.out

    def did_allocate_qureg(self, args: 'qp.AllocArgs', qureg: 'qp.Qureg'):
        self.out.append(('alloc', (args, qureg)))

    def do_release_qureg(self, op: 'qp.ReleaseQuregOperation'):
        self.out.append(('release', op))

    def do_phase_flip(self, controls: 'qp.QubitIntersection'):
        self.out.append(('phase_flip', controls))

    def do_toggle_qureg(self, targets: 'qp.Qureg', controls: 'qp.QubitIntersection'):
        self.out.append(('toggle', (targets, controls)))

    def do_measure_qureg(self, op: 'qp.MeasureOperation'):
        self.out.append(('measure', op))
        if self.measure_bias is not None:
            op.take_default_result(bias=self.measure_bias)

    def do_start_measurement_based_uncomputation(self, op: 'qp.StartMeasurementBasedUncomputation'):
        self.out.append(('start_measurement_based_uncomputation', op))
        if self.measure_bias is not None:
            op.captured_phase_degrees = 0
            op.take_default_result(bias=self.measure_bias)

    def do_end_measurement_based_uncomputation(self, op: 'qp.EndMeasurementBasedComputationOp'):
        self.out.append(('end_measurement_based_uncomputation', op))


class _GlobalLogger(Logger):
    def __init__(self):
        super().__init__()
        self.sim: Optional['qp.Logger'] = None
        self.loggers: List['qp.Logger'] = []

    def do_allocate_qureg(self, args: 'qp.AllocArgs') -> 'qp.Qureg':
        result = self.loggers[0].do_allocate_qureg(args)
        for logger in self.loggers[1:]:
            logger.did_allocate_qureg(args, result)
        return result

    def did_allocate_qureg(self, args: 'qp.AllocArgs', qureg: 'qp.Qureg'):
        for logger in self.loggers:
            logger.did_allocate_qureg(args, qureg)

    def do_release_qureg(self, op: 'qp.ReleaseQuregOperation'):
        for logger in self.loggers:
            logger.do_release_qureg(op)

    def do_phase_flip(self, controls: 'qp.QubitIntersection'):
        for logger in self.loggers:
            logger.do_phase_flip(controls)

    def do_toggle_qureg(self, targets: 'qp.Qureg', controls: 'qp.QubitIntersection'):
        for logger in self.loggers:
            logger.do_toggle_qureg(targets, controls)

    def do_measure_qureg(self, op: 'qp.MeasureOperation'):
        for logger in self.loggers:
            logger.do_measure_qureg(op)

    def do_start_measurement_based_uncomputation(self, op: 'qp.StartMeasurementBasedUncomputation'):
        for logger in self.loggers:
            logger.do_start_measurement_based_uncomputation(op)

    def do_end_measurement_based_uncomputation(self, op: 'qp.EndMeasurementBasedComputationOp'):
        for logger in self.loggers:
            logger.do_end_measurement_based_uncomputation(op)


global_logger = _GlobalLogger()
