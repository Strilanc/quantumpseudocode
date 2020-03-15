import random

import cirq

import quantumpseudocode as qp


def test_quantum_classical_consistent():
    qp.testing.assert_semi_quantum_func_is_consistent(
        qp.arithmetic.do_xor_const,
        fuzz_space={
            'lvalue': lambda: qp.IntBuf.random(range(0, 6)),
            'mask': lambda: random.randint(0, 63),
        },
        fuzz_count=100)

    qp.testing.assert_semi_quantum_func_is_consistent(
        qp.arithmetic.do_xor,
        fuzz_space={
            'lvalue': lambda: qp.IntBuf.random(range(0, 6)),
            'mask': lambda: random.randint(0, 63),
        },
        fuzz_count=100)


def test_xor_equal_gate_circuit():
    with qp.Sim(enforce_release_at_zero=False):
        with qp.LogCirqCircuit() as circuit:
            with qp.qalloc(len=3, name='a') as a:
                with qp.qalloc(len=4, name='t') as t:
                    with qp.qalloc(name='_c') as c:
                        qp.arithmetic.do_xor(lvalue=t, mask=a)
                        qp.arithmetic.do_xor(lvalue=t, mask=a, control=c)

    cirq.testing.assert_has_diagram(circuit, r"""
_c: ---------------------alloc---------------@---@---@---release-----------------------
                                             |   |   |
a[0]: ---alloc-------------------@-----------@---|---|-----------------------release---
         |                       |           |   |   |                       |
a[1]: ---alloc-------------------|---@-------|---@---|-----------------------release---
         |                       |   |       |   |   |                       |
a[2]: ---alloc-------------------|---|---@---|---|---@-----------------------release---
                                 |   |   |   |   |   |
t[0]: -----------alloc-----------X---|---|---X---|---|-------------release-------------
                 |                   |   |       |   |             |
t[1]: -----------alloc---------------X---|-------X---|-------------release-------------
                 |                       |           |             |
t[2]: -----------alloc-------------------X-----------X-------------release-------------
                 |                                                 |
t[3]: -----------alloc---------------------------------------------release-------------
        """, use_unicode_characters=False)


def test_xor_equal_gate_circuit_2():
    with qp.Sim(enforce_release_at_zero=False):
        with qp.LogCirqCircuit() as circuit:
            with qp.qalloc(len=3, name='a') as a:
                with qp.qalloc(len=4, name='t') as t:
                    with qp.qalloc(name='_c') as c:
                        t ^= a
                        t ^= a & qp.controlled_by(c)

    cirq.testing.assert_has_diagram(circuit, r"""
_c: ---------------------alloc---------------@---@---@---release-----------------------
                                             |   |   |
a[0]: ---alloc-------------------@-----------@---|---|-----------------------release---
         |                       |           |   |   |                       |
a[1]: ---alloc-------------------|---@-------|---@---|-----------------------release---
         |                       |   |       |   |   |                       |
a[2]: ---alloc-------------------|---|---@---|---|---@-----------------------release---
                                 |   |   |   |   |   |
t[0]: -----------alloc-----------X---|---|---X---|---|-------------release-------------
                 |                   |   |       |   |             |
t[1]: -----------alloc---------------X---|-------X---|-------------release-------------
                 |                       |           |             |
t[2]: -----------alloc-------------------X-----------X-------------release-------------
                 |                                                 |
t[3]: -----------alloc---------------------------------------------release-------------
        """, use_unicode_characters=False)
