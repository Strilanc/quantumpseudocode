import functools
import itertools
import random

import pytest

import quantumpseudocode as qp
from .plus_equal_product import *


methods = [
    plus_equal_product_builtin,
    plus_equal_product_iter_classical,
    plus_equal_product_iter_quantum,
    plus_equal_product_single_lookup,
    plus_equal_product_windowed_2,
    plus_equal_product_windowed_4,
    plus_equal_product_windowed_lg,
]

cases = [
    {'n': 10, 't': 5, 'k': 7, 'y': 13},
    {'n': 4, 't': 5, 'k': 7, 'y': 13},
    {'n': 1, 't': 1, 'k': 1, 'y': 1},
    {'k': 847561784, 'n': 30, 't': 771685281, 'y': 541683290},
    {'k': 2, 'n': 2, 't': 0, 'y': 2},
    {'k': 2, 'n': 2, 't': 1, 'y': 2},
    {
        'n': 30,
        't': random.randint(0, 2**30-1),
        'k': random.randint(0, 2**30-1),
        'y': random.randint(0, 2**30-1)
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
    y = case['y']

    final_state = qp.testing.sim_call(
        method,
        target=qp.IntBuf.raw(val=t, length=n),
        k=k,
        y=y)
    assert final_state == qp.ArgsAndKwargs([], {
        'target': (t + k * y) % 2**n,
        'k': k,
        'y': y
    })
