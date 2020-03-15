import abc
import random
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


class Sink(metaclass=abc.ABCMeta):
    def __init__(self):
        self.used = False

    def do_allocate(self, args: 'qp.AllocArgs') -> 'qp.Qureg':
        result = qp.NamedQureg(args.qureg_name or '', length=args.qureg_length)
        self.did_allocate(args, result)
        return result

    @abc.abstractmethod
    def did_allocate(self, args: 'qp.AllocArgs', qureg: 'qp.Qureg'):
        pass

    @abc.abstractmethod
    def do_release(self, op: 'qp.ReleaseQuregOperation'):
        pass

    @abc.abstractmethod
    def do_phase_flip(self, controls: 'qp.QubitIntersection'):
        pass

    @abc.abstractmethod
    def do_toggle(self, targets: 'qp.Qureg', controls: 'qp.QubitIntersection'):
        pass

    @abc.abstractmethod
    def do_measure(self, qureg: 'qp.Qureg', reset: bool) -> int:
        pass

    @abc.abstractmethod
    def did_measure(self, qureg: 'qp.Qureg', reset: bool, result: int):
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
        global_sink.sinks.append(self)
        return self._val()

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert global_sink.sinks[-1] is self
        global_sink.sinks.pop()
        if exc_type is None:
            self._succeeded()


class CaptureLens(Sink):
    def __init__(self, out: List[Tuple[str, Any]], measure_bias: Optional[float]):
        super().__init__()
        self.out = out
        self.measure_bias = measure_bias

    def __enter__(self):
        super().__enter__()
        return self.out

    def did_allocate(self, args: 'qp.AllocArgs', qureg: 'qp.Qureg'):
        self.out.append(('alloc', (args, qureg)))

    def do_release(self, op: 'qp.ReleaseQuregOperation'):
        self.out.append(('release', op))

    def do_phase_flip(self, controls: 'qp.QubitIntersection'):
        self.out.append(('phase_flip', controls))

    def do_toggle(self, targets: 'qp.Qureg', controls: 'qp.QubitIntersection'):
        self.out.append(('toggle', (targets, controls)))

    def do_measure(self, qureg: 'qp.Qureg', reset: bool) -> int:
        if self.measure_bias is None:
            raise NotImplementedError()
        bits = tuple(random.random() < self.measure_bias for _ in range(len(qureg)))
        result = qp.little_endian_int(bits)
        self.did_measure(qureg, reset, result)
        return result

    def did_measure(self, qureg: 'qp.Qureg', reset: bool, result: int):
        self.out.append(('measure', (qureg, reset, result)))

    def do_start_measurement_based_uncomputation(self, op: 'qp.StartMeasurementBasedUncomputation'):
        self.out.append(('start_measurement_based_uncomputation', op))
        if self.measure_bias is not None:
            op.captured_phase_degrees = 0
            op.take_default_result(bias=self.measure_bias)

    def do_end_measurement_based_uncomputation(self, op: 'qp.EndMeasurementBasedComputationOp'):
        self.out.append(('end_measurement_based_uncomputation', op))


class _GlobalSink(Sink):
    def __init__(self):
        super().__init__()
        self.sinks: List['qp.Sink'] = []

    def do_allocate(self, args: 'qp.AllocArgs') -> 'qp.Qureg':
        result = self.sinks[0].do_allocate(args)
        for sink in self.sinks[1:]:
            sink.did_allocate(args, result)
        return result

    def did_allocate(self, args: 'qp.AllocArgs', qureg: 'qp.Qureg'):
        for sink in self.sinks:
            sink.did_allocate(args, qureg)

    def do_release(self, op: 'qp.ReleaseQuregOperation'):
        for sink in self.sinks:
            sink.do_release(op)

    def do_phase_flip(self, controls: 'qp.QubitIntersection'):
        for sink in self.sinks:
            sink.do_phase_flip(controls)

    def do_toggle(self, targets: 'qp.Qureg', controls: 'qp.QubitIntersection'):
        for sink in self.sinks:
            sink.do_toggle(targets, controls)

    def do_measure(self, qureg: 'qp.Qureg', reset: bool) -> int:
        result = self.sinks[0].do_measure(qureg, reset)
        for sink in self.sinks[1:]:
            sink.did_measure(qureg, result, result)
        return result

    def did_measure(self, qureg: 'qp.Qureg', reset: bool, result: int):
        for sink in self.sinks:
            sink.did_measure(qureg, reset, result)

    def do_start_measurement_based_uncomputation(self, op: 'qp.StartMeasurementBasedUncomputation'):
        for sink in self.sinks:
            sink.do_start_measurement_based_uncomputation(op)

    def do_end_measurement_based_uncomputation(self, op: 'qp.EndMeasurementBasedComputationOp'):
        for sink in self.sinks:
            sink.do_end_measurement_based_uncomputation(op)


global_sink = _GlobalSink()
