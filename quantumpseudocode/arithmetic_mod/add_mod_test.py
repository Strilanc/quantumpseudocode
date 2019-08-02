import random

import quantumpseudocode as qp


def test_do():
    qp.testing.assert_semi_quantum_func_is_consistent(
        qp.arithmetic_mod.do_add_const_mod,
        fuzz_space={
            'lvalue': qp.IntBufMod.random(range(2, 512)),
            'offset': lambda lvalue: random.choice(range(lvalue.modulus)),
        },
        fuzz_count=100)

    qp.testing.assert_semi_quantum_func_is_consistent(
        qp.arithmetic_mod.do_add_mod,
        fuzz_space={
            'lvalue': qp.IntBufMod.random(range(512)),
            'offset': lambda lvalue: random.choice(range(lvalue.modulus)),
        },
        fuzz_count=100)


