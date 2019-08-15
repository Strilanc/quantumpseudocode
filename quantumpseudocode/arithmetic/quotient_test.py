import random

import quantumpseudocode as qp


def test_do_init_small_quotient():
    qp.testing.assert_semi_quantum_func_is_consistent(
        qp.arithmetic.do_init_small_quotient,
        fuzz_space={
            'divisor': lambda: random.randint(1, 1023),
            'total': lambda divisor: qp.IntBuf.random(divisor.bit_length() + random.randint(0, 3)),
            'lvalue': lambda divisor, total:
                qp.IntBuf.raw(val=0, length=len(total) - divisor.bit_length() + random.randint(1, 3)),
            'forward': True,
            'transfer': [False, True],
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
            'transfer': False,
        },
        fuzz_count=100)

    qp.testing.assert_semi_quantum_func_is_consistent(
        qp.arithmetic.do_init_small_quotient,
        fuzz_space={
            'divisor': lambda: random.randint(1, 1023),
            'total': lambda divisor: qp.IntBuf.random(
                length=(divisor - 1).bit_length() + random.randint(0, 3),
                val=range(divisor)),
            'lvalue': lambda divisor, total: qp.IntBuf.random(
                val=range((1 << len(total)) // divisor),
                length=((1 << len(total)) // divisor).bit_length()),
            'forward': False,
            'transfer': True,
        },
        fuzz_count=100)

def test_do_div_rem():
    n = 10

    qp.testing.assert_semi_quantum_func_is_consistent(
        qp.arithmetic.do_div_rem,
        fuzz_space={
            'divisor': lambda: random.randint(1, 1 << n),
            'lvalue_total_then_remainder': lambda divisor:
                qp.IntBuf.random(divisor.bit_length() + random.randint(0, n)),
            'lvalue_quotient': lambda divisor, lvalue_total_then_remainder:
                qp.IntBuf.raw(
                    val=0,
                    length=len(lvalue_total_then_remainder) - divisor.bit_length() + random.randint(1, n)),
            'forward': True,
        },
        fuzz_count=3)

    qp.testing.assert_semi_quantum_func_is_consistent(
        qp.arithmetic.do_div_rem,
        fuzz_space={
            'divisor': lambda: random.randint(1, 1 << n),
            'lvalue_total_then_remainder': lambda divisor: qp.IntBuf.random(
                length=(divisor - 1).bit_length() + random.randint(0, n),
                val=range(divisor)),
            'lvalue_quotient': lambda divisor, lvalue_total_then_remainder: qp.IntBuf.random(
                val=range((1 << len(lvalue_total_then_remainder)) // divisor),
                length=((1 << len(lvalue_total_then_remainder)) // divisor).bit_length()),
            'forward': False,
        },
        fuzz_count=3)
