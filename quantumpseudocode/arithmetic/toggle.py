import quantumpseudocode as qp
from quantumpseudocode.ops import SignatureGate


class _NotGateClass(SignatureGate):
    def emulate(self, forward: bool, lvalue: 'List[qp.Mutable[bool]]'):
        for q in lvalue:
            q.val = not q.val

    def do(self,
           controls: 'qp.QubitIntersection',
           lvalue: 'qp.Qureg'):
        raise ValueError("The NOT gate is fundamental. "
                         "It must be handled by the simulator, not decomposed.")

    def __pow__(self, power):
        if power in [1, -1]:
            return self
        return NotImplemented

    def describe(self, lvalue):
        return 'OP_TOGGLE {}'.format(lvalue)

    def __repr__(self):
        return 'qp.OP_TOGGLE'


OP_TOGGLE = _NotGateClass()
