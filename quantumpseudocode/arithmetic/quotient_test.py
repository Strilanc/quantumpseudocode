import random

import quantumpseudocode as qp


def test_do():
    qp.testing.assert_semi_quantum_func_is_consistent(
        qp.arithmetic.do_init_small_quotient,
        fuzz_space={
            'divisor': lambda: random.randint(1, 1023),
            'total': lambda divisor: qp.IntBuf.random(divisor.bit_length() + random.randint(0, 3)),
            'lvalue': lambda divisor, total:
                qp.IntBuf.raw(val=0, length=len(total) - divisor.bit_length() + random.randint(1, 3)),
            'forward': True,
        },
        fuzz_count=100)

    qp.testing.assert_semi_quantum_func_is_consistent(
        qp.arithmetic.do_init_small_quotient,
        fuzz_space={
            'divisor': lambda: random.randint(1, 1023),
            'total': lambda divisor: qp.IntBuf.random(divisor.bit_length() + random.randint(0, 3)),
            'lvalue': lambda divisor, total: qp.IntBuf.raw(
                val=int(total) // divisor,
                length=len(total) - divisor.bit_length() + random.randint(1, 3)),
            'forward': False,
        },
        fuzz_count=100)
