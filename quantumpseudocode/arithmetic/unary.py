from typing import Iterable, Tuple, Optional

import quantumpseudocode as qp


class UnaryRValue(qp.RValue[int]):
    """Represents the temporary result of a binary-to-unary conversion."""

    def __init__(self, binary: 'qp.Quint'):
        self.binary = binary

    def __rixor__(self, other):
        other, controls = qp.ControlledLValue.split(other)
        if controls == qp.QubitIntersection.NEVER:
            return other

        if isinstance(other, qp.Quint):
            t = qp.LookupTable(1 << k for k in range(1 << len(self.binary)))
            other ^= t[self.binary] & qp.controlled_by(controls)
            return other

        return NotImplemented

    def make_storage_location(self,
                              name: Optional[str] = None) -> 'qp.Quint':
        return qp.Quint(qp.NamedQureg(name, 1 << len(self.binary)))

    def init_storage_location(self,
                              location: 'qp.Quint',
                              controls: 'qp.QubitIntersection'):
        assert len(location) >= 1 << len(self.binary)
        location[0].init(controls)
        for i, q in enumerate(self.binary):
            s = 1 << i
            for j in range(s):
                location[j + s].init(location[j] & q)
                location[j] ^= location[j + s]

    def __str__(self):
        return '1 << {}'.format(self.binary)

    def __repr__(self):
        return 'qp.UnaryRValue({!r})'.format(self.binary)
