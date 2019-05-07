import cirq
import pytest

import quantumpseudocode as qp


def test_init():
    q1 = qp.Quint(qp.NamedQureg('test', 10))
    q2 = qp.Quint(qp.NamedQureg('test', 10))
    assert q1 != q2
    assert 'test' in str(q1)
    assert 'test' in str(q2)
    assert str(q1) != str(q2)

    h = qp.UniqueHandle('test')
    h1 = qp.Quint(qp.NamedQureg(h, 10))
    h2 = qp.Quint(qp.NamedQureg(h, 10))
    assert q1 != h1 == h2 != q2


def test_len_getitem():
    h = qp.UniqueHandle('test')
    q = qp.Quint(qp.NamedQureg(h, 10))
    assert len(q) == 10

    with pytest.raises(IndexError):
        _ = q[-100]

    assert q[0] == qp.Qubit(h, 0)
    assert q[-1] == qp.Qubit(h, 9)
    assert q[2:4] == qp.Quint(qp.RangeQureg(
        qp.NamedQureg(h, 10), range(2, 4)))


def test_set_item():
    q = qp.Quint(qp.NamedQureg('test', 10))

    with pytest.raises(NotImplementedError):
        q[2] = qp.Qubit()

    with qp.capture() as out:
        q[2] ^= q[3]
    assert out == [qp.OP_TOGGLE(qp.RawQureg([q[2]])).controlled_by(q[3])]

    with qp.capture() as out:
        q[2:] += 5
    assert out == [qp.PlusEqual(lvalue=q[2:],
                                offset=5,
                                carry_in=False)]


def test_mul_rmul():
    q = qp.Quint(qp.NamedQureg('test', 10))

    assert q * 5 == 5 * q == qp.ScaledIntRValue(q, 5)


def test_ixor():
    q = qp.Quint(qp.NamedQureg('test', 10))

    with pytest.raises(TypeError):
        q ^= None

    with qp.capture() as out:
        q ^= 5
    assert out == [qp.XorEqualConst(q, 5)]

    q2 = qp.Quint(qp.NamedQureg('test2', 5))
    with qp.capture() as out:
        q ^= q2
    assert out == [qp.XorEqual(q, q2)]

    # Classes can specify custom behavior via __rixor__.
    class Rixor:
        def __rixor__(self, other):
            qp.emit('yay!')
            return other
    with qp.capture() as out:
        q ^= Rixor()
    assert out == ['yay!']


def test_iadd_isub():
    q = qp.Quint(qp.NamedQureg('test', 10))

    with pytest.raises(TypeError):
        q += None

    with qp.capture() as out:
        q += 5
    assert out == [qp.PlusEqual(lvalue=q,
                                offset=5,
                                carry_in=False)]

    with qp.capture() as out:
        q += 4
    assert out == [qp.PlusEqual(lvalue=q[2:],
                                offset=1,
                                carry_in=False)]

    with qp.capture() as out:
        q -= 3
    assert out == [
        qp.InverseOperation(qp.PlusEqual(
            lvalue=q,
            offset=3,
            carry_in=False))
    ]

    q2 = qp.Quint(qp.NamedQureg('test2', 5))
    with qp.capture() as out:
        q += q2
    assert out == [qp.PlusEqual(lvalue=q,
                                offset=q2,
                                carry_in=False)]

    # Classes can specify custom behavior via __riadd__.
    class Riadd:
        def __riadd__(self, other):
            qp.emit('yay!')
            return other
    with qp.capture() as out:
        q += Riadd()
    assert out == ['yay!']


def test_repr():
    cirq.testing.assert_equivalent_repr(
        qp.Quint(qp.NamedQureg('test', 10)),
        setup_code='import quantumpseudocode as qp')
