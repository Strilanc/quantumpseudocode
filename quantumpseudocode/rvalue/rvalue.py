from typing import Optional, Any, Generic, TypeVar, overload

import quantumpseudocode as qp

T = TypeVar('T')


class RValue(Generic[T]):
    """A value or expression that only needs to exist temporarily."""

    def trivial_unwrap(self):
        """Returns the value wrapped by this RValue, if it already exists.

        For example, an rvalue wrapping a classical integer will unwrap into that integers.
        Similarly, an rvalue wrapping a quantum integer register unwrap into that quantum integer.
        But an expression rvalue, such as a comparison, will unwrap to itself.
        """
        return self

    def existing_storage_location(self) -> Any:
        """If the rvalue references a storage location, returns that location. Otherwise returns None."""
        return None

    def make_storage_location(self, name: Optional[str] = None) -> Any:
        """Creates a new storage location that the rvalue can be stored in."""
        raise NotImplementedError()

    def init_storage_location(self,
                              location: Any,
                              controls: 'qp.QubitIntersection'):
        """Initializes a zero'd storage location so that it contains the rvalue."""
        raise NotImplementedError(f'{type(self)}.init_storage_location')

    def clear_storage_location(self,
                               location: Any,
                               controls: 'qp.QubitIntersection'):
        """Zeroes a storage location that currently contains the rvalue."""
        raise NotImplementedError(f'{type(self)}.del_storage_Location')


_raise_on_fail = object()


@overload
def rval(val: 'qp.Qubit') -> 'qp.RValue[bool]':
    pass


@overload
def rval(val: 'qp.Quint') -> 'qp.RValue[int]':
    pass


@overload
def rval(val: 'int') -> 'qp.RValue[int]':
    pass


@overload
def rval(val: 'bool') -> 'qp.RValue[bool]':
    pass


@overload
def rval(val: 'qp.RValue[T]') -> 'qp.RValue[T]':
    pass


@overload
def rval(val: Any, default: Any) -> 'qp.RValue[Any]':
    pass


def rval(val: Any, default: Any = _raise_on_fail) -> 'qp.RValue[Any]':
    """Wraps the given candidate value into a `qp.RValue`, if needed.

    Args:
         val: The value that the caller wants as an rvalue.
         default: Default result to return for an unrecognized type of value. Defaults to raising an exception.

    Returns:
        A `qp.RValue` wrapper around the given candidate value.
    """
    if isinstance(val, bool):
        return qp.BoolRValue(val)
    if isinstance(val, int):
        return qp.IntRValue(val)
    if isinstance(val, qp.IntBuf):
        return qp.IntRValue(int(val))
    if isinstance(val, qp.Qubit):
        return qp.QubitRValue(val)
    if isinstance(val, qp.Quint):
        return qp.QuintRValue(val)
    if isinstance(val, qp.RValue):
        return val
    if default is not _raise_on_fail:
        return default
    raise NotImplementedError(
        "Don't know how to wrap type {} (value {!r}).".format(
            type(val),
            val))
