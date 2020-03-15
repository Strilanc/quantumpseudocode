import cirq

import quantumpseudocode as qp


def test_cmp():
    with qp.Sim():
        with qp.qalloc(len=4) as t:
            t.init(5)
            for k in range(-5, 30):
                assert qp.measure(t >= k) == (5 >= k)
                assert qp.measure(t > k) == (5 > k)
                assert qp.measure(t < k) == (5 < k)
                assert qp.measure(k < t) == (k < 5)
                assert qp.measure(t <= k) == (5 <= k)
            assert qp.measure(t, reset=True) == 5


def test_eq():
    with qp.Sim():
        with qp.qalloc(len=4) as t:
            t.init(5)
            for k in range(-2, 60):
                assert qp.measure(t == k) == (k == 5)
            assert qp.measure(t, reset=True) == 5


def test_neq():
    with qp.Sim():
        with qp.qalloc(len=4) as t:
            t.init(5)
            for k in range(-2, 60):
                with qp.hold(t != k) as q:
                    assert qp.measure(q) == (k != 5)
            assert qp.measure(t, reset=True) == 5


def test_eq_circuit():
    with qp.Sim(enforce_release_at_zero=False, phase_fixup_bias=True):
        with qp.LogCirqCircuit() as circuit:
            with qp.qalloc(len=4, name='lhs') as lhs:
                with qp.hold(lhs == 5, name='target'):
                    pass

    cirq.testing.assert_has_diagram(circuit, r"""
lhs[0]: ---alloc---------------@-----------------@-----------------------release---
           |                   |                 |                       |
lhs[1]: ---alloc-----------X---@---X---------X---@---X-------------------release---
           |               |   |   |         |   |   |                   |
lhs[2]: ---alloc-----------|---@---|---------|---@---|-------------------release---
           |               |   |   |         |   |   |                   |
lhs[3]: ---alloc-----------X---@---X---------X---Z---X-------------------release---
                               |
target: -----------alloc-------X-------Mxc---------------cxM---release-------------
        """, use_unicode_characters=False)


def test_if_less_than_then_circuit():
    with qp.Sim(enforce_release_at_zero=False):
        lhs = qp.qalloc(len=4, name='lhs')
        rhs = qp.qalloc(len=4, name='rhs')
        c = qp.qalloc(name='_or_eq')
        t = qp.qalloc(name='t')
        with qp.LogCirqCircuit() as circuit:
            qp.arithmetic.do_if_less_than(
                lhs=lhs,
                rhs=rhs,
                or_equal=c,
                effect=t.__ixor__)
    cirq.testing.assert_has_diagram(circuit, r"""
_or_eq: ---@---X---@-------------------------------------------------------------------------------@---X---@---
           |   |   |                                                                               |   |   |
lhs[0]: ---X---|---@-------------------------------------------------------------------------------@---|---X---
               |   |                                                                               |   |
lhs[1]: -------|---|---X-------@-------------------------------------------------------@-------X---|---|-------
               |   |   |       |                                                       |       |   |   |
lhs[2]: -------|---|---|-------|---X-------@-------------------------------@-------X---|-------|---|---|-------
               |   |   |       |   |       |                               |       |   |       |   |   |
lhs[3]: -------|---|---|-------|---|-------|---X-------@-------@-------X---|-------|---|-------|---|---|-------
               |   |   |       |   |       |   |       |       |       |   |       |   |       |   |   |
rhs[0]: -------@---X---@---X---@---|-------|---|-------|-------|-------|---|-------|---@---X---@---X---@-------
                           |   |   |       |   |       |       |       |   |       |   |   |
rhs[1]: -------------------@---X---@---X---@---|-------|-------|-------|---@---X---@---X---@-------------------
                                       |   |   |       |       |       |   |   |
rhs[2]: -------------------------------@---X---@---X---@-------@---X---@---X---@-------------------------------
                                                   |   |       |   |
rhs[3]: -------------------------------------------@---X---@---X---@-------------------------------------------
                                                           |
t: --------------------------------------------------------X---------------------------------------------------
        """, use_unicode_characters=False)
