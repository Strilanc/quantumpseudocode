from quantumpseudocode import *


def plus_equal_product_builtin(target: Quint, k: int, y: Quint):
    target += k * y


def plus_equal_product_iter_quantum(target: Quint, k: int, y: Quint):
    for i in range(len(y)):
        with controlled_by(y[i]):
            target[i:] += k


def plus_equal_product_iter_classical(target: Quint, k: int, y: Quint):
    for i in range(k.bit_length()):
        if (k >> i) & 1:
            target[i:] += y
