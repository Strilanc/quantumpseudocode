import functools
import itertools
import random

import pytest

import quantumpseudocode as qp
from .plus_equal_product_mod import *


methods = [
    plus_equal_product_mod_classic,
    plus_equal_product_mod_windowed_2,
    plus_equal_product_mod_windowed_4,
    plus_equal_product_mod_windowed_lg,
]

cases = [
    {'N': 10, 't': 5, 'k': 7, 'y': 13},
    {'N': 4, 't': 5, 'k': 7, 'y': 13},
    {'N': 1, 't': 1, 'k': 1, 'y': 1},
    {'k': 847561784, 'N': 30, 't': 771685281, 'y': 541683290},
    {'k': 2, 'N': 2, 't': 0, 'y': 2},
    {'k': 2, 'N': 2, 't': 1, 'y': 2},
    {
        'N': 30,
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
    modulus = case['N']
    t = case['t']
    k = case['k']
    y = case['y']
    t %= modulus
    y %= modulus
    k %= modulus

    final_state = qp.testing.sim_call(
        method,
        target=qp.testing.ModInt(val=t, modulus=modulus),
        k=k,
        y=y)
    assert final_state == qp.ArgsAndKwargs([], {
        'target': (t + k * y) % modulus,
        'k': k,
        'y': y
    })
