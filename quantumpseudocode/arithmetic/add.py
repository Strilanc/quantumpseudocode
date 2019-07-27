from typing import List, Union

import quantumpseudocode as qp
from quantumpseudocode.ops import Op


class PlusEqual(Op):
    @staticmethod
    def alloc_prefix():
        return '_add_'

    @staticmethod
    def biemulate(forward: bool,
                  *,
                  lvalue: 'qp.IntBuf',
                  offset: int,
                  carry_in: bool):
        sign = 1 if forward else -1
        lvalue += (offset + carry_in) * sign

    @staticmethod
    def do(controls: 'qp.QubitIntersection',
           *,
           lvalue: qp.Quint,
           offset: qp.Quint,
           carry_in: qp.Qubit):
        out_len = len(lvalue)

        # Special cases.
        if out_len == 0:
            return
        if out_len == 1:
            if len(offset):
                lvalue[0] ^= offset[0] & controls
            lvalue[0] ^= carry_in & controls
            return

        with qp.pad(offset, min_len=out_len - 1) as offset:
            in_len = min(out_len, len(offset))

            # Propagate carry.
            maj_sweep(lvalue, carry_in, offset)

            # Carry output.
            if out_len == in_len + 1:
                lvalue[in_len] ^= offset[in_len - 1] & controls

            # Apply and uncompute carries.
            uma_sweep(lvalue, carry_in, offset, controls)

    @staticmethod
    def describe(*, lvalue, offset, carry_in):
        return '{} += {} + {}'.format(lvalue, offset, carry_in)


def maj_sweep(lvalue: Union[qp.Quint, List[qp.Qubit], qp.Qureg],
              carry: qp.Qubit,
              offset: Union[qp.Quint, List[qp.Qubit], qp.Qureg]):
    out_len = len(lvalue)
    carry_then_offset = [carry] + list(offset)
    in_len = min(out_len, len(offset))

    for i in range(in_len):
        a = carry_then_offset[i]
        b = lvalue[i]
        c = offset[i]

        # Maj.
        a ^= c
        b ^= c
        c ^= a & b


def uma_sweep(lvalue: Union[qp.Quint, List[qp.Qubit], qp.Qureg],
              carry: qp.Qubit,
              offset: Union[qp.Quint, List[qp.Qubit], qp.Qureg],
              controls: qp.QubitIntersection):
    out_len = len(lvalue)
    carry_then_offset = [carry] + list(offset)
    in_len = min(out_len, len(offset))

    for i in range(in_len)[::-1]:
        a = carry_then_offset[i]
        b = lvalue[i]
        c = offset[i]

        # Uma.
        c ^= a & b
        b ^= a & controls
        b ^= c
        a ^= c
