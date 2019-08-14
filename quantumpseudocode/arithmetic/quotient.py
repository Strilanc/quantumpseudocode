from typing import Tuple

import quantumpseudocode as qp
from quantumpseudocode.ops import semi_quantum


def classical_do_init_small_quotient(*,
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


@semi_quantum(classical=classical_do_init_small_quotient)
def do_init_small_quotient(*,
                           lvalue: qp.Quint,
                           total: qp.Quint,
                           divisor: int,
                           forward: bool = True):
    """Performs lvalue := total // divisor.

    Args:
        lvalue: A zero'd register that will end up storing total // divisor.
        total: A register containing some value q*divisor + r.
        divisor: The value to divide by.
        forward: If not set, uncomputes the small quotient instead of computing
            it.
    """
    if divisor == 1:
        lvalue ^= total
        return

    # Determine problem size from register sizes.
    max_quotient = min(
        ((1 << len(total)) - 1) // divisor,
        (1 << len(lvalue)) - 1
    )
    max_total = min(
        (divisor << len(lvalue)) - 1,
        (1 << len(total)) - 1
    )
    lvalue = lvalue[:max_quotient.bit_length()]
    total = total[:max_total.bit_length()]

    # Compute the quotient.
    m, start, thresh = build_quotient_threshold_table(divisor, max_total)
    low, high = total[:m], total[m:]
    if forward:
        lvalue ^= start[high]
        lvalue += low > thresh[high]
    else:
        lvalue -= low > thresh[high]
        lvalue.clear(start[high])


def build_quotient_threshold_table(divisor: int,
                                   max_total: int,
                                   ) -> Tuple[int, qp.LookupTable, qp.LookupTable]:
    n = (divisor - 1).bit_length()
    m = n - 1
    mask = ~(-1 << m)
    max_address = max_total >> m

    quotients = []
    thresholds = []
    for address in range(max_address + 1):
        q = (address << m) // divisor
        next_q = ((address + 1) << m) // divisor
        if q == next_q:
            t = mask
        else:
            t = ((q + 1) * divisor - 1) & mask
        quotients.append(q)
        thresholds.append(t)

    return m, qp.LookupTable(quotients), qp.LookupTable(thresholds)
