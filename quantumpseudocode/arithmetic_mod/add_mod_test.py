import random

import quantumpseudocode as qp


def test_quantum_classical_consistent():
    qp.testing.assert_semi_quantum_func_is_consistent(
        qp.arithmetic_mod.do_plus_const_mod,
        fuzz_space={
            'modulus': lambda: random.randint(1, 63),
            'lvalue': lambda modulus: qp.IntBuf.random_mod(modulus),
            'offset': lambda modulus: random.randint(-3 * modulus, 3 * modulus),
            'forward': [False, True],
        },
        fuzz_count=100)

    qp.testing.assert_semi_quantum_func_is_consistent(
        qp.arithmetic_mod.do_plus_mod,
        fuzz_space={
            'modulus': lambda: random.randint(1, 63),
            'lvalue': lambda modulus: qp.IntBuf.random_mod(modulus),
            'offset': lambda modulus: random.randint(0, modulus - 1),
            'forward': [False, True],
        },
        fuzz_count=100)
