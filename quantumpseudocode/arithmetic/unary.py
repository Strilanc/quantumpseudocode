import quantumpseudocode as qp
from quantumpseudocode.ops.signature_gate import SignatureGate


class _LetUnaryGate(SignatureGate):
    def alloc_prefix(self):
        return '_let_unary_'

    def emulate(self,
                forward: bool,
                *,
                lvalue: 'qp.Mutable[int]',
                binary: int):
        if forward:
            assert lvalue.val == 0
            lvalue.val = 1 << binary
        else:
            assert lvalue.val == 1 << binary
            lvalue.val = 0

    def do(self,
           controls: 'qp.QubitIntersection',
           *,
           lvalue: qp.Quint,
           binary: qp.Quint):
        assert len(lvalue) >= 1 << len(binary)
        lvalue[0].init(controls)
        for i, q in enumerate(binary):
            s = 1 << i
            for j in range(s):
                lvalue[j + s].init(lvalue[j] & q)
                lvalue[j] ^= lvalue[j + s]

    def describe(self, lvalue, binary):
        return '{} := unary({})'.format(lvalue, binary)

    def __repr__(self):
        return 'qp.LetUnaryGate'


LetUnary = _LetUnaryGate()
