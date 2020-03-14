from typing import List, Optional, ContextManager, cast

import quantumpseudocode as qp

lens_stack: List['qp.Logger'] = []


def emit(operation: 'qp.Operation', controls: 'qp.QubitIntersection'):
    op, cnt = qp.ControlledOperation.split(operation)
    cnt = cnt & controls
    for logger in lens_stack:
        logger.log(op, cnt)


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


class Logger:
    def __init__(self):
        self.used = False

    def log(self, op: 'qp.Operation', cnt: 'qp.QubitIntersection'):
        raise NotImplementedError()

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
    def __init__(self, out: 'List[qp.Operation]', measure_bias: Optional[float]):
        super().__init__()
        self.out = out
        self.measure_bias = measure_bias

    def __enter__(self):
        super().__enter__()
        return self.out

    def log(self, op: 'qp.Operation', cnt: 'qp.QubitIntersection'):
        if cnt != qp.QubitIntersection.ALWAYS:
            operation = op.controlled_by(cnt)
        else:
            operation = op
        if self.measure_bias is not None and isinstance(operation, qp.MeasureOperation):
            operation.take_default_result(bias=self.measure_bias)
        if self.measure_bias is not None and isinstance(operation, qp.StartMeasurementBasedUncomputation):
            operation.captured_phase_degrees = 0
            operation.take_default_result(bias=self.measure_bias)
        self.out.append(operation)
