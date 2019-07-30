from typing import List, Union

import cirq

import quantumpseudocode as qp
from quantumpseudocode.ops import Operation, semi_quantum


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
    with qp.invert():
        do_addition(control=control, lvalue=lvalue, offset=offset, carry_in=carry_in)


@cirq.value_equality()
class PlusEqual(Operation):
    def __init__(self, lvalue: qp.Quint, offset: qp.Quint, carry_in: qp.Qubit):
        self.lvalue = lvalue
        self.offset = offset
        self.carry_in = carry_in

    def _value_equality_values_(self):
        return self.lvalue, self.offset, self.carry_in

    def emit_ops(self, controls: 'qp.QubitIntersection'):
        do_addition(control=controls, lvalue=self.lvalue, offset=self.offset, carry_in=self.carry_in)

    def mutate_state(self, sim_state: 'qp.ClassicalSimState', forward: bool) -> None:
        if forward:
            do_addition.sim(sim_state, lvalue=self.lvalue, offset=self.offset, carry_in=self.carry_in)
        else:
            do_subtraction.sim(sim_state, lvalue=self.lvalue, offset=self.offset, carry_in=self.carry_in)

    def __str__(self):
        return '{} += {} + {}'.format(self.lvalue, self.offset, self.carry_in)

    def __repr__(self):
        return 'qp.PlusEqual({!r}, {!r}, {!r})'.format(self.lvalue, self.offset, self.carry_in)


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
