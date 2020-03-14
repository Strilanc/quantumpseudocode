import cirq
import pytest

import quantumpseudocode as qp


def test_init():
    q1 = qp.Quint(qp.NamedQureg('test', 10))
    q2 = qp.Quint(qp.NamedQureg('test', 10))
    assert q1.qureg != q2.qureg
    assert 'test' in str(q1)
    assert 'test' in str(q2)
    assert str(q1) != str(q2)

    h = qp.UniqueHandle('test')
    h1 = qp.Quint(qp.NamedQureg(h, 10))
    h2 = qp.Quint(qp.NamedQureg(h, 10))
    assert q1.qureg != h1.qureg == h2.qureg != q2.qureg


def test_len_getitem():
    h = qp.UniqueHandle('test')
    q = qp.Quint(qp.NamedQureg(h, 10))
    assert len(q) == 10

    with pytest.raises(IndexError):
        _ = q[-100]

    assert q[0] == qp.Qubit(h, 0)
    assert q[-1] == qp.Qubit(h, 9)
    assert q[2:4].qureg == qp.Quint(qp.RangeQureg(
        qp.NamedQureg(h, 10), range(2, 4))).qureg


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

    with qp.LogCirqCircuit() as circuit:
        q ^= 5
    cirq.testing.assert_has_diagram(circuit, """
test[0]: ---X---
            |
test[2]: ---X---
    """, use_unicode_characters=False)

    q2 = qp.Quint(qp.NamedQureg('test2', 5))
    with qp.LogCirqCircuit() as circuit:
        q ^= q2
        cirq.testing.assert_has_diagram(circuit, """
test2[0]: ---@-------------------
             |
test2[1]: ---|---@---------------
             |   |
test2[2]: ---|---|---@-----------
             |   |   |
test2[3]: ---|---|---|---@-------
             |   |   |   |
test2[4]: ---|---|---|---|---@---
             |   |   |   |   |
test[0]: ----X---|---|---|---|---
                 |   |   |   |
test[1]: --------X---|---|---|---
                     |   |   |
test[2]: ------------X---|---|---
                         |   |
test[3]: ----------------X---|---
                             |
test[4]: --------------------X---
        """, use_unicode_characters=False)

    q3 = qp.Quint(qp.NamedQureg('test3', 5))
    c = qp.Qubit('c')
    with qp.LogCirqCircuit() as circuit:
        q ^= q3 & qp.controlled_by(c)
        cirq.testing.assert_has_diagram(circuit, """
c: ----------@---@---@---@---@---
             |   |   |   |   |
test3[0]: ---@---|---|---|---|---
             |   |   |   |   |
test3[1]: ---|---@---|---|---|---
             |   |   |   |   |
test3[2]: ---|---|---@---|---|---
             |   |   |   |   |
test3[3]: ---|---|---|---@---|---
             |   |   |   |   |
test3[4]: ---|---|---|---|---@---
             |   |   |   |   |
test[0]: ----X---|---|---|---|---
                 |   |   |   |
test[1]: --------X---|---|---|---
                     |   |   |
test[2]: ------------X---|---|---
                         |   |
test[3]: ----------------X---|---
                             |
test[4]: --------------------X---
            """, use_unicode_characters=False)

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

    with qp.capture(measure_bias=0.5) as out:
        q += 5
    assert qp.ccz_count(out) == 18

    with qp.capture(measure_bias=0.5) as out:
        q += 4
    assert qp.ccz_count(out) == 14

    with qp.capture(measure_bias=0.5) as out:
        q -= 3
    assert qp.ccz_count(out) == 18

    q2 = qp.Quint(qp.NamedQureg('test2', 5))
    with qp.capture(measure_bias=0.5) as out:
        q += q2
    assert qp.ccz_count(out) == 18

    # Classes can specify custom behavior via __riadd__.
    class Riadd:
        def __riadd__(self, other):
            qp.emit('yay!')
            return other
    with qp.capture() as out:
        q += Riadd()
    assert out == ['yay!']
