from typing import List, Optional, Union, Tuple, Callable, TYPE_CHECKING, Iterable, ContextManager, cast

import quantumpseudocode as qp


_current_lens: 'qp.Lens' = None


def emit(operation: 'qp.Operation'):
    _current_lens.modify(operation)


def capture(out: 'Optional[List[qp.Operation]]' = None) -> ContextManager[List['qp.Operation']]:
    return cast(ContextManager, CaptureLens([] if out is None else out))


class EmptyManager:
    def __init__(self, value=None):
        self.value = value

    def __enter__(self):
        return self.value

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class Lens:
    def __init__(self):
        self.used = False
        self._prev_simulator = None

    def modify(self, operation: 'qp.Operation'
               ) -> Iterable['qp.Operation']:
        raise NotImplementedError()

    def __enter__(self):
        global _current_lens
        assert not self.used
        self.used = True
        self._prev_simulator = _current_lens
        _current_lens = self

    def __exit__(self, exc_type, exc_val, exc_tb):
        global _current_lens
        assert _current_lens is self
        _current_lens = self._prev_simulator
        self._prev_simulator = None


class CaptureLens(Lens):
    def __init__(self, out: 'List[qp.Operation]'):
        super().__init__()
        self.out = out

    def __enter__(self):
        super().__enter__()
        return self.out

    def modify(self, operation):
        self.out.append(operation)
        if self._prev_simulator is not None:
            self._prev_simulator.modify(operation)
