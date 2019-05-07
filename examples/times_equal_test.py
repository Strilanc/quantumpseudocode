import itertools
import random

import pytest

import quantumpseudocode as qp
from .times_equal import *


methods = [
    times_equal_builtin,
    times_equal_classic,
    times_equal_windowed_2,
    times_equal_windowed_4,
    times_equal_windowed_lg,
]

cases = [
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
]


@pytest.mark.parametrize(
    'method,case',
    itertools.product(methods, cases)
)
def test_correct_result(method, case):
    n = case['n']
    t = case['t']
    k = case['k']

    final_state = qp.testing.sim_call(
        method,
        target=qp.IntBuf.raw(val=t, length=n),
        k=k)
    assert final_state == qp.ArgsAndKwargs([], {
        'target': t * k % 2**n,
        'k': k,
    })
