from typing import List, Optional, Union, Tuple, Callable, TYPE_CHECKING, Iterable, ContextManager, cast

import quantumpseudocode as qp


lens_stack = []


def emit(operation: 'qp.Operation'):
    for logger in lens_stack:
        logger.log(operation)


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

    def log(self, operation: 'qp.Operation'):
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

    def log(self, operation):
        if self.measure_bias is not None and isinstance(operation, qp.MeasureOperation):
            operation.take_default_result(bias=self.measure_bias)
        if self.measure_bias is not None and isinstance(operation, qp.StartMeasurementBasedUncomputation):
            operation.captured_phase_degrees = 0
            operation.take_default_result(bias=self.measure_bias)
        self.out.append(operation)


class _ControlLens(CaptureLens):
    def __init__(self, controls: 'qp.QubitIntersection'):
        super().__init__([])
        self.controls = controls

    def __enter__(self):
        super().__enter__()
        return None

    def _succeeded(self):
        if self.controls.bit:
            for op in self.out:
                emit(op.controlled_by(self.controls))


class Log(Logger):
    def __init__(self, max_indent: Optional[int] = None):
        super().__init__()
        self.max_indent = max_indent

    def log(self, operation: 'qp.Operation'):
        if self.max_indent is None or self.max_indent >= emit_indent - 1:
            print(' ' * (emit_indent * 4 - 4) + str(operation))
