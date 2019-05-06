from typing import Optional, Dict, Set

import cirq


@cirq.value_equality
class UniqueHandle:
    _next_handle = {}  # type: Dict[Optional[str], int]
    _free_handles = {}  # type: Dict[Optional[str], Set[int]]

    def __init__(self, key: str = '', n: Optional[int] = None):
        self.key = None
        assert isinstance(key, str)
        if n is None:
            free = UniqueHandle._free_handles.get(key, None)
            if free:
                self.n = min(free)
                free.remove(self.n)
            else:
                self.n = UniqueHandle._next_handle.get(key, 0)
                UniqueHandle._next_handle[key] = self.n + 1
        else:
            self.n = n
        self.key = key

    def _value_equality_values_(self):
        return self.key, self.n

    def __del__(self):
        if self.key is not None:
            if self.key not in UniqueHandle._free_handles:
                UniqueHandle._free_handles[self.key] = set()
            UniqueHandle._free_handles[self.key].add(self.n)
            self.key = None

    def __str__(self):
        if self.n == 0 and self.key:
            return self.key
        return '{}_{}'.format(self.key, self.n)

    def __repr__(self):
        return 'qp.UniqueHandle({!r}, {!r})'.format(self.key, self.n)
