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


def test_set_item_blocks():
    q = qp.Quint(qp.NamedQureg('test', 10))

    with pytest.raises(NotImplementedError):
        q[2] = qp.Qubit()


def test_mul_rmul():
    q = qp.Quint(qp.NamedQureg('test', 10))

    assert q * 5 == 5 * q == qp.ScaledIntRValue(q, 5)


def test_ixor():
    q = qp.Quint(qp.NamedQureg('test', 10))

    with pytest.raises(TypeError):
        q ^= None

    with qp.capture() as out:
        q ^= 5
    assert out == [qp.Toggle(lvalue=qp.RawQureg([q[0], q[2]]))]

    q2 = qp.Quint(qp.NamedQureg('test2', 5))
    with qp.capture() as out:
        q ^= q2
    assert out == [
        qp.Toggle(lvalue=qp.RawQureg([q[0]])).controlled_by(q2[0]),
        qp.Toggle(lvalue=qp.RawQureg([q[1]])).controlled_by(q2[1]),
        qp.Toggle(lvalue=qp.RawQureg([q[2]])).controlled_by(q2[2]),
        qp.Toggle(lvalue=qp.RawQureg([q[3]])).controlled_by(q2[3]),
        qp.Toggle(lvalue=qp.RawQureg([q[4]])).controlled_by(q2[4]),
    ]

    q3 = qp.Quint(qp.NamedQureg('test3', 5))
    c = qp.Qubit('c')
    with qp.capture() as out:
        q ^= q3 & qp.controlled_by(c)
    assert out == [
        qp.Toggle(lvalue=qp.RawQureg([q[0]])).controlled_by(q3[0] & c),
        qp.Toggle(lvalue=qp.RawQureg([q[1]])).controlled_by(q3[1] & c),
        qp.Toggle(lvalue=qp.RawQureg([q[2]])).controlled_by(q3[2] & c),
        qp.Toggle(lvalue=qp.RawQureg([q[3]])).controlled_by(q3[3] & c),
        qp.Toggle(lvalue=qp.RawQureg([q[4]])).controlled_by(q3[4] & c),
    ]

    # Classes can specify custom behavior via __rixor__.
    class Rixor:
        def __rixor__(self, other):
            qp.do_atom('yay!')
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
    assert qp.ccz_count(out) == 18

    with qp.capture() as out:
        q += 4
    assert qp.ccz_count(out) == 14

    with qp.capture() as out:
        q -= 3
    assert qp.ccz_count(out) == 18

    q2 = qp.Quint(qp.NamedQureg('test2', 5))
    with qp.capture() as out:
        q += q2
    assert qp.ccz_count(out) == 18

    # Classes can specify custom behavior via __riadd__.
    class Riadd:
        def __riadd__(self, other):
            qp.do_atom('yay!')
            return other
    with qp.capture() as out:
        q += Riadd()
    assert out == ['yay!']


def test_repr():
    cirq.testing.assert_equivalent_repr(
        qp.Quint(qp.NamedQureg('test', 10)),
        setup_code='import quantumpseudocode as qp')
