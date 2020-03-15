from .xor import (
    do_xor,
    do_xor_const,
)

from .add import (
    do_addition,
)

from .cmp import (
    IfLessThanRVal,
    QuintEqConstRVal,
    do_if_less_than,
)

from .mul import (
    do_multiplication,
)

from .mult_add import (
    do_plus_product,
)

from .measure import (
    measure,
    MeasureOperation,
    StartMeasurementBasedUncomputation,
    EndMeasurementBasedComputationOp,
    measurement_based_uncomputation,
)

from .lookup import (
    LookupRValue,
    do_xor_lookup,
    del_xor_lookup,
)

from .phase_flip import (
    phase_flip,
)

from .unary import (
    UnaryRValue,
)

from .swap import (
    swap,
)
