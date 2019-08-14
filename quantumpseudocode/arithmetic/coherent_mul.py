import quantumpseudocode as qp


def init_mul(*,
             factor1: qp.Quint,
             factor2: qp.Quint,
             clean_out: qp.Quint):
    """Initializes a zero'd quint to store the product of two quints."""
    n = len(factor1)
    m = len(factor2)
    for k in range(n):
        clean_out[k:k+m+1] += factor2 & qp.controlled_by(factor1[k])
    return clean_out


def init_square(*,
                factor: qp.Quint,
                clean_out: qp.Quint):
    """Initializes a zero'd quint to store the square of a quint."""
    n = len(factor)
    zero = qp.alloc(name='_sqr_zero')
    for k in range(n):
        rval = factor[k+1:] & qp.controlled_by(factor[k])
        with qp.hold(rval, name='_sqr_offset') as partial_offset:
            offset = qp.Quint(qp.RawQureg([
                factor[k],
                zero,
                *partial_offset.qureg
            ]))
            clean_out[2*k:2*k+len(offset)+1] += offset
    qp.free(zero)
    return clean_out
