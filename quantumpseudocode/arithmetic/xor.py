import quantumpseudocode as qp
from quantumpseudocode.ops import semi_quantum
from quantumpseudocode import sink


def do_xor_const_classical(*,
                           lvalue: qp.IntBuf,
                           mask: int):
    lvalue ^= mask


def do_xor_classical(*,
                     lvalue: qp.IntBuf,
                     mask: qp.IntBuf):
    lvalue ^= mask


@semi_quantum(alloc_prefix='_xor_const_', classical=do_xor_const_classical)
def do_xor_const(*,
                 control: qp.Qubit.Control = True,
                 lvalue: qp.Quint,
                 mask: int):
    assert isinstance(control, qp.QubitIntersection) and len(control.qubits) <= 1
    assert isinstance(lvalue, qp.Quint)
    assert isinstance(mask, int)
    targets = [q for i, q in enumerate(lvalue) if mask & (1 << i)]
    sink.global_sink.do_toggle(qp.RawQureg(targets), control)


@semi_quantum(alloc_prefix='_xor_', classical=do_xor_classical)
def do_xor(*,
           control: qp.Qubit.Control = True,
           lvalue: qp.Quint,
           mask: qp.Quint.Borrowed):
    assert isinstance(control, qp.QubitIntersection) and len(control.qubits) <= 1
    assert isinstance(lvalue, qp.Quint)
    assert isinstance(mask, qp.Quint)
    for q, m in zip(lvalue, mask):
        sink.global_sink.do_toggle(q.qureg, control & m)
