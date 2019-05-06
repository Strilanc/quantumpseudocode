import cirq
import pytest

import quantumpseudocode


def test_init():
    q1 = quantumpseudocode.Quint(quantumpseudocode.NamedQureg('test', 10))
    q2 = quantumpseudocode.Quint(quantumpseudocode.NamedQureg('test', 10))
    assert q1 != q2
    assert 'test' in str(q1)
    assert 'test' in str(q2)
    assert str(q1) != str(q2)

    h = quantumpseudocode.UniqueHandle('test')
    h1 = quantumpseudocode.Quint(quantumpseudocode.NamedQureg(h, 10))
    h2 = quantumpseudocode.Quint(quantumpseudocode.NamedQureg(h, 10))
    assert q1 != h1 == h2 != q2


def test_len_getitem():
    h = quantumpseudocode.UniqueHandle('test')
    q = quantumpseudocode.Quint(quantumpseudocode.NamedQureg(h, 10))
    assert len(q) == 10

    with pytest.raises(IndexError):
        _ = q[-100]

    assert q[0] == quantumpseudocode.Qubit(h, 0)
    assert q[-1] == quantumpseudocode.Qubit(h, 9)
    assert q[2:4] == quantumpseudocode.Quint(quantumpseudocode.RangeQureg(
        quantumpseudocode.NamedQureg(h, 10), range(2, 4)))


def test_set_item():
    q = quantumpseudocode.Quint(quantumpseudocode.NamedQureg('test', 10))

    with pytest.raises(NotImplementedError):
        q[2] = quantumpseudocode.Qubit()

    with quantumpseudocode.capture() as out:
        q[2] ^= q[3]
    assert out == [quantumpseudocode.OP_TOGGLE(quantumpseudocode.RawQureg([q[2]])).controlled_by(q[3])]

    with quantumpseudocode.capture() as out:
        q[2:] += 5
    assert out == [quantumpseudocode.PlusEqualGate(lvalue=q[2:],
                                       offset=5,
                                       carry_in=False)]


def test_mul_rmul():
    q = quantumpseudocode.Quint(quantumpseudocode.NamedQureg('test', 10))

    assert q * 5 == 5 * q == quantumpseudocode.ScaledIntRValue(q, 5)


def test_ixor():
    q = quantumpseudocode.Quint(quantumpseudocode.NamedQureg('test', 10))

    with pytest.raises(TypeError):
        q ^= None

    with quantumpseudocode.capture() as out:
        q ^= 5
    assert out == [quantumpseudocode.OP_XOR_C(q, 5)]

    q2 = quantumpseudocode.Quint(quantumpseudocode.NamedQureg('test2', 5))
    with quantumpseudocode.capture() as out:
        q ^= q2
    assert out == [quantumpseudocode.OP_XOR(q, q2)]

    # Classes can specify custom behavior via __rixor__.
    class Rixor:
        def __rixor__(self, other):
            quantumpseudocode.emit('yay!')
            return other
    with quantumpseudocode.capture() as out:
        q ^= Rixor()
    assert out == ['yay!']


def test_iadd_isub():
    q = quantumpseudocode.Quint(quantumpseudocode.NamedQureg('test', 10))

    with pytest.raises(TypeError):
        q += None

    with quantumpseudocode.capture() as out:
        q += 5
    assert out == [quantumpseudocode.PlusEqualGate(lvalue=q,
                                       offset=5,
                                       carry_in=False)]

    with quantumpseudocode.capture() as out:
        q += 4
    assert out == [quantumpseudocode.PlusEqualGate(lvalue=q[2:],
                                       offset=1,
                                       carry_in=False)]

    with quantumpseudocode.capture() as out:
        q -= 3
    assert out == [quantumpseudocode.InverseOperation(
        quantumpseudocode.PlusEqualGate(lvalue=q,
                            offset=3,
                            carry_in=False))]

    q2 = quantumpseudocode.Quint(quantumpseudocode.NamedQureg('test2', 5))
    with quantumpseudocode.capture() as out:
        q += q2
    assert out == [quantumpseudocode.PlusEqualGate(lvalue=q,
                                       offset=q2,
                                       carry_in=False)]

    # Classes can specify custom behavior via __riadd__.
    class Riadd:
        def __riadd__(self, other):
            quantumpseudocode.emit('yay!')
            return other
    with quantumpseudocode.capture() as out:
        q += Riadd()
    assert out == ['yay!']


def test_repr():
    cirq.testing.assert_equivalent_repr(
        quantumpseudocode.Quint(quantumpseudocode.NamedQureg('test', 10)),
        setup_code='import quantumpseudocode')
