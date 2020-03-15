import quantumpseudocode as qp
from quantumpseudocode.ops import semi_quantum


def do_plus_const_mod_classical(*,
                                lvalue: qp.IntBuf,
                                offset: int,
                                modulus: int,
                                forward: bool = True):
    if not forward:
        offset *= -1
    lvalue[:] = (int(lvalue) + offset) % modulus


def do_plus_mod_classical(*,
                          lvalue: qp.IntBuf,
                          offset: qp.IntBuf,
                          modulus: int,
                          forward: bool = True):
    offset = int(offset)
    if not forward:
        offset *= -1
    lvalue[:] = (int(lvalue) + offset) % modulus


@semi_quantum(alloc_prefix='_do_plus_const_mod_', classical=do_plus_const_mod_classical)
def do_plus_const_mod(*,
                      control: qp.Qubit.Control = True,
                      lvalue: qp.Quint,
                      offset: int,
                      modulus: int,
                      forward: bool = True):
    assert isinstance(control, qp.QubitIntersection) and len(control.qubits) <= 1
    assert isinstance(lvalue, qp.Quint)
    assert isinstance(offset, int)
    assert isinstance(modulus, int)
    assert modulus > 0
    n = (modulus - 1).bit_length()
    assert len(lvalue) >= n
    if not forward:
        offset *= -1
    offset %= modulus

    if not modulus & (modulus - 1):
        lvalue += offset & qp.controlled_by(control)
        return

    with qp.qalloc(name='mod_cmp') as q:
        q.init(lvalue >= modulus - offset, controls=control)
        lvalue += offset & qp.controlled_by(control)
        lvalue -= modulus & qp.controlled_by(q & control)
        q.clear(lvalue < offset, controls=control)


@semi_quantum(alloc_prefix='_do_plus_mod_', classical=do_plus_mod_classical)
def do_plus_mod(control: 'qp.Qubit.Control' = True,
                *,
                lvalue: qp.Quint,
                offset: qp.Quint.Borrowed,
                modulus: int,
                forward: bool = True):
    assert isinstance(lvalue, qp.Quint)
    assert modulus > 0
    n = (modulus - 1).bit_length()
    assert len(offset) <= len(lvalue)
    assert len(lvalue) >= n

    if not modulus & (modulus - 1):
        if forward:
            lvalue[:n] += offset & qp.controlled_by(control)
        else:
            lvalue[:n] -= offset & qp.controlled_by(control)
        return

    with offset.hold_padded_to(n) as offset:
        with qp.qalloc(name='mod_cmp') as q:
            if forward:
                offset ^= -1
                offset += modulus + 1
                q.init(lvalue >= offset, controls=control)
                offset -= modulus + 1
                offset ^= -1

                lvalue += offset & qp.controlled_by(control)
                lvalue -= modulus & qp.controlled_by(q & control)
                q.clear(lvalue < offset, controls=control)
            else:
                q.init(lvalue < offset, controls=control)
                lvalue += modulus & qp.controlled_by(q & control)
                lvalue -= offset & qp.controlled_by(control)

                offset ^= -1
                offset += modulus + 1
                q.clear(lvalue >= offset, controls=control)
                offset -= modulus + 1
                offset ^= -1

