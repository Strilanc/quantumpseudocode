import quantumpseudocode as qp
from quantumpseudocode.ops.signature_decorator import SimpleOp


class LetAnd(SimpleOp):
    def emulate(self,
                lvalue: 'qp.Mutable[bool]'):
        assert lvalue.val == 0
        lvalue.val = 1

    def inv_type(self):
        return DelAnd

    def sigdo(self,
              controls: 'qp.QubitIntersection',
              lvalue: qp.Qubit):
        lvalue ^= controls

    def describe(self, lvalue):
        return 'let {} := 1'.format(lvalue)


class DelAnd(SimpleOp):
    def emulate(self,
                lvalue: 'qp.Mutable[bool]'):
        assert lvalue.val == 1
        lvalue.val = 0

    def sigdo(self,
              controls: 'qp.QubitIntersection',
              lvalue: qp.Qubit):
        if qp.measure_x_for_phase_fixup_and_reset(lvalue):
            qp.phase_flip(controls)

    def inv_type(self):
        return LetAnd

    def describe(self, lvalue):
        return 'del {} =: 1'.format(lvalue)
