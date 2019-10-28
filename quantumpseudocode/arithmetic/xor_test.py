import random

import cirq

import quantumpseudocode as qp


def test_do():
    qp.testing.assert_semi_quantum_func_is_consistent(
        qp.arithmetic.do_xor,
        fuzz_space={
            'lvalue': lambda: qp.IntBuf.random(range(0, 6)),
            'mask': lambda lvalue: random.randint(0, (1 << len(lvalue)) - 1),
        },
        fuzz_count=100)

    qp.testing.assert_semi_quantum_func_is_consistent(
        qp.arithmetic.do_xor_const,
        fuzz_space={
            'lvalue': lambda: qp.IntBuf.random(range(0, 6)),
            'mask': lambda: random.randint(0, 511),
        },
        fuzz_count=100)


def test_xor_equal_gate_circuit():
    with qp.Sim(enforce_release_at_zero=False):
        with qp.LogCirqCircuit() as circuit:
            with qp.qmanaged_int(bits=3, name='a') as a:
                with qp.qmanaged_int(bits=4, name='t') as t:
                    with qp.qmanaged(name='_c') as c:
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
