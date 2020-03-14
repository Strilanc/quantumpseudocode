from typing import Optional, Any, Union, Generic, TypeVar, List, Tuple, Iterable, overload

import quantumpseudocode as qp


T = TypeVar('T')


class RValue(Generic[T]):
    """A value or expression that only needs to exist temporarily."""

    def trivial_unwrap(self):
        return self

    def qureg_deps(self) -> Iterable['qp.Qureg']:
        raise NotImplementedError()

    def value_from_resolved_deps(self, args: Tuple[int, ...]) -> T:
        raise NotImplementedError()

    def existing_storage_location(self) -> Any:
        return None

    def make_storage_location(self, name: Optional[str] = None) -> Any:
        raise NotImplementedError()

    def phase_flip_if(self, controls: 'qp.QubitIntersection'):
        with qp.hold(self, controls=controls) as loc:
            qp.phase_flip(loc)

    def init_storage_location(self,
                              location: Any,
                              controls: 'qp.QubitIntersection'):
        raise NotImplementedError(f'{type(self)}.init_storage_location')

    def del_storage_location(self,
                             location: Any,
                             controls: 'qp.QubitIntersection'):
        raise NotImplementedError(f'{type(self)}.del_storage_Location')


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
def rval(val: Any, default: Any) -> 'qp.RValue[T]':
    pass


_raise_on_fail=([],)


def rval(val: Any, default: Any = _raise_on_fail) -> 'qp.RValue[Any]':
    """Wraps the given candidate value into a `qp.RValue`, if needed.

    Args:
         val: The value that the caller wants as an rvalue.

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
