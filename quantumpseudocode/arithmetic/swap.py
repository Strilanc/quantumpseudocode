from typing import Union

import quantumpseudocode as qp


def swap(a: Union[qp.Qureg, qp.Quint, qp.QuintMod],
         b: Union[qp.Qureg, qp.Quint, qp.QuintMod]) -> None:
    if isinstance(a, qp.QuintMod):
        a = a[:]
    if isinstance(b, qp.QuintMod):
        b = b[:]
    a ^= b
    b ^= a
    a ^= b
