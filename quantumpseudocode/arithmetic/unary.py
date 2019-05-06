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
        qp.emit(qp.LetAnd(lvalue[0]).controlled_by(controls))
        for i, q in enumerate(binary):
            s = 1 << i
            for j in range(s):
                a = lvalue[j]
                b = lvalue[j + s]
                qp.emit(qp.LetAnd(b).controlled_by(a & q))
                a ^= b

    def describe(self, lvalue, binary):
        return '{} := unary({})'.format(lvalue, binary)

    def __repr__(self):
        return 'qp.LetUnaryGate'


LetUnary = _LetUnaryGate()
