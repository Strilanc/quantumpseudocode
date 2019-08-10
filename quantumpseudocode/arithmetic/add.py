import quantumpseudocode as qp
from quantumpseudocode.ops import semi_quantum


def do_addition_classical(*,
                          lvalue: qp.IntBuf,
                          offset: int,
                          carry_in: bool = False,
                          forward: bool = True):
    if forward:
        lvalue += offset + carry_in
    else:
        lvalue -= offset + carry_in


@semi_quantum(alloc_prefix='_add_',
              classical=do_addition_classical)
def do_addition(*,
                control: qp.Qubit.Control = True,
                lvalue: qp.Quint,
                offset: qp.Quint.Borrowed,
                carry_in: qp.Qubit.Borrowed = False,
                forward: bool = True):
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
        if forward:
            maj_sweep(lvalue, carry_in, offset)
        else:
            uma_sweep(lvalue, carry_in, offset, control, forward=False)

        # Carry output.
        if out_len == in_len + 1:
            lvalue[in_len] ^= offset[in_len - 1] & control

        # Apply and uncompute carries.
        if forward:
            uma_sweep(lvalue, carry_in, offset, control)
        else:
            maj_sweep(lvalue, carry_in, offset, forward=False)


def maj_sweep(lvalue: qp.Quint,
              carry: qp.Qubit,
              offset: qp.Quint,
              forward: bool = True):
    out_len = len(lvalue)
    carry_then_offset = [carry] + list(offset)
    in_len = min(out_len, len(offset))

    for i in range(in_len)[::+1 if forward else -1]:
        a = carry_then_offset[i]
        b = lvalue[i]
        c = offset[i]

        # Maj.
        if forward:
            a ^= c
            b ^= c
            c ^= a & b
        else:
            c ^= a & b
            b ^= c
            a ^= c


def uma_sweep(lvalue: qp.Quint,
              carry: qp.Qubit,
              offset: qp.Quint,
              control: qp.QubitIntersection,
              forward: bool = True):
    out_len = len(lvalue)
    carry_then_offset = [carry] + list(offset)
    in_len = min(out_len, len(offset))

    for i in range(in_len)[::-1 if forward else +1]:
        a = carry_then_offset[i]
        b = lvalue[i]
        c = offset[i]

        # Uma.
        if forward:
            c ^= a & b
            b ^= a & control
            b ^= c
            a ^= c
        else:
            a ^= c
            b ^= c
            b ^= a & control
            c ^= a & b
