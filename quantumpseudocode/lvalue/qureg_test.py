import cirq
import pytest

import quantumpseudocode


def test_raw_qureg_init():
    eq = cirq.testing.EqualsTester()
    a = quantumpseudocode.Qubit()
    b = quantumpseudocode.Qubit()
    eq.add_equality_group(quantumpseudocode.RawQureg([a, b]), quantumpseudocode.RawQureg([a, b]))
    eq.add_equality_group(quantumpseudocode.RawQureg([b, a]))
    eq.add_equality_group(quantumpseudocode.RawQureg([]))


def test_raw_qureg_getitem_len():
    a = quantumpseudocode.Qubit()
    b = quantumpseudocode.Qubit()
    q = quantumpseudocode.RawQureg([a,  b])
    assert len(q) == 2
    assert q[0] == a
    assert q[:] == q
    assert q[0:2] == q


def test_raw_qureg_repr():
    cirq.testing.assert_equivalent_repr(
        quantumpseudocode.RawQureg([quantumpseudocode.Qubit()]),
        setup_code='import quantumpseudocode'
    )


def test_named_qureg_init():
    eq = cirq.testing.EqualsTester()

    q1 = quantumpseudocode.NamedQureg('test', 10)
    q2 = quantumpseudocode.NamedQureg('test', 10)
    assert 'test' in str(q1)
    assert 'test' in str(q2)
    assert str(q1) != str(q2)

    eq.add_equality_group(quantumpseudocode.NamedQureg('', 5))
    eq.add_equality_group(quantumpseudocode.NamedQureg('', 5))
    eq.add_equality_group(q1)
    eq.add_equality_group(q2)
    eq.add_equality_group(quantumpseudocode.NamedQureg('q', 2))

    h = quantumpseudocode.UniqueHandle('test')
    eq.add_equality_group(quantumpseudocode.NamedQureg(h, 10), quantumpseudocode.NamedQureg(h, 10))
    eq.add_equality_group(quantumpseudocode.NamedQureg(h, 5))


def test_named_qureg_get_item_len():
    h = quantumpseudocode.UniqueHandle('a')
    q = quantumpseudocode.NamedQureg(h, 5)
    assert q[0] == quantumpseudocode.Qubit(h, 0)
    assert len(q) == 5
    assert q[:] == q
    assert q[2:4] == quantumpseudocode.RangeQureg(q, range(2, 4))


def test_named_qureg_repr():
    cirq.testing.assert_equivalent_repr(
        quantumpseudocode.NamedQureg('a', 3),
        setup_code='import quantumpseudocode')


def test_range_qureg_init():
    eq = cirq.testing.EqualsTester()

    a = quantumpseudocode.NamedQureg('a', 5)
    b = quantumpseudocode.NamedQureg('b', 5)
    eq.add_equality_group(a[:2])
    eq.add_equality_group(a[:3])
    eq.add_equality_group(b[:3])


def test_range_qureg_getitem_len():
    h = quantumpseudocode.UniqueHandle('a')
    a = quantumpseudocode.NamedQureg(h, 5)
    r = quantumpseudocode.RangeQureg(a, range(1, 3))
    assert r[0] == quantumpseudocode.Qubit(h, 1);
    assert r[1] == quantumpseudocode.Qubit(h, 2);
    assert r[-1] == quantumpseudocode.Qubit(h, 2);
    with pytest.raises(IndexError):
        _ = r[2]


def test_range_qureg_repr():
    h = quantumpseudocode.UniqueHandle('a')
    a = quantumpseudocode.NamedQureg(h, 5)
    r = quantumpseudocode.RangeQureg(a, range(1, 3))
    cirq.testing.assert_equivalent_repr(
        r,
        setup_code='import quantumpseudocode')
