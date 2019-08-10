import quantumpseudocode as qp
from quantumpseudocode.ops import semi_quantum


def do_multiplication_classical(*,
                                lvalue: qp.IntBuf,
                                factor: int,
                                forward: bool = True):
    assert factor & 1, "Irreversible multiplication"
    if forward:
        lvalue *= factor
    else:
        lvalue *= qp.modular_multiplicative_inverse(factor, 1 << len(lvalue))


@semi_quantum(alloc_prefix='_mul_',
              classical=do_multiplication_classical)
def do_multiplication(*,
                      control: qp.Qubit.Control = True,
                      lvalue: qp.Quint,
                      factor: int,
                      forward: bool = True):
    assert factor & 1, "Irreversible multiplication"
    assert isinstance(control, qp.QubitIntersection) and len(control.qubits) <= 1
    if forward:
        for i in range(len(lvalue))[::-1]:
            lvalue[i + 1:] += (factor >> 1) & qp.controlled_by(control & lvalue[i])
    else:
        for i in range(len(lvalue)):
            lvalue[i + 1:] -= (factor >> 1) & qp.controlled_by(control & lvalue[i])
