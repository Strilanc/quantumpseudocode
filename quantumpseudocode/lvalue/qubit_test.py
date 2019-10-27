import cirq
import pytest

import quantumpseudocode as qp


def test_init():
    eq = cirq.testing.EqualsTester()

    q1 = qp.Qubit('test', 10)
    q2 = qp.Qubit('test', 10)
    assert 'test' in str(q1)
    assert 'test' in str(q2)
    assert str(q1) != str(q2)

    eq.add_equality_group(qp.Qubit())
    eq.add_equality_group(qp.Qubit())
    eq.add_equality_group(q1)
    eq.add_equality_group(q2)
    eq.add_equality_group(qp.Qubit('q'))

    h = qp.UniqueHandle('test')
    eq.add_equality_group(qp.Qubit(h), qp.Qubit(h))
    eq.add_equality_group(qp.Qubit(h, 5))
    eq.add_equality_group(qp.Qubit(h, 0), qp.Qubit(h, 0))


def test_and():
    a = qp.Qubit('a')
    b = qp.Qubit('b')
    c = qp.Qubit('c')
    d = qp.Qubit('d')
    s = qp.QubitIntersection((c, d))
    assert a & b == qp.QubitIntersection((a, b))
    assert a & b & c == qp.QubitIntersection((a, b, c))
    assert a & s == qp.QubitIntersection((a, c, d))
    assert a & False == qp.QubitIntersection.NEVER
    assert a & True is a
    assert False & a == qp.QubitIntersection.NEVER
    assert True & a is a


def test_ixor():
    q = qp.Qubit('q')
    c = qp.Qubit('c')
    d = qp.Qubit('d')

    # Unsupported classes cause type error.
    with pytest.raises(TypeError):
        q ^= None
    class C:
        pass
    with pytest.raises(TypeError):
        q ^= C()

    # False does nothing. True causes toggle.
    with qp.capture() as out:
        q ^= False
    assert out == []
    with qp.capture() as out:
        q ^= True
    assert out == [qp.Toggle(lvalue=qp.RawQureg([q]))]

    # Qubit and qubit intersection cause controlled toggle.
    with qp.capture() as out:
        q ^= c
    assert out == [qp.Toggle(lvalue=qp.RawQureg([q])).controlled_by(c)]
    with qp.capture() as out:
        q ^= c & d
    assert out == [qp.Toggle(lvalue=qp.RawQureg([q])).controlled_by(c & d)]

    # Classes can specify custom behavior via __rixor__.
    class Rixor:
        def __rixor__(self, other):
            qp.do_atom('yay!')
            return other
    with qp.capture() as out:
        q ^= Rixor()
    assert out == ['yay!']


def test_repr():
    cirq.testing.assert_equivalent_repr(
        qp.Qubit('test'),
        setup_code='import quantumpseudocode as qp')

    cirq.testing.assert_equivalent_repr(
        qp.Qubit('test', 10),
        setup_code='import quantumpseudocode as qp')
