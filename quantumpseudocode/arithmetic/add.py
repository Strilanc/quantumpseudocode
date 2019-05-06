from typing import List, Union

import quantumpseudocode
from quantumpseudocode.ops.signature_gate import SignatureGate


class _PlusEqualGateClass(SignatureGate):
    def register_name_prefix(self):
        return '_add_'

    def emulate(self,
                forward: bool,
                *,
                lvalue: 'quantumpseudocode.Mutable[int]',
                offset: int,
                carry_in: bool):
        lvalue.val += (offset + carry_in) * (1 if forward else -1)

    def do(self,
           controls: 'quantumpseudocode.QubitIntersection',
           *,
           lvalue: quantumpseudocode.Quint,
           offset: quantumpseudocode.Quint,
           carry_in: quantumpseudocode.Qubit):
        out_len = len(lvalue)

        # Special cases.
        if out_len == 0:
            return
        if out_len == 1:
            if len(offset):
                lvalue[0] ^= offset[0]
            lvalue[0] ^= carry_in
            return

        with quantumpseudocode.pad(offset, min_len=out_len - 1) as offset:
            in_len = min(out_len, len(offset))

            # Propagate carry.
            maj_sweep(lvalue, carry_in, offset)

            # Carry output.
            if out_len == in_len + 1:
                lvalue[in_len] ^= offset[in_len - 1] & controls

            # Apply and uncompute carries.
            uma_sweep(lvalue, carry_in, offset, controls)

    def describe(self, lvalue, offset, carry_in):
        return 'ADD {} += {} + {}'.format(lvalue, offset, carry_in)

    def __repr__(self):
        return 'quantumpseudocode.PlusEqualGate'


def maj_sweep(lvalue: Union[quantumpseudocode.Quint, List[quantumpseudocode.Qubit], quantumpseudocode.Qureg],
              carry: quantumpseudocode.Qubit,
              offset: Union[quantumpseudocode.Quint, List[quantumpseudocode.Qubit], quantumpseudocode.Qureg]):
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


def uma_sweep(lvalue: Union[quantumpseudocode.Quint, List[quantumpseudocode.Qubit], quantumpseudocode.Qureg],
              carry: quantumpseudocode.Qubit,
              offset: Union[quantumpseudocode.Quint, List[quantumpseudocode.Qubit], quantumpseudocode.Qureg],
              controls: quantumpseudocode.QubitIntersection):
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


PlusEqualGate = _PlusEqualGateClass()
