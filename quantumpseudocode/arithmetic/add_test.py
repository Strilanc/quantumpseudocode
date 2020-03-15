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
    for n1 in range(3):
        for n2 in range(3):
            for v1 in range(1 << n1):
                for v2 in range(1 << n2):
                    assert_adds_correctly(n1, n2, v1, v2)

    for _ in range(10):
        n1 = random.randint(0, 100)
        n2 = random.randint(0, 100)
        v1 = random.randint(0, 2**n1 - 1)
        v2 = random.randint(0, 2**n2 - 1)
        assert_adds_correctly(n1, n2, v1, v2)


def test_plus_equal_gate_circuit():
    with qp.Sim(enforce_release_at_zero=False):
        with qp.LogCirqCircuit() as circuit:
            with qp.qalloc(len=3, name='a') as a:
                with qp.qalloc(len=4, name='t') as t:
                    with qp.qalloc(name='_c') as c:
                        qp.arithmetic.do_addition(lvalue=t, offset=a, carry_in=c)

    cirq.testing.assert_has_diagram(circuit, r"""
_c: ---------------------alloc---X-------@---------------------------------------------------------------@---@-------X---release-----------------------
                                 |       |                                                               |   |       |
a[0]: ---alloc-------------------@---@---X---X-------@-----------------------------------@---@-------X---X---|---@---@-----------------------release---
         |                           |   |   |       |                                   |   |       |   |   |   |                           |
a[1]: ---alloc-----------------------|---|---@---@---X---X-------@-------@---@-------X---X---|---@---@---|---|---|---------------------------release---
         |                           |   |       |   |   |       |       |   |       |   |   |   |       |   |   |                           |
a[2]: ---alloc-----------------------|---|-------|---|---@---@---X---@---X---|---@---@---|---|---|-------|---|---|---------------------------release---
                                     |   |       |   |       |   |   |   |   |   |       |   |   |       |   |   |
t[0]: -----------alloc---------------X---@-------|---|-------|---|---|---|---|---|-------|---|---|-------@---X---X-----------------release-------------
                 |                               |   |       |   |   |   |   |   |       |   |   |                                 |
t[1]: -----------alloc---------------------------X---@-------|---|---|---|---|---|-------@---X---X---------------------------------release-------------
                 |                                           |   |   |   |   |   |                                                 |
t[2]: -----------alloc---------------------------------------X---@---|---@---X---X-------------------------------------------------release-------------
                 |                                                   |                                                             |
t[3]: -----------alloc-----------------------------------------------X-------------------------------------------------------------release-------------
        """, use_unicode_characters=False)


def test_quantum_classical_consistent():
    qp.testing.assert_semi_quantum_func_is_consistent(
        qp.arithmetic.do_addition,
        fuzz_space={
            'lvalue': lambda: qp.IntBuf.random(range(0, 6)),
            'offset': lambda: random.randint(0, 511),
            'carry_in': [False, True],
        },
        fuzz_count=100)

    qp.testing.assert_semi_quantum_func_is_consistent(
        qp.arithmetic.do_addition,
        fixed=[{
            'lvalue': qp.IntBuf.raw(val=3, length=3),
            'offset': 2
        }])

    qp.testing.assert_semi_quantum_func_is_consistent(
        qp.arithmetic.do_subtraction,
        fuzz_space={
            'lvalue': lambda: qp.IntBuf.random(range(0, 6)),
            'offset': lambda: random.randint(0, 511),
            'carry_in': [False, True],
        },
        fuzz_count=100)

    qp.testing.assert_semi_quantum_func_is_consistent(
        qp.arithmetic.do_subtraction,
        fixed=[{
            'lvalue': qp.IntBuf.raw(val=3, length=3),
            'offset': 2
        }])
