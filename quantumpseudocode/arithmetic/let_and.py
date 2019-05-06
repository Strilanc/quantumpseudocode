import quantumpseudocode
from quantumpseudocode.ops.signature_gate import SignatureGate


class _LetAndGate(SignatureGate):
    def emulate(self,
                forward: bool,
                *,
                lvalue: 'quantumpseudocode.Mutable[bool]'):
        if forward:
            assert lvalue.val == 0
            lvalue.val = 1
        else:
            assert lvalue.val == 1
            lvalue.val = 0

    def __pow__(self, power):
        if power == -1:
            return DelAnd

    def do(self,
           controls: 'quantumpseudocode.QubitIntersection',
           lvalue: quantumpseudocode.Qubit):
        lvalue ^= controls

    def describe(self, lvalue):
        return '{} := 1'.format(lvalue)

    def __repr__(self):
        return 'quantumpseudocode.LetAnd'


class _DelAndGate(SignatureGate):
    def emulate(self,
                forward: bool,
                *,
                lvalue: 'quantumpseudocode.Mutable[bool]'):
        LetAnd.emulate(not forward, lvalue=lvalue)

    def do(self,
           controls: 'quantumpseudocode.QubitIntersection',
           lvalue: quantumpseudocode.Qubit):
        if quantumpseudocode.measure_x_for_phase_fixup_and_reset(lvalue):
            quantumpseudocode.phase_flip(controls)

    def __pow__(self, power):
        if power == -1:
            return LetAnd

    def describe(self, lvalue):
        return '{} =: del 1'.format(lvalue)

    def __repr__(self):
        return 'quantumpseudocode.DelAnd'


LetAnd = _LetAndGate()
DelAnd = _DelAndGate()
