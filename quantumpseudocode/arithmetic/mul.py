import quantumpseudocode as qp
from quantumpseudocode.ops import semi_quantum


def do_multiplication_classical(*,
                                lvalue: qp.IntBuf,
                                factor: int,
                                forward: bool = True):
    assert factor % 2 == 1
    if forward:
        lvalue *= factor
    else:
        lvalue *= qp.modular_multiplicative_inverse(factor, 2**len(lvalue))


@semi_quantum(alloc_prefix='_mul_', classical=do_multiplication_classical)
def do_multiplication(*,
                      control: qp.Qubit.Control = True,
                      lvalue: qp.Quint,
                      factor: int,
                      forward: bool = True):
    assert isinstance(control, qp.QubitIntersection) and len(control.qubits) <= 1
    assert isinstance(lvalue, qp.Quint)
    assert isinstance(factor, int)
    assert factor % 2 == 1
    if forward:
        for i in range(len(lvalue))[::-1]:
            c = control & lvalue[i]
            lvalue[i+1:] += (factor >> 1) & qp.controlled_by(c)
    else:
        for i in range(len(lvalue)):
            c = control & lvalue[i]
            lvalue[i+1:] -= (factor >> 1) & qp.controlled_by(c)
