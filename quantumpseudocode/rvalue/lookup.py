import random
from typing import Union, Iterable, Iterator

import quantumpseudocode as qp


def _flatten(x: Union[int, Iterable]) -> Iterator[int]:
    if isinstance(x, int):
        yield x
    else:
        for item in x:
            yield from _flatten(item)


class LookupTable:
    """A classical list that supports quantum addressing."""

    def __init__(self,
                 values: Union[Iterable[int], Iterable[Iterable[int]]]):
        self.values = tuple(_flatten(values))
        assert len(self.values) > 0
        assert all(e >= 0 for e in self.values)

    def output_len(self) -> int:
        return max(e.bit_length() for e in self.values)

    @staticmethod
    def random(addresses: Union[int, range, Iterable[int]],
               word_size: Union[int, range, Iterable[int]]) -> 'LookupTable':
        """Generates a LookupTable with random contents of specified lengths."""
        addresses = addresses if isinstance(addresses, int) else random.choice(addresses)
        word_size = word_size if isinstance(word_size, int) else random.choice(word_size)
        return LookupTable([
            random.randint(0, 2**word_size - 1)
            for _ in range(addresses)
        ])

    def __len__(self):
        return len(self.values)

    def __getitem__(self, item):
        if isinstance(item, bool):
            return self.values[int(item)]
        if isinstance(item, int):
            return self.values[item]
        if isinstance(item, slice):
            return LookupTable(self.values[item])
        if isinstance(item, tuple):
            if all(isinstance(e, qp.Quint) for e in item):
                reg = qp.RawQureg(q for e in item[::-1] for q in e)
                return qp.LookupRValue(self, qp.Quint(reg))
        if isinstance(item, qp.Quint):
            return qp.LookupRValue(self, item)
        if isinstance(item, qp.Qubit):
            return qp.LookupRValue(self, qp.Quint(item.qureg))
        raise NotImplementedError('Strange index: {}'.format(item))

    def __repr__(self):
        return 'qp.LookupTable({!r})'.format(self.values)
