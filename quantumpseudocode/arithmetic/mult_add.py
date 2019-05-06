from typing import Optional

import quantumpseudocode as qp
from quantumpseudocode.ops import Op


class PlusEqualProduct(Op):
    @staticmethod
    def alloc_prefix():
        return '_mult_add_'

    @staticmethod
    def biemulate(forward: bool,
                  *,
                  lvalue: 'qp.Mutable[int]',
                  quantum_factor: int,
                  const_factor: int):
        lvalue.val += quantum_factor * const_factor * (1 if forward else -1)

    @staticmethod
    def do(controls: 'qp.QubitIntersection',
           *,
           lvalue: 'qp.Quint',
           quantum_factor: 'qp.Quint',
           const_factor: int):
        for i, q in enumerate(quantum_factor):
            lvalue += (const_factor << i) & qp.controlled_by(q)

    def describe(self, lvalue, quantum_factor, const_factor):
        return '{} += {} * {}'.format(lvalue,
                                      quantum_factor,
                                      const_factor)
