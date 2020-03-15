import cirq
import pytest

import quantumpseudocode as qp


def test_init():
    eq = cirq.testing.EqualsTester()

    q1 = qp.Qubit('test', 10)
    q2 = qp.Qubit('test', 10)
    assert str(q1) == str(q2) == 'test[10]'

    eq.add_equality_group(qp.Qubit(), qp.Qubit())
    eq.add_equality_group(q1, q2)
    eq.add_equality_group(qp.Qubit('q'))


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
    with qp.LogCirqCircuit() as circuit:
        q ^= False
    assert len(circuit) == 0
    with qp.LogCirqCircuit() as circuit:
        q ^= True
    cirq.testing.assert_has_diagram(circuit, """
q: ---X---    
    """, use_unicode_characters=False)

    # Qubit and qubit intersection cause controlled toggle.
    with qp.LogCirqCircuit() as circuit:
        q ^= c
    cirq.testing.assert_has_diagram(circuit, """
c: ---@---
      |
q: ---X---    
        """, use_unicode_characters=False)
    with qp.LogCirqCircuit() as circuit:
        q ^= c & d
    cirq.testing.assert_has_diagram(circuit, """
c: ---@---
      |
d: ---@---
      |
q: ---X---    
        """, use_unicode_characters=False)

    # Classes can specify custom behavior via __rixor__.
    class Rixor:
        def __rixor__(self, other):
            qp.phase_flip()
            return other
    with qp.capture() as out:
        q ^= Rixor()
    assert out == [('phase_flip', qp.QubitIntersection.ALWAYS)]


def test_repr():
    cirq.testing.assert_equivalent_repr(
        qp.Qubit('test'),
        setup_code='import quantumpseudocode as qp')

    cirq.testing.assert_equivalent_repr(
        qp.Qubit('test', 10),
        setup_code='import quantumpseudocode as qp')
