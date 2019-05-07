import quantumpseudocode as qp
from quantumpseudocode.ops import Op


class PlusEqualConstMod(Op):
    @staticmethod
    def alloc_prefix():
        return '_addc_mod_'

    @staticmethod
    def biemulate(forward: bool,
                  *,
                  lvalue: 'qp.Mutable[int]',
                  offset: int,
                  modulus: int):
        assert lvalue.val < modulus
        sign = 1 if forward else -1
        lvalue.val = (lvalue.val + offset * sign) % modulus

    @staticmethod
    def do(controls: 'qp.QubitIntersection',
           *,
           lvalue: qp.Quint,
           offset: int,
           modulus: int):
        assert 0 <= offset < modulus
        assert isinstance(lvalue, qp.Quint)
        with qp.qmanaged(qp.Qubit(name='mod_cmp')) as q:
            q.init(lvalue >= modulus - offset)
            lvalue += offset & qp.controlled_by(controls)
            lvalue -= modulus & qp.controlled_by(q & controls)
            q.clear(lvalue < offset)

    @staticmethod
    def describe(*, lvalue, offset, modulus):
        return '{} += {} (mod {})'.format(lvalue, offset, modulus)


class PlusEqualMod(Op):
    @staticmethod
    def alloc_prefix():
        return '_addc_mod_'

    @staticmethod
    def biemulate(forward: bool,
                  *,
                  lvalue: 'qp.Mutable[int]',
                  offset: int,
                  modulus: int):
        assert lvalue.val < modulus
        sign = 1 if forward else -1
        lvalue.val = (lvalue.val + offset * sign) % modulus

    @staticmethod
    def do(controls: 'qp.QubitIntersection',
           *,
           lvalue: qp.Quint,
           offset: qp.Quint,
           modulus: int):
        assert len(offset) <= len(lvalue)
        assert isinstance(lvalue, qp.Quint)
        with qp.pad(offset, min_len=len(lvalue)) as p:
            p_off = qp.Quint(p)
            with qp.qmanaged(qp.Qubit(name='mod_cmp')) as q:
                p_off ^= -1
                p_off += modulus + 1
                q.init(lvalue >= p_off)
                p_off -= modulus + 1
                p_off ^= -1

                lvalue += p_off & qp.controlled_by(controls)
                lvalue -= modulus & qp.controlled_by(q & controls)
                q.clear(lvalue < offset)

    @staticmethod
    def describe(*, lvalue, offset, modulus):
        return '{} += {} (mod {})'.format(lvalue, offset, modulus)
