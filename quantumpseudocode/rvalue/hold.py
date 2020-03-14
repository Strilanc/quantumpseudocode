from typing import Optional, Any, Union, Generic, TypeVar, List, Tuple, Iterable, overload

import quantumpseudocode as qp


T = TypeVar('T')


@overload
def hold(val: 'qp.Qubit',
         name: Optional[str] = None,
         controls: 'Optional[qp.QubitIntersection]' = None) -> 'qp.HeldRValueManager[bool]':
    pass
@overload
def hold(val: 'qp.Quint',
         name: Optional[str] = None,
         controls: 'Optional[qp.QubitIntersection]' = None) -> 'qp.HeldRValueManager[int]':
    pass
@overload
def hold(val: 'int',
         name: Optional[str] = None,
         controls: 'Optional[qp.QubitIntersection]' = None) -> 'qp.HeldRValueManager[int]':
    pass
@overload
def hold(val: 'bool',
         name: Optional[str] = None,
         controls: 'Optional[qp.QubitIntersection]' = None) -> 'qp.HeldRValueManager[bool]':
    pass
@overload
def hold(val: 'qp.RValue[T]',
         name: Optional[str] = None,
         controls: 'Optional[qp.QubitIntersection]' = None) -> 'qp.HeldRValueManager[T]':
    pass


def hold(val: Union[T, 'qp.RValue[T]', 'qp.Qubit', 'qp.Quint'],
         *,
         name: str = '',
         controls: 'Optional[qp.QubitIntersection]' = None
         ) -> 'qp.HeldRValueManager[T]':
    """Returns a context manager that ensures the given rvalue is allocated.

    Usage:
        ```
        with qp.hold(5) as reg:
            # reg is an allocated quint storing the value 5
            ...
        ```

    Args:
        val: The value to hold.
        name: Optional name to use when allocating space for the value.
        controls: If any of these are not set, the result is a default value
            (e.g. False or 0) instead of the rvalue.

    Returns:
        A qp.HeldRValueManager wrapping the given value.
    """
    return qp.HeldRValueManager(
        qp.rval(val),
        controls=qp.QubitIntersection.ALWAYS if controls is None else controls,
        name=name)


class HeldRValueManager(Generic[T]):
    def __init__(self, rvalue: 'qp.RValue[T]',
                 *,
                 controls: 'qp.QubitIntersection' = None,
                 name: str = ''):
        assert isinstance(name, str)
        self.name = name
        self.rvalue = rvalue
        self.controls = controls if controls is not None else qp.QubitIntersection.ALWAYS
        self.location = None  # type: Optional[Any]
        self.qalloc = None  # type: Optional[Any]

    def __repr__(self):
        return 'qp.HeldRValueManager({!r}, {!r})'.format(
            self.rvalue, self.name)

    def __enter__(self):
        assert self.location is None
        self.location = self.rvalue.existing_storage_location()
        if self.location is None:
            self.location = self.rvalue.make_storage_location(self.name)
            self.qalloc = qp.qmanaged(self.location)
            self.qalloc.__enter__()
            self.rvalue.init_storage_location(self.location, self.controls)
        return self.location

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.qalloc is not None and exc_type is None:
            self.rvalue.del_storage_location(self.location, self.controls)
            self.qalloc.__exit__(exc_type, exc_val, exc_tb)
