import random

import math

from quantumpseudocode import *


def measure_pow_mod(base: int, exponent: Quint, modulus: int) -> int:
    """Measure `base**exponent % modulus`, and nothing else."""
    assert modular_multiplicative_inverse(base, modulus) is not None

    n = ceil_lg2(modulus)  # Problem size in bits.
    g = ceil_lg2(n) // 3 + 1  # Group size for lookups.
    g0 = g
    g1 = g
    coset_len = n + 2 * ceil_lg2(n) + 10  # Extra bits to suppress deviation.

    # Initialize coset registers to starting state (a=1, b=0).
    a = make_coset_register(value=1, length=coset_len, modulus=modulus)
    b = make_coset_register(value=0, length=coset_len, modulus=modulus)

    # Perform a *= base**exponent (mod modulus) using b as workspace.
    for i in range(0, len(exponent), g0):
        exp_index = exponent[i:i+g0]
        ks = [pow(base, 2**i * e, modulus) for e in range(2**g0)]
        ks_inv = [modular_multiplicative_inverse(k, modulus) for k in ks]

        # Perform b += a * k (mod modulus).
        # Maps (x, 0) into (x, x*k).
        for j in range(0, coset_len, g1):
            mul_index = a[j:j + g1]
            table = LookupTable(
                [(k * f * 2**j) % modulus for f in range(2**len(mul_index))]
                for k in ks
            )
            b += table[exp_index, mul_index]

        # Perform a -= b * inv(k) (mod modulus).
        # Maps (x, x*k) into (0, x*k).
        for j in range(0, coset_len, g1):
            mul_index = b[j:j + g1]
            table = LookupTable(
                [(k_inv * f * 2**j) % modulus for f in range(2**len(mul_index))]
                for k_inv in ks_inv
            )
            a -= table[exp_index, mul_index]

        # Swap.
        # Maps (0, x*k) into (x*k, 0).
        a, b = b, a

    result = measure(a)
    qfree(a, dirty=True)
    qfree(b, dirty=True)

    return result % modulus


def make_coset_register(value: int, length: int, modulus: int) -> Quint:
    reg = qalloc_int(bits=length, name='coset')
    reg ^= value % modulus

    # Add coherent multiple of modulus into reg.
    pad_bits = length - modulus.bit_length()
    for i in range(pad_bits):
        offset = modulus << i
        q = qalloc(x_basis=True)
        reg += offset & controlled_by(q)
        qfree(q, equivalent_expression=reg >= offset)

    return reg
