from typing import Optional, Any, Union, Generic, TypeVar, List, Tuple, Iterable, overload

import quantumpseudocode


T = TypeVar('T')


@overload
def hold(val: 'quantumpseudocode.Qubit',
         name: Optional[str] = None,
         controls: 'Optional[quantumpseudocode.QubitIntersection]' = None) -> 'quantumpseudocode.HeldRValueManager[bool]':
    pass
@overload
def hold(val: 'quantumpseudocode.Quint',
         name: Optional[str] = None,
         controls: 'Optional[quantumpseudocode.QubitIntersection]' = None) -> 'quantumpseudocode.HeldRValueManager[int]':
    pass
@overload
def hold(val: 'int',
         name: Optional[str] = None,
         controls: 'Optional[quantumpseudocode.QubitIntersection]' = None) -> 'quantumpseudocode.HeldRValueManager[int]':
    pass
@overload
def hold(val: 'bool',
         name: Optional[str] = None,
         controls: 'Optional[quantumpseudocode.QubitIntersection]' = None) -> 'quantumpseudocode.HeldRValueManager[bool]':
    pass
@overload
def hold(val: 'quantumpseudocode.RValue[T]',
         name: Optional[str] = None,
         controls: 'Optional[quantumpseudocode.QubitIntersection]' = None) -> 'quantumpseudocode.HeldRValueManager[T]':
    pass


def hold(val: Union[T, 'quantumpseudocode.RValue[T]', 'quantumpseudocode.Qubit', 'quantumpseudocode.Quint'],
         *,
         name: str = '',
         controls: 'Optional[quantumpseudocode.QubitIntersection]' = None
         ) -> 'quantumpseudocode.HeldRValueManager[T]':
    """Returns a context manager that ensures the given rvalue is allocated.

    Usage:
        ```
        with quantumpseudocode.hold(5) as reg:
            # reg is an allocated quint storing the value 5
            ...
        ```

    Args:
        val: The value to hold.
        name: Optional name to use when allocating space for the value.
        controls: If any of these are not set, the result is a default value
            (e.g. False or 0) instead of the rvalue.

    Returns:
        A quantumpseudocode.HeldRValueManager wrapping the given value.
    """
    return quantumpseudocode.HeldRValueManager(
        quantumpseudocode.rval(val),
        controls=controls or quantumpseudocode.QubitIntersection.EMPTY,
        name=name)


class HeldRValueManager(Generic[T]):
    def __init__(self, rvalue: 'quantumpseudocode.RValue[T]',
                 *,
                 controls: 'quantumpseudocode.QubitIntersection',
                 name: str = ''):
        assert isinstance(name, str)
        self.name = name
        self.rvalue = rvalue
        self.controls = controls
        self.location = None  # type: Optional[Any]
        self.qalloc = None  # type: Optional[Any]

    def __repr__(self):
        return 'quantumpseudocode.HeldRValueManager({!r}, {!r})'.format(
            self.rvalue, self.name)

    def __enter__(self):
        assert self.location is None
        self.location = self.rvalue.existing_storage_location()
        if self.location is None:
            self.location = self.rvalue.make_storage_location(self.name)
            self.qalloc = quantumpseudocode.qmanaged(self.location)
            self.qalloc.__enter__()
            quantumpseudocode.emit(quantumpseudocode.LetRValueOperation(
                self.rvalue, self.location).controlled_by(self.controls))
        return self.location

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.qalloc is not None and exc_type is None:
            quantumpseudocode.emit(quantumpseudocode.DelRValueOperation(
                self.rvalue, self.location).controlled_by(self.controls))
            self.qalloc.__exit__(exc_type, exc_val, exc_tb)
