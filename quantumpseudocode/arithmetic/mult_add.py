import quantumpseudocode as qp
from quantumpseudocode.ops import semi_quantum


def do_plus_product_classical(*,
                              lvalue: qp.IntBuf,
                              quantum_factor: qp.IntBuf,
                              const_factor: int,
                              forward: bool = True):
    if forward:
        lvalue += int(quantum_factor) * const_factor
    else:
        lvalue -= int(quantum_factor) * const_factor


@semi_quantum(alloc_prefix='_plus_mul_', classical=do_plus_product_classical)
def do_plus_product(*,
                    control: qp.Qubit.Control = True,
                    lvalue: qp.Quint,
                    quantum_factor: qp.Quint.Borrowed,
                    const_factor: int,
                    forward: bool = True):
    assert isinstance(control, qp.QubitIntersection) and len(control.qubits) <= 1
    assert isinstance(lvalue, qp.Quint)
    assert isinstance(quantum_factor, qp.Quint)
    assert isinstance(const_factor, int)
    for i, q in enumerate(quantum_factor):
        with qp.hold(const_factor & qp.controlled_by(q & control)) as offset:
            if forward:
                lvalue[i:] += offset
            else:
                lvalue[i:] -= offset
