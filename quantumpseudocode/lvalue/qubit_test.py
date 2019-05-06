import cirq
import pytest

import quantumpseudocode


def test_init():
    eq = cirq.testing.EqualsTester()

    q1 = quantumpseudocode.Qubit('test', 10)
    q2 = quantumpseudocode.Qubit('test', 10)
    assert 'test' in str(q1)
    assert 'test' in str(q2)
    assert str(q1) != str(q2)

    eq.add_equality_group(quantumpseudocode.Qubit())
    eq.add_equality_group(quantumpseudocode.Qubit())
    eq.add_equality_group(q1)
    eq.add_equality_group(q2)
    eq.add_equality_group(quantumpseudocode.Qubit('q'))

    h = quantumpseudocode.UniqueHandle('test')
    eq.add_equality_group(quantumpseudocode.Qubit(h), quantumpseudocode.Qubit(h))
    eq.add_equality_group(quantumpseudocode.Qubit(h, 5))
    eq.add_equality_group(quantumpseudocode.Qubit(h, 0), quantumpseudocode.Qubit(h, 0))


def test_and():
    a = quantumpseudocode.Qubit('a')
    b = quantumpseudocode.Qubit('b')
    c = quantumpseudocode.Qubit('c')
    d = quantumpseudocode.Qubit('d')
    s = quantumpseudocode.QubitIntersection((c, d))
    assert a & b == quantumpseudocode.QubitIntersection((a, b))
    assert a & b & c == quantumpseudocode.QubitIntersection((a, b, c))
    assert a & s == quantumpseudocode.QubitIntersection((a, c, d))


def test_ixor():
    q = quantumpseudocode.Qubit('q')
    c = quantumpseudocode.Qubit('c')
    d = quantumpseudocode.Qubit('d')

    # Unsupported classes cause type error.
    with pytest.raises(TypeError):
        q ^= None
    class C:
        pass
    with pytest.raises(TypeError):
        q ^= C()

    # False does nothing. True causes toggle.
    with quantumpseudocode.capture() as out:
        q ^= False
    assert out == []
    with quantumpseudocode.capture() as out:
        q ^= True
    assert out == [quantumpseudocode.OP_TOGGLE(quantumpseudocode.RawQureg([q]))]

    # Qubit and qubit intersection cause controlled toggle.
    with quantumpseudocode.capture() as out:
        q ^= c
    assert out == [quantumpseudocode.OP_TOGGLE(quantumpseudocode.RawQureg([q])).controlled_by(c)]
    with quantumpseudocode.capture() as out:
        q ^= c & d
    assert out == [quantumpseudocode.OP_TOGGLE(quantumpseudocode.RawQureg([q])).controlled_by(c & d)]

    # Classes can specify custom behavior via __rixor__.
    class Rixor:
        def __rixor__(self, other):
            quantumpseudocode.emit('yay!')
            return other
    with quantumpseudocode.capture() as out:
        q ^= Rixor()
    assert out == ['yay!']


def test_repr():
    cirq.testing.assert_equivalent_repr(
        quantumpseudocode.Qubit('test'),
        setup_code='import quantumpseudocode')

    cirq.testing.assert_equivalent_repr(
        quantumpseudocode.Qubit('test', 10),
        setup_code='import quantumpseudocode')
