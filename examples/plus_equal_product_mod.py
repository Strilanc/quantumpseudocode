from quantumpseudocode import *


def plus_equal_product_mod_classic(target: QuintMod,
                                   k: int,
                                   y: Quint):
    N = target.modulus
    for i in range(len(y)):
        with controlled_by(y[i]):
            target += (k * 2**i % N)


def plus_equal_product_mod_windowed(target: QuintMod,
                                    k: int,
                                    y: Quint,
                                    window: int):
    N = target.modulus
    for i in range(0, len(y), window):
        w = y[i:i + window]
        table = LookupTable([
            j * k * 2**i % N
            for j in range(2**window)
        ])
        target += table[w]


def plus_equal_product_mod_windowed_2(target: QuintMod,
                                      k: int,
                                      y: Quint):
    plus_equal_product_mod_windowed(target, k, y, 2)


def plus_equal_product_mod_windowed_4(target: QuintMod,
                                      k: int,
                                      y: Quint):
    plus_equal_product_mod_windowed(target, k, y, 4)


def plus_equal_product_mod_windowed_lg(target: QuintMod,
                                       k: int,
                                       y: Quint):
    w = max(1, ceil_lg2(len(target)))
    plus_equal_product_mod_windowed(target, k, y, w)
