import random

import quantumpseudocode as qp


def test_quantum_classical_consistent():
    qp.testing.assert_semi_quantum_func_is_consistent(
        qp.arithmetic.do_plus_product,
        fuzz_space={
            'lvalue': lambda: qp.IntBuf.random(range(0, 6)),
            'quantum_factor': lambda: random.randint(0, 99),
            'const_factor': lambda: random.randint(0, 99),
            'forward': [False, True],
        },
        fuzz_count=100)
