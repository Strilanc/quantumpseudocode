from typing import Union, Any, Optional, Iterable

import cirq

import quantumpseudocode as qp
from .rvalue import RValue


@cirq.value_equality
class QuintIntersection(RValue[int]):
    def __init__(self,
                 *elements: Iterable[Union['qp.Quint', 'qp.QuintIntersection', int]],
                 mask: int = -1):
        flattened = []
        for element in elements:
            if isinstance(element, qp.Quint):
                flattened.append(element)
            elif isinstance(element, qp.QuintIntersection):
                mask &= element.mask
                flattened.extend(element.quints)
            elif isinstance(element, int):
                mask &= element
            else:
                raise NotImplementedError(f"Unrecognized {element!r}.")
        if not flattened:
            raise ValueError('QuintIntersection must have at least one quint.')

        self._len = min(len(e) for e in flattened)
        while self._len and mask >> (self._len - 1) == 0:
            self._len -= 1
        self.quints = tuple(e[:self._len] for e in flattened)
        self.mask = mask

    def _is_mask_vacuous(self):
        relevant_mask = ~(-1 << self._len)
        return self.mask & relevant_mask == relevant_mask

    def __and__(self, other) -> Union['qp.Quint', 'qp.QuintIntersection']:
        if isinstance(other, (int, qp.Quint, qp.QuintIntersection)):
            return qp.QuintIntersection(self, other).unwrap()
        return NotImplemented

    __rand__ = __and__

    def unwrap(self) -> Union['qp.Quint', 'qp.QuintIntersection']:
        if len(self.quints) == 1 and self._is_mask_vacuous():
            return self.quints[0]
        return self

    def _value_equality_values_(self):
        return self.quints

    def make_storage_location(self, name: Optional[str] = None) -> Any:
        return qp.alloc(self._len)

    def __getitem__(self, index: Union[int, range]) -> Union['qp.QubitIntersection', 'qp.QuintIntersection']:
        if isinstance(index, int):
            return qp.QubitIntersection(tuple(quint[index] for quint in self.quints))
        if isinstance(index, range):
            return QuintIntersection(quint[index] for quint in self.quints)
        raise NotImplementedError()

    def init_storage_location(self,
                              location: Any,
                              controls: 'qp.QubitIntersection'):
        for k in range(self._len):
            if self.mask & (1 << k):
                self[k].init_storage_location(location[k], controls)

    def del_storage_location(self,
                             location: Any,
                             controls: 'qp.QubitIntersection'):
        for k in range(self._len):
            self[k].del_storage_location(location[k], controls=controls)

    def __rixor__(self, other):
        other, controls = qp.ControlledLValue.split(other)

        if isinstance(other, qp.Quint):
            if len(other) < self._len:
                raise ValueError("Right hand sde is quantum and longer than destination.")
            for k in range(self._len):
                other[k] ^= self[k] & qp.controlled_by(controls)
            return other

        return NotImplemented

    def __str__(self):
        elements = list(self.quints)
        if not self._is_mask_vacuous():
            elements.append(self.mask)
        return ' & '.join(str(e) for e in elements)

    def __repr__(self):
        return f'qp.QuintIntersection({self.quints!r}, mask={self.mask!r})'
