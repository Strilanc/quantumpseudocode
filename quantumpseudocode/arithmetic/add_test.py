import random

import cirq

import quantumpseudocode as qp


def test_plus_equal_gate_circuit():
    with qp.Sim(enforce_release_at_zero=False):
        with qp.LogCirqCircuit() as circuit:
            with qp.qmanaged_int(bits=3, name='a') as a:
                with qp.qmanaged_int(bits=4, name='t') as t:
                    with qp.qmanaged(qp.Qubit(name='_c')) as c:
                        qp.emit(
                            qp.PlusEqual(lvalue=t, offset=a, carry_in=c))

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


def test_vs_emulation():
    with qp.Sim(enforce_release_at_zero=False) as sim:
        bits = 4
        with qp.qmanaged_int(bits=bits, name='lvalue') as lvalue:
            for _ in range(10):
                sim.randomize_location(lvalue)

                old_state = sim.snapshot()
                op = qp.PlusEqual(lvalue=lvalue,
                                  offset=random.randint(0, 1 << bits),
                                  carry_in=random.random() < 0.5)
                qp.emit(op)
                sim.apply_op_via_emulation(op, forward=False)
                assert sim.snapshot() == old_state
