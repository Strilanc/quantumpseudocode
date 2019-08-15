from typing import Tuple

import quantumpseudocode as qp
from quantumpseudocode.ops import semi_quantum


def classical_do_div_rem(*,
                         lvalue_total_then_remainder: qp.IntBuf,
                         lvalue_quotient: qp.IntBuf,
                         divisor: int,
                         forward: bool = True):
    if forward:
        t = int(lvalue_total_then_remainder)
        assert int(lvalue_quotient) == 0
        lvalue_quotient[:] = t // divisor
        lvalue_total_then_remainder[:] = t % divisor
    else:
        r = int(lvalue_total_then_remainder)
        q = int(lvalue_quotient)
        assert r < divisor
        lvalue_total_then_remainder[:] = q * divisor + r
        lvalue_quotient[:] = 0


@semi_quantum(classical=classical_do_div_rem)
def do_div_rem(*,
               lvalue_total_then_remainder: qp.Quint,
               lvalue_quotient: qp.Quint,
               divisor: int,
               forward: bool = True):
    """Replaces a value with a (quotient, remainder) pair relative to a given divisor.

    Args:
        lvalue_total_then_remainder: Initially equal to the total value (q*N + r). Transformed
            into the remainder value (r) by the end of the method.
        lvalue_quotient: Initially equal to 0. Transformed into the quotient value
            (q) by the end of the method.
        divisor: The value to divide by.
        forward: Determines if the function goes forward or backwards, i.e. from
            t -> q*N + r or else from q*N + r -> t.
    """
    if divisor == 1:
        if forward:
            lvalue_quotient ^= lvalue_total_then_remainder
            lvalue_total_then_remainder ^= lvalue_quotient
        else:
            lvalue_total_then_remainder ^= lvalue_quotient
            lvalue_quotient ^= lvalue_total_then_remainder
        return

    # Determine problem size from register sizes.
    max_quotient = min(
        ((1 << len(lvalue_total_then_remainder)) - 1) // divisor,
        (1 << len(lvalue_quotient)) - 1
    )
    max_total = min(
        (divisor << len(lvalue_quotient)) - 1,
        (1 << len(lvalue_total_then_remainder)) - 1
    )
    lvalue_quotient = lvalue_quotient[:max_quotient.bit_length()]
    lvalue_total_then_remainder = lvalue_total_then_remainder[:max_total.bit_length()]

    # Window size.
    w = qp.ceil_lg2(len(lvalue_total_then_remainder))

    chunks = []
    lv = lvalue_quotient
    while len(lv):
        word_offset = len(lv[:-w])
        lword = lv[-w:]
        chunks.append((word_offset, lword))
        lv = lv[:-w]

    if forward:
        for word_offset, lword in chunks:
            do_init_small_quotient(
                lvalue=lword,
                divisor=divisor << word_offset,
                total=lvalue_total_then_remainder,
                forward=True)
            lvalue_total_then_remainder[word_offset:] -= lword * divisor
    else:
        for word_offset, lword in chunks[::-1]:
            lvalue_total_then_remainder[word_offset:] += lword * divisor
            do_init_small_quotient(
                lvalue=lword,
                divisor=divisor << word_offset,
                total=lvalue_total_then_remainder,
                forward=False)


def classical_do_init_quotient(*,
                               lvalue: qp.IntBuf,
                               total: qp.IntBuf,
                               divisor: int,
                               forward: bool = True):
    if forward:
        assert int(lvalue) == 0
        lvalue[:] = int(total) // divisor
    else:
        assert lvalue[:] == int(total) // divisor
        lvalue[:] = 0


@semi_quantum(classical=classical_do_init_quotient)
def do_init_small_quotient(*,
                           lvalue: qp.Quint,
                           total: qp.Quint,
                           divisor: int,
                           forward: bool = True):
    """Performs lvalue := total // divisor.

    This method is efficient for small numbers of quotient bits, but has
    exponential scaling and so is inefficient for large numbers.

    Args:
        lvalue: A zero'd register that will end up storing total // divisor.
        total: A register containing some value q*divisor + r.
        divisor: The value to divide by.
        forward: If not set, uncomputes the small quotient instead of computing
            it.
    """
    m, start, thresh = build_quotient_threshold_table(divisor, len(total))
    low, high = total[:m], total[m:]
    if forward:
        lvalue ^= start[high]
        lvalue += low > thresh[high]
    else:
        lvalue -= low > thresh[high]
        lvalue.clear(start[high])


def build_quotient_threshold_table(divisor: int,
                                   total_n: int,
                                   ) -> Tuple[int, qp.LookupTable, qp.LookupTable]:
    n = (divisor - 1).bit_length()
    m = n - 1
    mask = ~(-1 << m)

    quotients = []
    thresholds = []
    for address in range(1 << (total_n - m)):
        q = (address << m) // divisor
        next_q = ((address + 1) << m) // divisor
        if q == next_q:
            t = mask
        else:
            t = ((q + 1) * divisor - 1) & mask
        quotients.append(q)
        thresholds.append(t)

    return m, qp.LookupTable(quotients), qp.LookupTable(thresholds)
