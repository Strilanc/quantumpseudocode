from typing import List, Optional, Union, Tuple, Callable, TYPE_CHECKING, Iterable

import quantumpseudocode


lens_stack = []

emit_indent = 0
def emit(operation: 'quantumpseudocode.Operation'):
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
        op.do(quantumpseudocode.QubitIntersection.EMPTY)
    emit_indent -= 1


def capture(out: 'Optional[List[quantumpseudocode.Operation]]' = None):
    return CaptureLens([] if out is None else out)


class EmptyManager:
    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

def condition(control: Union['quantumpseudocode.Qubit', 'quantumpseudocode.QubitIntersection']):
    if isinstance(control, quantumpseudocode.Qubit):
        control = quantumpseudocode.QubitIntersection((control,))
    elif len(control) == 0:
        return EmptyManager()
    return _ControlLens(control)


def invert():
    return _InvertLens()


class Lens:
    def __init__(self):
        self.used = False

    def modify(self, operation: 'quantumpseudocode.Operation'
               ) -> Iterable['quantumpseudocode.Operation']:
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
    def __init__(self, out: 'List[quantumpseudocode.Operation]'):
        super().__init__()
        self.out = out

    def __enter__(self):
        super().__enter__()
        return self.out

    def modify(self, operation):
        self.out.append(operation)
        return []


class _ControlLens(CaptureLens):
    def __init__(self, controls: 'quantumpseudocode.QubitIntersection'):
        super().__init__([])
        self.controls = controls

    def _succeeded(self):
        for op in self.out:
            emit(op.controlled_by(self.controls))


class _InvertLens(CaptureLens):
    def __init__(self):
        super().__init__([])

    def _succeeded(self):
        for op in reversed(self.out):
            emit(op.inverse())


class Log(Lens):
    def __init__(self, max_indent: Optional[int] = None):
        super().__init__()
        self.max_indent = max_indent

    def modify(self, operation: 'quantumpseudocode.Operation'):
        if self.max_indent is None or self.max_indent >= emit_indent - 1:
            print(' ' * (emit_indent * 4 - 4) + str(operation))
        return [operation]