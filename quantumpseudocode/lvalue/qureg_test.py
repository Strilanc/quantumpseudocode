import cirq
import pytest

import quantumpseudocode as qp


def test_raw_qureg_init():
    eq = cirq.testing.EqualsTester()
    a = qp.Qubit.lonely('')
    b = qp.Qubit.lonely('')
    eq.add_equality_group(qp.RawQureg([a, b]), qp.RawQureg([a, b]))
    eq.add_equality_group(qp.RawQureg([b, a]))
    eq.add_equality_group(qp.RawQureg([]))


def test_raw_qureg_getitem_len():
    a = qp.Qubit.lonely('')
    b = qp.Qubit.lonely('')
    q = qp.RawQureg([a,  b])
    assert len(q) == 2
    assert q[0] == a
    assert q[:] == q
    assert q[0:2] == q


def test_raw_qureg_repr():
    cirq.testing.assert_equivalent_repr(
        qp.RawQureg([qp.Qubit.lonely('')]),
        setup_code='import quantumpseudocode as qp'
    )


def test_named_qureg_init():
    eq = cirq.testing.EqualsTester()

    q1 = qp.NamedQureg('test', 10)
    q2 = qp.NamedQureg('test', 10)
    assert 'test' in str(q1)
    assert 'test' in str(q2)
    assert str(q1) != str(q2)

    eq.add_equality_group(qp.NamedQureg('', 5))
    eq.add_equality_group(qp.NamedQureg('', 5))
    eq.add_equality_group(q1)
    eq.add_equality_group(q2)
    eq.add_equality_group(qp.NamedQureg('q', 2))

    h = qp.UniqueHandle('test')
    eq.add_equality_group(qp.NamedQureg(h, 10), qp.NamedQureg(h, 10))
    eq.add_equality_group(qp.NamedQureg(h, 5))


def test_named_qureg_get_item_len():
    h = qp.UniqueHandle('a')
    q = qp.NamedQureg(h, 5)
    assert q[0] == qp.Qubit(q, 0)
    assert len(q) == 5
    assert q[:] == q
    assert q[2:4] == qp.RangeQureg(q, range(2, 4))


def test_named_qureg_repr():
    cirq.testing.assert_equivalent_repr(
        qp.NamedQureg('a', 3),
        setup_code='import qp as qp')


def test_range_qureg_init():
    eq = cirq.testing.EqualsTester()

    a = qp.NamedQureg('a', 5)
    b = qp.NamedQureg('b', 5)
    eq.add_equality_group(a[:2])
    eq.add_equality_group(a[:3])
    eq.add_equality_group(b[:3])


def test_range_qureg_getitem_len():
    h = qp.UniqueHandle('a')
    a = qp.NamedQureg(h, 5)
    r = qp.RangeQureg(a, range(1, 3))
    assert r[0] == qp.Qubit(a, 1);
    assert r[1] == qp.Qubit(a, 2);
    assert r[-1] == qp.Qubit(a, 2);
    with pytest.raises(IndexError):
        _ = r[2]


def test_range_qureg_repr():
    h = qp.UniqueHandle('a')
    a = qp.NamedQureg(h, 5)
    r = qp.RangeQureg(a, range(1, 3))
    cirq.testing.assert_equivalent_repr(
        r,
        setup_code='import quantumpseudocode as qp')
