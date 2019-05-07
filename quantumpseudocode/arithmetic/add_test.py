import random

import cirq

import quantumpseudocode as qp


def assert_adds_correctly(n1: int, n2: int, v1: int, v2: int):
    assert_control_adds_correctly(n1, n2, v1, v2, False)
    assert_control_adds_correctly(n1, n2, v1, v2, True)

    def f(a: qp.Quint, b: qp.Quint):
        a += b
    r = qp.testing.sim_call(f,
                            qp.IntBuf.raw(val=v1, length=n1),
                            qp.IntBuf.raw(val=v2, length=n2))
    assert r == qp.ArgsAndKwargs([
        (v1 + v2) % 2**n1,
        v2
    ], {})


def assert_control_adds_correctly(n1: int, n2: int, v1: int, v2: int,
                                  control: bool):
    def f(a: qp.Quint, b: qp.Quint, c: qp.Qubit):
        # with qp.controlled_by(c):
            a += b & qp.controlled_by(c)
    r = qp.testing.sim_call(f,
                            qp.IntBuf.raw(val=v1, length=n1),
                            qp.IntBuf.raw(val=v2, length=n2),
                            control)
    assert r == qp.ArgsAndKwargs([
        (v1 + v2) % 2**n1 if control else v1,
        v2,
        control
    ], {})


def test_function():
    assert_control_adds_correctly(1, 1, 0, 1, False)
    # for n1 in range(3):
    #     for n2 in range(3):
    #         for v1 in range(1 << n1):
    #             for v2 in range(1 << n2):
    #                 assert_adds_correctly(n1, n2, v1, v2)
    #
    # for _ in range(10):
    #     n1 = random.randint(0, 100)
    #     n2 = random.randint(0, 100)
    #     v1 = random.randint(0, 2**n1 - 1)
    #     v2 = random.randint(0, 2**n2 - 1)
    #     assert_adds_correctly(n1, n2, v1, v2)


# def test_plus_equal_gate_circuit():
#     with qp.Sim(enforce_release_at_zero=False):
#         with qp.LogCirqCircuit() as circuit:
#             with qp.qmanaged_int(bits=3, name='a') as a:
#                 with qp.qmanaged_int(bits=4, name='t') as t:
#                     with qp.qmanaged(qp.Qubit(name='_c')) as c:
#                         qp.emit(
#                             qp.PlusEqual(lvalue=t, offset=a, carry_in=c))
#
#     cirq.testing.assert_has_diagram(circuit, r"""
# _c: -----X-------@---------------------------------------------------------------@---@-------X---
#          |       |                                                               |   |       |
# a[0]: ---@---@---X---X-------@-----------------------------------@---@-------X---X---|---@---@---
#              |   |   |       |                                   |   |       |   |   |   |
# a[1]: -------|---|---@---@---X---X-------@-------@---@-------X---X---|---@---@---|---|---|-------
#              |   |       |   |   |       |       |   |       |   |   |   |       |   |   |
# a[2]: -------|---|-------|---|---@---@---X---@---X---|---@---@---|---|---|-------|---|---|-------
#              |   |       |   |       |   |   |   |   |   |       |   |   |       |   |   |
# t[0]: -------X---@-------|---|-------|---|---|---|---|---|-------|---|---|-------@---X---X-------
#                          |   |       |   |   |   |   |   |       |   |   |
# t[1]: -------------------X---@-------|---|---|---|---|---|-------@---X---X-----------------------
#                                      |   |   |   |   |   |
# t[2]: -------------------------------X---@---|---@---X---X---------------------------------------
#                                              |
# t[3]: ---------------------------------------X---------------------------------------------------
#         """, use_unicode_characters=False)
#
#
# def test_vs_emulation():
#     with qp.Sim(enforce_release_at_zero=False) as sim:
#         bits = 4
#         with qp.qmanaged_int(bits=bits, name='lvalue') as lvalue:
#             for _ in range(10):
#                 sim.randomize_location(lvalue)
#
#                 old_state = sim.snapshot()
#                 op = qp.PlusEqual(lvalue=lvalue,
#                                   offset=random.randint(0, 1 << bits),
#                                   carry_in=random.random() < 0.5)
#                 qp.emit(op)
#                 sim.apply_op_via_emulation(op, forward=False)
#                 assert sim.snapshot() == old_state
