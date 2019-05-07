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

    def inv_mul(target: qp.Quint, k: int):
        with qp.invert():
            target *= k

    final_state = qp.testing.sim_call(
        mul,
        target=qp.IntBuf.raw(val=t, length=n),
        k=k)
    assert final_state == qp.ArgsAndKwargs([], {
        'target': t * k % 2**n,
        'k': k,
    })

    final_state = qp.testing.sim_call(
        inv_mul,
        target=qp.IntBuf.raw(val=t * k % 2**n, length=n),
        k=k)
    assert final_state == qp.ArgsAndKwargs([], {
        'target': t,
        'k': k,
    })
