from typing import List, Optional, Union, Tuple, Callable, TYPE_CHECKING, Iterable, ContextManager, cast

import quantumpseudocode as qp


lens_stack = []

emit_indent = 0
def emit(operation: 'qp.Operation'):
    global emit_indent
    emit_indent += 1

    state = [operation]

    for lens in reversed(lens_stack):
        if not state:
            break
        next_state = []
        for op in state:
            next_state.extend(lens.modify(op))
        state = next_state

    for op in state:
        op.emit_ops(qp.QubitIntersection.ALWAYS)
    emit_indent -= 1


def capture(out: 'Optional[List[qp.Operation]]' = None) -> ContextManager[List['qp.Operation']]:
    return cast(ContextManager, CaptureLens([] if out is None else out))


class EmptyManager:
    def __init__(self, value=None):
        self.value = value

    def __enter__(self):
        return self.value

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def condition(control: Union['qp.Qubit', 'qp.QubitIntersection']) -> ContextManager[None]:
    if isinstance(control, qp.Qubit):
        control = qp.QubitIntersection((control,))
    elif control == qp.QubitIntersection.ALWAYS:
        return EmptyManager()
    return cast(ContextManager[None], _ControlLens(control))


def invert() -> ContextManager[None]:
    return cast(ContextManager[None], _InvertLens())


class Lens:
    def __init__(self):
        self.used = False

    def modify(self, operation: 'qp.Operation'
               ) -> Iterable['qp.Operation']:
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


class CaptureLens(Lens):
    def __init__(self, out: 'List[qp.Operation]'):
        super().__init__()
        self.out = out

    def __enter__(self):
        super().__enter__()
        return self.out

    def modify(self, operation):
        self.out.append(operation)
        return []


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


class _InvertLens(CaptureLens):
    def __init__(self):
        super().__init__([])

    def __enter__(self):
        super().__enter__()
        return None

    def _succeeded(self):
        for op in reversed(self.out):
            emit(op.inverse())


class Log(Lens):
    def __init__(self, max_indent: Optional[int] = None):
        super().__init__()
        self.max_indent = max_indent

    def modify(self, operation: 'qp.Operation'):
        if self.max_indent is None or self.max_indent >= emit_indent - 1:
            print(' ' * (emit_indent * 4 - 4) + str(operation))
        return [operation]
