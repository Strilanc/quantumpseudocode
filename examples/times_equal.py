from quantumpseudocode import *


def times_equal_builtin(target: Quint, k: int):
    assert k & 1
    target *= k


def times_equal_classic(target: Quint, k: int):
    assert k % 2 == 1  # Even factors aren't reversible.
    k %= 2**len(target)  # Normalize factor.
    for i in range(len(target))[::-1]:
        target[i + 1:] += (k >> 1) & controlled_by(target[i])


def times_equal_windowed(target: Quint, k: int, window: int):
    assert k % 2 == 1  # Even factors aren't reversible.
    k %= 2**len(target)  # Normalize factor.
    if k == 1:
        return
    table = LookupTable([
        (j * k) >> window
        for j in range(2**window)
    ])
    for i in range(0, len(target), window)[::-1]:
        w = target[i:i + window]
        target[i + window:] += table[w]

        # Recursively fix up the window.
        times_equal_windowed(w, k, window=1)


def times_equal_windowed_2(target: Quint, k: int):
    times_equal_windowed(target, k, 2)


def times_equal_windowed_4(target: Quint, k: int):
    times_equal_windowed(target, k, 4)


def times_equal_windowed_lg(target: Quint, k: int):
    w = max(1, ceil_lg2(len(target)))
    times_equal_windowed(target, k, w)
