import quantumpseudocode as qp
from quantumpseudocode.ops.simple_op import Op


class LetAnd(Op):
    @staticmethod
    def emulate(lvalue: 'qp.Mutable[bool]'):
        assert lvalue.val == 0
        lvalue.val = 1

    @staticmethod
    def inv_type():
        return DelAnd

    @staticmethod
    def do(controls: 'qp.QubitIntersection', lvalue: qp.Qubit):
        lvalue ^= controls

    @staticmethod
    def describe(lvalue):
        return 'let {} := 1'.format(lvalue)


class DelAnd(Op):
    @staticmethod
    def emulate(lvalue: 'qp.Mutable[bool]'):
        assert lvalue.val == 1
        lvalue.val = 0

    @staticmethod
    def do(controls: 'qp.QubitIntersection',
           lvalue: qp.Qubit):
        if qp.measure_x_for_phase_fixup_and_reset(lvalue):
            qp.phase_flip(controls)

    @staticmethod
    def inv_type():
        return LetAnd

    @staticmethod
    def describe(lvalue):
        return 'del {} =: 1'.format(lvalue)
