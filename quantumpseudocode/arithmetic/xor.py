import quantumpseudocode
from quantumpseudocode.ops.signature_gate import SignatureGate


class _XorConstGateClass(SignatureGate):
    def emulate(self, forward: bool, lvalue: 'quantumpseudocode.Mutable[int]', mask: int):
        lvalue.val ^= mask

    def do(self,
           controls: 'quantumpseudocode.QubitIntersection',
           lvalue: 'quantumpseudocode.Quint',
           mask: int):
        targets = []
        for i, q in enumerate(lvalue):
            if mask & (1 << i):
                targets.append(q)
        quantumpseudocode.emit(quantumpseudocode.OP_TOGGLE(quantumpseudocode.RawQureg(targets)).controlled_by(controls))

    def describe(self, lvalue, mask):
        return 'OP_XOR_C {} ^= {}'.format(lvalue, mask)

    def __repr__(self):
        return 'quantumpseudocode.OP_XOR_C'


class _XorRegisterGateClass(SignatureGate):
    def emulate(self, forward: bool, lvalue: 'quantumpseudocode.Mutable[int]', mask: int):
        lvalue.val ^= mask

    def do(self,
           controls: 'quantumpseudocode.QubitIntersection',
           lvalue: 'quantumpseudocode.Quint',
           mask: 'quantumpseudocode.Quint'):
        for i, q in enumerate(lvalue):
            quantumpseudocode.emit(quantumpseudocode.OP_TOGGLE(quantumpseudocode.RawQureg([q])).controlled_by(controls & mask[i]))

    def describe(self, lvalue, mask):
        return 'OP_XOR {} ^= {}'.format(lvalue, mask)

    def __repr__(self):
        return 'quantumpseudocode.OP_XOR'


OP_XOR_C = _XorConstGateClass()
OP_XOR = _XorRegisterGateClass()
