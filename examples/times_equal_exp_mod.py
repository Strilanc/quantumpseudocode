from quantumpseudocode import *


def times_equal_exp_mod(target: QuintMod,
                        k: int,
                        e: Quint,
                        e_window: int,
                        m_window: int):
    """Performs `target *= k**e`, modulo the target's modulus."""
    N = target.modulus
    ki = modular_multiplicative_inverse(k, N)
    assert ki is not None

    a = target
    b = qalloc_int_mod(modulus=N)

    for i in range(0, len(e), e_window):
        ei = e[i:i + e_window]

        # Exponent-indexed factors and inverse factors.
        kes = [pow(k, 2**i * x, N)
               for x in range(2**e_window)]
        kes_inv = [modular_multiplicative_inverse(x, N)
                   for x in kes]

        # Perform b += a * k_e (mod modulus).
        # Maps (x, 0) into (x, x*k_e).
        for j in range(0, len(a), m_window):
            mi = a[j:j + m_window]
            table = LookupTable(
                [(ke * f * 2**j) % N
                 for f in range(2**len(mi))]
                for ke in kes)
            b += table[ei, mi]

        # Perform a -= b * inv(k_e) (mod modulus).
        # Maps (x, x*k_e) into (0, x*k_e).
        for j in range(0, len(a), m_window):
            mi = b[j:j + m_window]
            table = LookupTable(
                [(ke_inv * f * 2**j) % N
                 for f in range(2**len(mi))]
                for ke_inv in kes_inv)
            a -= table[ei, mi]

        # Relabelling swap. Maps (0, x*k_e) into (x*k_e, 0).
        a, b = b, a

    # Xor swap result into correct register if needed.
    if a is not target:
        swap(a, b)
        a, b = b, a
    qfree(b)


def times_equal_exp_mod_window_1_1(target: QuintMod,
                                   k: int,
                                   e: Quint):
    return times_equal_exp_mod(target, k, e, 1, 1)


def times_equal_exp_mod_window_2_3(target: QuintMod,
                                   k: int,
                                   e: Quint):
    return times_equal_exp_mod(target, k, e, 2, 3)
