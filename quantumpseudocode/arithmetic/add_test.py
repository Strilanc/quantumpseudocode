import random

import cirq

import quantumpseudocode


def test_plus_equal_gate_circuit():
    with quantumpseudocode.Sim(enforce_release_at_zero=False):
        with quantumpseudocode.LogCirqCircuit() as circuit:
            with quantumpseudocode.qmanaged_int(bits=3, name='a') as a:
                with quantumpseudocode.qmanaged_int(bits=4, name='t') as t:
                    with quantumpseudocode.qmanaged(quantumpseudocode.Qubit(name='_c')) as c:
                        quantumpseudocode.emit(
                            quantumpseudocode.PlusEqualGate(lvalue=t, offset=a, carry_in=c))

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
    with quantumpseudocode.Sim(enforce_release_at_zero=False) as sim:
        bits = 4
        with quantumpseudocode.qmanaged_int(bits=bits, name='lvalue') as lvalue:
            for _ in range(10):
                sim.randomize_location(lvalue)

                old_state = sim.snapshot()
                op = quantumpseudocode.PlusEqualGate(lvalue=lvalue,
                                         offset=random.randint(0, 1 << bits),
                                         carry_in=random.random() < 0.5)
                quantumpseudocode.emit(op)
                sim.apply_op_via_emulation(op, forward=False)
                assert sim.snapshot() == old_state
