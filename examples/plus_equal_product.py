from quantumpseudocode import *


def plus_equal_product_builtin(target: Quint, k: int, y: Quint):
    target += k * y


def plus_equal_product_iter_quantum(target: Quint, k: int, y: Quint):
    for i in range(len(y)):
        target[i:] += k & controlled_by(y[i])


def plus_equal_product_iter_classical(target: Quint, k: int, y: Quint):
    for i in range(k.bit_length()):
        if (k >> i) & 1:
            target[i:] += y


def plus_equal_product_single_lookup(target: Quint, k: int, y: Quint):
    table = LookupTable([0, k])
    for i in range(len(y)):
        target[i:] += table[y[i]]


def plus_equal_product_windowed(target: Quint,
                                k: int,
                                y: Quint,
                                window: int):
    table = LookupTable([
        i*k
        for i in range(2**window)
    ])
    for i in range(0, len(y), window):
        target[i:] += table[y[i:i+window]]


def plus_equal_product_windowed_2(target: Quint,
                                  k: int,
                                  y: Quint):
    return plus_equal_product_windowed(target, k, y, 2)


def plus_equal_product_windowed_4(target: Quint,
                                  k: int,
                                  y: Quint):
    return plus_equal_product_windowed(target, k, y, 4)


def plus_equal_product_windowed_lg(target: Quint,
                                   k: int,
                                   y: Quint):
    return plus_equal_product_windowed(target, k, y, max(1, ceil_lg2(len(y))))
