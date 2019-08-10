import quantumpseudocode as qp
from quantumpseudocode.ops import semi_quantum


def do_classical_add_mod(
        *,
        lvalue: 'qp.IntBufMod',
        offset: int,
        forward: bool = True):
    v = int(lvalue)
    assert v < lvalue.modulus
    if forward:
        lvalue.as_int_buf()[:] = (v + offset) % lvalue.modulus
    else:
        lvalue.as_int_buf()[:] = (v - offset) % lvalue.modulus


@semi_quantum(alloc_prefix='_addc_mod_', classical=do_classical_add_mod)
def do_add_const_mod(
        *,
        control: 'qp.Qubit.Control',
        lvalue: 'qp.QuintMod',
        offset: int,
        forward: bool = True):
    assert isinstance(control, qp.QubitIntersection) and len(control.qubits) <= 1
    assert isinstance(lvalue, qp.QuintMod)
    modulus = lvalue.modulus
    lvalue_as_quint = qp.Quint(lvalue.qureg)
    assert modulus > 0
    assert 0 <= offset < modulus
    n = (modulus - 1).bit_length()
    assert len(lvalue_as_quint) >= n
    if not forward:
        offset = -offset % modulus

    if not modulus & (modulus - 1):
        lvalue_as_quint += offset & qp.controlled_by(control)
        return

    with qp.qmanaged(qp.Qubit(name='mod_cmp')) as q:
        q.init(lvalue_as_quint >= modulus - offset, controls=control)
        lvalue_as_quint += offset & qp.controlled_by(control)
        lvalue_as_quint -= modulus & qp.controlled_by(q)
        q.clear(lvalue_as_quint < offset, controls=control)


@semi_quantum(alloc_prefix='_add_mod_', classical=do_classical_add_mod)
def do_add_mod(
        *,
        control: 'qp.Qubit.Control',
        lvalue: 'qp.QuintMod',
        offset: 'qp.Quint.Borrowed',
        forward: bool = True):
    assert isinstance(control, qp.QubitIntersection) and len(control.qubits) <= 1
    assert isinstance(lvalue, qp.QuintMod)
    assert isinstance(offset, qp.Quint)
    assert len(offset) <= len(lvalue)
    assert isinstance(lvalue, qp.QuintMod)
    modulus = lvalue.modulus
    n = (modulus - 1).bit_length()
    lvalue_as_quint = qp.Quint(lvalue.qureg)
    assert len(lvalue) >= n

    if not modulus & (modulus - 1):
        if forward:
            lvalue_as_quint += offset & qp.controlled_by(control)
        else:
            lvalue_as_quint -= offset & qp.controlled_by(control)
        return

    with offset.hold_padded_to(n) as offset:
        with qp.qmanaged(qp.Qubit(name='mod_cmp')) as q:
            if forward:
                offset ^= -1
                offset += modulus + 1
                q.init(lvalue_as_quint >= offset, controls=control)
                offset -= modulus + 1
                offset ^= -1

                lvalue_as_quint += offset & qp.controlled_by(control)
                lvalue_as_quint -= modulus & qp.controlled_by(q)
                q.clear(lvalue_as_quint < offset, controls=control)
            else:
                q.init(lvalue_as_quint < offset, controls=control)
                lvalue_as_quint += modulus & qp.controlled_by(q)
                lvalue_as_quint -= offset & qp.controlled_by(control)

                offset ^= -1
                offset += modulus + 1
                q.clear(lvalue_as_quint >= offset, controls=control)
                offset -= modulus + 1
                offset ^= -1
