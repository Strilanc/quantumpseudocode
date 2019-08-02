from typing import Optional, Any, Union, Generic, TypeVar, List, Tuple, Iterable, overload

import quantumpseudocode as qp


T = TypeVar('T')


class LValue(Generic[T]):
    """A value or expression that can be mutated and written to."""

    def _rval_(self) -> 'qp.RValue[T]':
        raise NotImplementedError()
