import quantumpseudocode as qp
from quantumpseudocode.ops import semi_quantum


def do_classical_xor(*, lvalue: 'qp.IntBuf', mask: int):
    lvalue ^= mask


@semi_quantum(classical=do_classical_xor)
def do_xor_const(*,
                 lvalue: 'qp.Quint',
                 mask: int,
                 control: 'qp.Qubit.Control' = True):
    assert isinstance(control, qp.QubitIntersection) and len(control.qubits) <= 1
    targets = []
    for i, q in enumerate(lvalue):
        if mask & (1 << i):
            targets.append(q)
    qp.emit(qp.Toggle(lvalue=qp.RawQureg(targets)).controlled_by(control))


@semi_quantum(classical=do_classical_xor)
def do_xor(*,
           lvalue: 'qp.Quint',
           mask: 'qp.Quint.Borrowed',
           control: 'qp.Qubit.Control' = True):
    assert isinstance(control, qp.QubitIntersection) and len(control.qubits) <= 1
    assert isinstance(mask, qp.Quint)
    assert len(mask) <= len(lvalue)
    for q, m in zip(lvalue, mask):
        qp.emit(qp.Toggle(lvalue=qp.RawQureg([q])).controlled_by(m & control))
