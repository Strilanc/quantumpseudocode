import abc
from typing import Optional, Any, Union, Generic, TypeVar, List, Tuple, Iterable, overload

import quantumpseudocode as qp


T = TypeVar('T')


class RValue(Generic[T], metaclass=abc.ABCMeta):
    """A value or expression that only needs to exist temporarily."""

    def _rval_(self):
        return self

    def trivial_unwrap(self):
        return self

    def existing_storage_location(self) -> Any:
        return None

    @abc.abstractmethod
    def make_storage_location(self, name: Optional[str] = None) -> Any:
        raise NotImplementedError()

    def phase_flip_if(self, controls: 'qp.QubitIntersection'):
        with qp.hold(self, controls=controls) as loc:
            qp.phase_flip(loc)

    @abc.abstractmethod
    def init_storage_location(self,
                              location: Any,
                              controls: 'qp.QubitIntersection'):
        raise NotImplementedError()

    @abc.abstractmethod
    def del_storage_location(self,
                             location: Any,
                             controls: 'qp.QubitIntersection'):
        raise NotImplementedError()


@overload
def rval(val: 'qp.LValue[T]') -> 'qp.RValue[T]':
    pass
@overload
def rval(val: 'qp.RValue[T]') -> 'qp.RValue[T]':
    pass
@overload
def rval(val: 'int') -> 'qp.RValue[int]':
    pass
@overload
def rval(val: 'bool') -> 'qp.RValue[bool]':
    pass
@overload
def rval(val: Any, default: Any) -> 'qp.RValue[T]':
    pass


_raise_on_fail=([],)


def rval(val: Any, default: Any = _raise_on_fail) -> 'qp.RValue[Any]':
    """Wraps the given candidate value into a `qp.RValue`, if needed.

    Args:
         val: The value that the caller wants as an rvalue.
         default: Alternative result used when there is no associated rvalue.
            If not specified, an error is raised when no associated rvalue
            exists.

    Returns:
        A `qp.RValue` wrapper around the given candidate value.
    """
    func = getattr(val, '_rval_', None)
    if func is not None:
        return func()

    if isinstance(val, bool):
        return qp.BoolRValue(val)
    if isinstance(val, int):
        return qp.IntRValue(val)
    if default is not _raise_on_fail:
        return default
    raise NotImplementedError(
        "Don't know how to wrap type {} (value {!r}).".format(
            type(val),
            val))
