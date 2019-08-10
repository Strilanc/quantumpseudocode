import quantumpseudocode as qp
from quantumpseudocode.ops import semi_quantum


def do_classical_multiply_add(*,
                              lvalue: 'qp.IntBuf',
                              quantum_factor: int,
                              const_factor: int,
                              forward: bool = True):
    if forward:
        lvalue += quantum_factor * const_factor
    else:
        lvalue -= quantum_factor * const_factor


@semi_quantum(classical=do_classical_multiply_add, alloc_prefix='_mult_add_')
def do_multiply_add(*,
                    control: 'qp.Qubit.Control' = True,
                    lvalue: 'qp.Quint',
                    quantum_factor: 'qp.Quint.Borrowed',
                    const_factor: int,
                    forward: bool = True):
        for i, q in enumerate(quantum_factor):
            with qp.hold((const_factor << i) & qp.controlled_by(q & control)) as offset:
                if forward:
                    lvalue += offset
                else:
                    lvalue -= offset
