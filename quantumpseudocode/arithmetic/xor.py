import quantumpseudocode as qp
from quantumpseudocode.ops import SignatureGate, Op


class XorEqualConst(Op):
    @staticmethod
    def emulate(lvalue: 'qp.Mutable[int]', mask: int):
        lvalue.val ^= mask

    @staticmethod
    def do(controls: 'qp.QubitIntersection',
           lvalue: 'qp.Quint',
           mask: int):
        targets = []
        for i, q in enumerate(lvalue):
            if mask & (1 << i):
                targets.append(q)
        qp.emit(qp.Toggle(qp.RawQureg(targets)).controlled_by(controls))

    def inverse(self):
        return self

    @staticmethod
    def describe(lvalue, mask):
        return '{} ^= {}'.format(lvalue, mask)


class XorEqual(Op):
    @staticmethod
    def emulate(lvalue: 'qp.Mutable[int]', mask: int):
        lvalue.val ^= mask

    @staticmethod
    def do(controls: 'qp.QubitIntersection',
           lvalue: 'qp.Quint',
           mask: 'qp.Quint'):
        for i, q in enumerate(lvalue):
            qp.emit(qp.Toggle(qp.RawQureg([q])).controlled_by(
                controls & mask[i]))

    def inverse(self):
        return self

    @staticmethod
    def describe(lvalue, mask):
        return '{} ^= {}'.format(lvalue, mask)
