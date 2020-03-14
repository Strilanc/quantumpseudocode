from typing import List, Union

import quantumpseudocode as qp
from quantumpseudocode.ops import semi_quantum


def do_addition_classical(*,
                          lvalue: qp.IntBuf,
                          offset: int,
                          carry_in: bool = False):
    lvalue += offset + carry_in


def do_subtraction_classical(*,
                             lvalue: qp.IntBuf,
                             offset: int,
                             carry_in: bool = False):
    lvalue -= offset + carry_in


@semi_quantum(alloc_prefix='_add_',
              classical=do_addition_classical)
def do_addition(*,
                control: qp.Qubit.Control = True,
                lvalue: qp.Quint,
                offset: qp.Quint.Borrowed,
                carry_in: qp.Qubit.Borrowed = False):
    assert isinstance(control, qp.QubitIntersection) and len(control.qubits) <= 1
    assert isinstance(lvalue, qp.Quint)
    assert isinstance(offset, qp.Quint)
    assert isinstance(carry_in, qp.Qubit)

    out_len = len(lvalue)

    # Special cases.
    if out_len == 0:
        return
    if out_len == 1:
        if len(offset):
            lvalue[0] ^= offset[0] & control
        lvalue[0] ^= carry_in & control
        return

    with offset.hold_padded_to(out_len - 1) as offset:
        in_len = min(out_len, len(offset))

        # Propagate carry.
        maj_sweep(lvalue, carry_in, offset)

        # Carry output.
        if out_len == in_len + 1:
            lvalue[in_len] ^= offset[in_len - 1] & control

        # Apply and uncompute carries.
        uma_sweep(lvalue, carry_in, offset, control)


@semi_quantum(alloc_prefix='_sub_',
              classical=do_subtraction_classical)
def do_subtraction(*,
                   control: qp.Qubit.Control = True,
                   lvalue: qp.Quint,
                   offset: qp.Quint.Borrowed,
                   carry_in: qp.Qubit.Borrowed = False):
    lvalue ^= -1
    do_addition(control=control, lvalue=lvalue, offset=offset, carry_in=carry_in)
    lvalue ^= -1


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
