import random

import quantumpseudocode as qp


def test_consistent():
    for n in range(6):
        qp.testing.assert_semi_quantum_func_is_consistent(
            qp.arithmetic.do_multiply_add,
            fuzz_space={
                'lvalue': lambda: qp.IntBuf.random(n),
                'quantum_factor': lambda: random.randint(0, (1 << n) - 1),
                'const_factor': lambda: random.randint(0, (1 << n) - 1),
            },
            fuzz_count=10)
