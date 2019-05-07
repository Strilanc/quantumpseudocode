import quantumpseudocode as qp
from quantumpseudocode.ops import Op


class TimesEqual(Op):
    @staticmethod
    def alloc_prefix():
        return '_mul_'

    @staticmethod
    def biemulate(forward: bool,
                  *,
                  lvalue: 'qp.IntBuf',
                  factor: int):
        assert factor % 2 == 1
        if forward:
            lvalue *= factor
        else:
            lvalue *= qp.modular_multiplicative_inverse(factor, 2**len(lvalue))

    @staticmethod
    def do(controls: 'qp.QubitIntersection',
           *,
           lvalue: 'qp.Quint',
           factor: int):
        assert factor % 2 == 1
        for i in range(len(lvalue))[::-1]:
            c = controls & lvalue[i]
            lvalue[i+1:] += (factor >> 1) & qp.controlled_by(c)

    def describe(self, lvalue, factor):
        return '{} *= {}'.format(lvalue, factor)
