import random

import cirq

import quantumpseudocode as qp


def test_plus_equal_gate_circuit():
    with qp.Sim(enforce_release_at_zero=False):
        a = qp.qalloc(len=3, name='a')
        t = qp.qalloc(len=4, name='t')
        c = qp.qalloc(name='_c')
        with qp.LogCirqCircuit() as circuit:
            qp.arithmetic.do_addition(lvalue=t, offset=a, carry_in=c)

    cirq.testing.assert_has_diagram(circuit, r"""
_c: -----X-------@---------------------------------------------------------------@---@-------X---
         |       |                                                               |   |       |
a[0]: ---@---@---X---X-------@-----------------------------------@---@-------X---X---|---@---@---
             |   |   |       |                                   |   |       |   |   |   |
a[1]: -------|---|---@---@---X---X-------@-------@---@-------X---X---|---@---@---|---|---|-------
             |   |       |   |   |       |       |   |       |   |   |   |       |   |   |
a[2]: -------|---|-------|---|---@---@---X---@---X---|---@---@---|---|---|-------|---|---|-------
             |   |       |   |       |   |   |   |   |   |       |   |   |       |   |   |
t[0]: -------X---@-------|---|-------|---|---|---|---|---|-------|---|---|-------@---X---X-------
                         |   |       |   |   |   |   |   |       |   |   |
t[1]: -------------------X---@-------|---|---|---|---|---|-------@---X---X-----------------------
                                     |   |   |   |   |   |
t[2]: -------------------------------X---@---|---@---X---X---------------------------------------
                                             |
t[3]: ---------------------------------------X---------------------------------------------------
        """, use_unicode_characters=False)


def test_quantum_classical_consistent():
    qp.testing.assert_semi_quantum_func_is_consistent(
        qp.arithmetic.do_addition,
        fuzz_space={
            'lvalue': lambda: qp.IntBuf.random(range(0, 6)),
            'offset': lambda: random.randint(0, 511),
            'carry_in': [False, True],
            'forward': [False, True],
        },
        fuzz_count=100)

    qp.testing.assert_semi_quantum_func_is_consistent(
        qp.arithmetic.do_addition,
        fixed=[{
            'lvalue': qp.IntBuf.raw(val=3, length=3),
            'offset': 2,
            'forward': True,
        }])
