import random

import math

import pytest

import quantumpseudocode
from .measure_pow_mod import measure_pow_mod, make_coset_register


@pytest.mark.parametrize("exp_len,modulus_len,emulate_additions", [
    (3, 5, False),
    (6, 12, False),
    # (20, 40, True),
    # (25, 60, True),
    # (30, 15, True),
])
def test_integration(exp_len: int, modulus_len: int, emulate_additions: bool):
    with quantumpseudocode.Sim(emulate_additions=emulate_additions):
        exponent = random.randint(0, 1 << exp_len)
        modulus = random.randint(0, 1 << modulus_len) * 2 + 1
        base = 0
        while math.gcd(base, modulus) != 1 or base >= modulus:
            base = random.randint(0, 1 << modulus_len) *  2 + 1

        with quantumpseudocode.hold(exponent) as exp:
            actual = measure_pow_mod(base=base, exponent=exp, modulus=modulus)

    expected = pow(base, exponent, modulus)
    assert actual == expected
