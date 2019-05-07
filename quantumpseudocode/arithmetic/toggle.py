from typing import List

import quantumpseudocode as qp
from quantumpseudocode.ops import Op


class Toggle(Op):
    def emulate(self, lvalue: List['qp.Mutable[bool]']):
        for q in lvalue:
            q.val = not q.val

    def do(self,
           controls: 'qp.QubitIntersection',
           lvalue: 'qp.Qureg'):
        raise ValueError("The NOT gate is fundamental. "
                         "It must be handled by the simulator, not decomposed.")

    def inverse(self):
        return self

    def describe(self, lvalue):
        assert not isinstance(lvalue, qp.Qubit)
        return 'Toggle {}'.format(lvalue)
