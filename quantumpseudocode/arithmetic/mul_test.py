import random

import pytest

import quantumpseudocode as qp


@pytest.mark.parametrize('case', [
    {'n': 5, 't': 2, 'k': 3},
    {
        'n': 10,
        't': random.randint(0, 2**10-1),
        'k': random.randint(0, 2**10-1) | 1,
    },
    {
        'n': 20,
        't': random.randint(0, 2**20 - 1),
        'k': random.randint(0, 2**20 - 1) | 1,
    },
])
def test_correct_result(case):
    n = case['n']
    t = case['t']
    k = case['k']

    def mul(target: qp.Quint, k: int):
        target *= k

    final_state = qp.testing.sim_call(
        mul,
        target=qp.IntBuf.raw(val=t, length=n),
        k=k)
    assert final_state == qp.ArgsAndKwargs([], {
        'target': t * k % 2**n,
        'k': k,
    })


def test_quantum_classical_consistent():
    qp.testing.assert_semi_quantum_func_is_consistent(
        qp.arithmetic.do_multiplication,
        fuzz_space={
            'lvalue': lambda: qp.IntBuf.random(range(0, 6)),
            'factor': lambda: random.randint(0, 31) * 2 + 1,
            'forward': [False, True],
        },
        fuzz_count=100)
