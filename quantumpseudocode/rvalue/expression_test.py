import itertools

import cirq
import pytest

import quantumpseudocode as qp


def test_let_and_circuit():
    with qp.Sim(enforce_release_at_zero=False):
        with qp.LogCirqCircuit() as circuit:
            with qp.qmanaged_int(bits=3, name='q') as q:
                q[0].init(q[1] & q[2])

    cirq.testing.assert_has_diagram(circuit, r"""
q[0]: ---X---
         |
q[1]: ---@---
         |
q[2]: ---@---
        """, use_unicode_characters=False)


def test_del_and_circuit():
    with qp.Sim(enforce_release_at_zero=False, phase_fixup_bias=True):
        with qp.LogCirqCircuit() as circuit:
            with qp.qmanaged_int(bits=3, name='q') as q:
                q[0].clear(q[1] & q[2])

    cirq.testing.assert_has_diagram(circuit, r"""
q[0]: ---Mxc-------

q[1]: ---------@---
               |
q[2]: ---------Z---
        """, use_unicode_characters=False)

    with qp.Sim(enforce_release_at_zero=False, phase_fixup_bias=False):
        with qp.LogCirqCircuit() as circuit:
            with qp.qmanaged_int(bits=3, name='b') as q:
                q[0].clear(q[1] & q[2])

    cirq.testing.assert_has_diagram(circuit, r"""
b[0]: ---Mxc---
        """, use_unicode_characters=False)


def test_uncompute():
    for a, b, p in itertools.product([False, True], repeat=3):
        with qp.Sim(phase_fixup_bias=p):
            with qp.hold(a, name='a') as qa:
                with qp.hold(b, name='b') as qb:
                    with qp.hold(a & b, name='c') as qc:
                        assert qp.measure(qa) == a
                        assert qp.measure(qb) == b
                        assert qp.measure(qc) == (a and b)


def test_intersection_and():
    a = qp.Qubit('a')
    b = qp.Qubit('b')
    c = qp.Qubit('c')
    d = qp.Qubit('d')
    assert a & b & c == qp.QubitIntersection((a, b, c))
    assert a & b & c & d == qp.QubitIntersection((a, b, c, d))
    assert (a & b) & c == a & (b & c)
    assert (a & b) & (c & d) == a & (b & (c & d))

    assert (a & b) & False == qp.QubitIntersection.NEVER
    assert False & (a & b) == qp.QubitIntersection.NEVER
    assert True & (a & b) == a & b


# HACK: workaround qubit name lifetime issues by hiding inside lambdas.
@pytest.mark.parametrize('value', [
    lambda: qp.QubitIntersection.NEVER,
    lambda: qp.QubitIntersection.ALWAYS,
    lambda: qp.QubitIntersection((qp.Qubit('a'),)),
    lambda: qp.QubitIntersection((qp.Qubit('a'), qp.Qubit('b'))),
])
def test_intersection_repr(value):
    cirq.testing.assert_equivalent_repr(
        value(),
        setup_code='import quantumpseudocode as qp')
