from typing import Optional

import quantumpseudocode as qp
from quantumpseudocode.ops import SignatureGate


class _PlusEqualTimesGateClass(SignatureGate):
    def alloc_prefix(self):
        return '_mult_add_'

    def emulate(self,
                forward: bool,
                lvalue: 'qp.Mutable[int]',
                quantum_factor: int,
                const_factor: int):
        lvalue.val += quantum_factor * const_factor * (1 if forward else -1)

    def do(self,
           controls: 'qp.QubitIntersection',
           lvalue: 'qp.Quint',
           quantum_factor: 'qp.Quint',
           const_factor: int):
        for i, q in enumerate(quantum_factor):
            lvalue += (const_factor << i) & qp.controlled_by(q)

    def describe(self, lvalue, quantum_factor, const_factor):
        return 'SCALE-ADD {} += {} * {}'.format(lvalue,
                                                quantum_factor,
                                                const_factor)

    def __repr__(self):
        return 'qp.PlusEqualTimesGate'


PlusEqualTimesGate = _PlusEqualTimesGateClass()
