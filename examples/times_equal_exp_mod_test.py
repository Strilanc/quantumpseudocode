import functools
import itertools
import random

import pytest

import quantumpseudocode as qp
from .times_equal_exp_mod import *


methods = [
    times_equal_exp_mod_window_1_1,
    times_equal_exp_mod_window_2_3,
]

cases = [
    {'N': 11, 'k': 5, 'e': 7, 't': 1},
    {'N': 213, 'k': 29, 'e': 1111, 't': 22},
]


@pytest.mark.parametrize(
    'method,case',
    itertools.product(methods, cases)
)
def test_correct_result(method, case):
    modulus = case['N']
    t = case['t']
    k = case['k']
    e = case['e']
    t %= modulus
    k %= modulus

    final_state = qp.testing.sim_call(
        method,
        target=qp.testing.ModInt(val=t, modulus=modulus),
        k=k,
        e=e)
    assert final_state == qp.ArgsAndKwargs([], {
        'target': (t * k ** e) % modulus,
        'k': k,
        'e': e
    })
