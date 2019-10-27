import abc
from typing import List, Optional, ContextManager, cast, Union, Iterable

import quantumpseudocode as qp

_current_operating_context: 'qp.OperatingContext' = None


def do_atom(operation: 'qp.Operation'):
    _current_operating_context.do(operation)


def capture(*, out: Optional[List['qp.Operation']] = None) -> ContextManager[List['qp.Operation']]:
    return cast(ContextManager, CaptureContext(out=out))


class EmptyManager:
    def __init__(self, value=None):
        self.value = value

    def __enter__(self):
        return self.value

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class OperatingContext(metaclass=abc.ABCMeta):
    def __init__(self):
        self.used = False
        self._outer_context = None

    @abc.abstractmethod
    def do(self, operation: 'qp.Operation'):
        """Perform the given operation using this context."""

    def __enter__(self):
        global _current_operating_context
        assert not self.used
        self.used = True
        self._outer_context = _current_operating_context
        _current_operating_context = self

    def __exit__(self, exc_type, exc_val, exc_tb):
        global _current_operating_context
        assert _current_operating_context is self
        _current_operating_context = self._outer_context
        self._outer_context = None


class CaptureContext(OperatingContext):
    def __init__(self, *, out: Optional[List['qp.Operation']] = None):
        super().__init__()
        self.out = out if out is not None else []

    def __enter__(self):
        super().__enter__()
        return self.out

    def do(self, operation):
        self.out.append(operation)
        if self._outer_context is not None:
            self._outer_context.do(operation)
