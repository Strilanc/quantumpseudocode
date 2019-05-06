from typing import Optional, Any, Union, Generic, TypeVar, List, Tuple, Iterable, overload

import quantumpseudocode


T = TypeVar('T')


class RValue(Generic[T]):
    """A value or expression that only needs to exist temporarily."""

    def permutation_registers(self) -> Iterable['quantumpseudocode.Qureg']:
        raise NotImplementedError()

    def value_from_permutation_registers(self, args: Tuple[int, ...]) -> T:
        raise NotImplementedError()

    def permutation_registers_from_value(self, val: T) -> Tuple[int, ...]:
        raise NotImplementedError()

    def existing_storage_location(self) -> Any:
        return None

    def make_storage_location(self, name: Optional[str] = None) -> Any:
        raise NotImplementedError()

    def phase_flip_if(self, controls: 'quantumpseudocode.QubitIntersection'):
        with quantumpseudocode.hold(self, controls=controls) as loc:
            quantumpseudocode.phase_flip(loc)

    def init_storage_location(self,
                              location: Any,
                              controls: 'quantumpseudocode.QubitIntersection'):
        raise NotImplementedError()

    def del_storage_location(self,
                             location: Any,
                             controls: 'quantumpseudocode.QubitIntersection'):
        with quantumpseudocode.invert():
            self.init_storage_location(location, controls)


@overload
def rval(val: 'quantumpseudocode.Qubit') -> 'quantumpseudocode.RValue[bool]':
    pass
@overload
def rval(val: 'quantumpseudocode.Quint') -> 'quantumpseudocode.RValue[int]':
    pass
@overload
def rval(val: 'int') -> 'quantumpseudocode.RValue[int]':
    pass
@overload
def rval(val: 'bool') -> 'quantumpseudocode.RValue[bool]':
    pass
@overload
def rval(val: 'quantumpseudocode.RValue[T]') -> 'quantumpseudocode.RValue[T]':
    pass
def rval(val: Any) -> 'quantumpseudocode.RValue[Any]':
    """Wraps the given candidate value into a `quantumpseudocode.RValue`, if needed.

    Args:
         val: The value that the caller wants as an rvalue.

    Returns:
        A `quantumpseudocode.RValue` wrapper around the given candidate value.
    """
    if isinstance(val, bool):
        return quantumpseudocode.BoolRValue(val)
    if isinstance(val, int):
        return quantumpseudocode.IntRValue(val)
    if isinstance(val, quantumpseudocode.Qubit):
        return quantumpseudocode.QubitRValue(val)
    if isinstance(val, quantumpseudocode.Quint):
        return quantumpseudocode.QuintRValue(val)
    if isinstance(val, quantumpseudocode.RValue):
        return val
    raise NotImplementedError(
        "Don't know how to wrap type {} (value {!r}).".format(
            type(val),
            val))
