import quantumpseudocode as qp
from quantumpseudocode.ops import Op, semi_quantum


class PlusEqualConstMod(Op):
    @staticmethod
    def alloc_prefix():
        return '_addc_mod_'

    @staticmethod
    def biemulate(forward: bool,
                  *,
                  lvalue: 'qp.IntBuf',
                  offset: int,
                  modulus: int):
        v = int(lvalue)
        assert v < modulus
        sign = 1 if forward else -1
        lvalue[:] = (v + offset * sign) % modulus

    @staticmethod
    def do(controls: 'qp.QubitIntersection',
           *,
           lvalue: qp.Quint,
           offset: int,
           modulus: int):
        assert 0 <= offset < modulus
        assert isinstance(lvalue, qp.Quint)
        assert modulus > 0
        n = (modulus - 1).bit_length()
        assert len(lvalue) >= n

        if not modulus & (modulus - 1):
            lvalue += offset & qp.controlled_by(controls)
            return

        with qp.qmanaged(qp.Qubit(name='mod_cmp')) as q:
            q.init(lvalue >= modulus - offset, controls=controls)
            lvalue += offset & qp.controlled_by(controls)
            lvalue -= modulus & qp.controlled_by(q & controls)
            q.clear(lvalue < offset, controls=controls)

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
                  lvalue: 'qp.IntBuf',
                  offset: int,
                  modulus: int):
        v = int(lvalue)
        assert v < modulus
        sign = 1 if forward else -1
        lvalue[:] = (v + offset * sign) % modulus

    @staticmethod
    def do(controls: 'qp.QubitIntersection',
           *,
           lvalue: qp.Quint,
           offset: qp.Quint,
           modulus: int):
        assert len(offset) <= len(lvalue)
        assert isinstance(lvalue, qp.Quint)
        assert modulus > 0
        n = (modulus - 1).bit_length()
        assert len(lvalue) >= n

        if not modulus & (modulus - 1):
            lvalue += offset & qp.controlled_by(controls)
            return

        with offset.hold_padded_to(n) as offset:
            with qp.qmanaged(qp.Qubit(name='mod_cmp')) as q:
                offset ^= -1
                offset += modulus + 1
                q.init(lvalue >= offset, controls=controls)
                offset -= modulus + 1
                offset ^= -1

                lvalue += offset & qp.controlled_by(controls)
                lvalue -= modulus & qp.controlled_by(q & controls)
                q.clear(lvalue < offset, controls=controls)

    @staticmethod
    def describe(*, lvalue, offset, modulus):
        return '{} += {} (mod {})'.format(lvalue, offset, modulus)


@semi_quantum(alloc_prefix='_minus_mod_')
def minus_mod(control: 'qp.Qubit.Control',
              *,
              lvalue: qp.Quint,
              offset: qp.Quint.Borrowed,
              modulus: int):
    assert len(offset) <= len(lvalue)
    assert isinstance(lvalue, qp.Quint)
    assert modulus > 0
    n = (modulus - 1).bit_length()
    assert len(lvalue) >= n

    if not modulus & (modulus - 1):
        lvalue -= offset & qp.controlled_by(control)
        return

    with offset.hold_padded_to(n) as offset:
        with qp.qmanaged(qp.Qubit(name='mod_cmp')) as q:
            q.init(lvalue < offset, controls=control)
            lvalue += modulus & qp.controlled_by(q & control)
            lvalue -= offset & qp.controlled_by(control)

            offset ^= -1
            offset += modulus + 1
            q.clear(lvalue >= offset, controls=control)
            offset -= modulus + 1
            offset ^= -1

