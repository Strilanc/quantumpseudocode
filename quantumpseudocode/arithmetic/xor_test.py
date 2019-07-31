import random

import cirq

import quantumpseudocode as qp


def assert_xors_correctly(n1: int, n2: int, v1: int, v2: int):
    assert_control_xors_correctly(n1, n2, v1, v2, False)
    assert_control_xors_correctly(n1, n2, v1, v2, True)

    def f(a: qp.Quint, b: qp.Quint):
        a ^= b
    r = qp.testing.sim_call(f,
                            qp.IntBuf.raw(val=v1, length=n1),
                            qp.IntBuf.raw(val=v2, length=n2))
    assert r == qp.ArgsAndKwargs([
        v1 ^ v2,
        v2
    ], {})


def assert_control_xors_correctly(n1: int, n2: int, v1: int, v2: int,
                                  control: bool):
    def f(a: qp.Quint, b: qp.Quint, c: qp.Qubit):
        a ^= b & qp.controlled_by(c)
    r = qp.testing.sim_call(f,
                            qp.IntBuf.raw(val=v1, length=n1),
                            qp.IntBuf.raw(val=v2, length=n2),
                            control)
    assert r == qp.ArgsAndKwargs([
        (v1 ^ v2) % 2**n1 if control else v1,
        v2,
        control
    ], {})


def test_function():
    for _ in range(10):
        n1 = random.randint(0, 100)
        n2 = random.randint(0, n1)
        v1 = random.randint(0, 2**n1 - 1)
        v2 = random.randint(0, 2**n2 - 1)
        assert_xors_correctly(n1, n2, v1, v2)

    for n1 in range(3):
        for n2 in range(n1 + 1):
            for v1 in range(1 << n1):
                for v2 in range(1 << n2):
                    assert_xors_correctly(n1, n2, v1, v2)


def test_xor_equal_gate_circuit():
    with qp.Sim(enforce_release_at_zero=False):
        with qp.LogCirqCircuit() as circuit:
            with qp.qmanaged_int(bits=3, name='a') as a:
                with qp.qmanaged_int(bits=4, name='t') as t:
                    with qp.qmanaged(qp.Qubit(name='_c')) as c:
                        qp.emit(
                            qp.XorEqual(lvalue=t, mask=a))
                        qp.emit(
                            qp.XorEqual(lvalue=t, mask=a).controlled_by(c))

    cirq.testing.assert_has_diagram(circuit, r"""
_c: -----------------@---@---@---
                     |   |   |
a[0]: ---@-----------@---|---|---
         |           |   |   |
a[1]: ---|---@-------|---@---|---
         |   |       |   |   |
a[2]: ---|---|---@---|---|---@---
         |   |   |   |   |   |
t[0]: ---X---|---|---X---|---|---
             |   |       |   |
t[1]: -------X---|-------X---|---
                 |           |
t[2]: -----------X-----------X---
        """, use_unicode_characters=False)


def test_xor_equal_gate_circuit_2():
    with qp.Sim(enforce_release_at_zero=False):
        with qp.LogCirqCircuit() as circuit:
            with qp.qmanaged_int(bits=3, name='a') as a:
                with qp.qmanaged_int(bits=4, name='t') as t:
                    with qp.qmanaged(qp.Qubit(name='_c')) as c:
                        t ^= a
                        t ^= a & qp.controlled_by(c)

    cirq.testing.assert_has_diagram(circuit, r"""
_c: -----------------@---@---@---
                     |   |   |
a[0]: ---@-----------@---|---|---
         |           |   |   |
a[1]: ---|---@-------|---@---|---
         |   |       |   |   |
a[2]: ---|---|---@---|---|---@---
         |   |   |   |   |   |
t[0]: ---X---|---|---X---|---|---
             |   |       |   |
t[1]: -------X---|-------X---|---
                 |           |
t[2]: -----------X-----------X---
        """, use_unicode_characters=False)
