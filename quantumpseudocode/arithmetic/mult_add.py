from typing import Optional

import quantumpseudocode
from quantumpseudocode.ops.signature_gate import SignatureGate


class _PlusEqualTimesGateClass(SignatureGate):
    def alloc_prefix(self):
        return '_mult_add_'

    def emulate(self,
                forward: bool,
                lvalue: 'quantumpseudocode.Mutable[int]',
                quantum_factor: int,
                const_factor: int):
        lvalue.val += quantum_factor * const_factor * (1 if forward else -1)

    def do(self,
           controls: 'quantumpseudocode.QubitIntersection',
           lvalue: 'quantumpseudocode.Quint',
           quantum_factor: 'quantumpseudocode.Quint',
           const_factor: int):
        for i, q in enumerate(quantum_factor):
            lvalue += (const_factor << i) & quantumpseudocode.controlled_by(q)

    def describe(self, lvalue, quantum_factor, const_factor):
        return 'SCALE-ADD {} += {} * {}'.format(lvalue,
                                                quantum_factor,
                                                const_factor)

    def __repr__(self):
        return 'quantumpseudocode.PlusEqualTimesGate'


PlusEqualTimesGate = _PlusEqualTimesGateClass()
