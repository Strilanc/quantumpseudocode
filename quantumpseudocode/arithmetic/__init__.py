from .xor import (
    XorEqual,
    XorEqualConst,
)

from .add import (
    do_addition,
    do_subtraction,
)

from .cmp import (
    IfLessThanRVal,
    EffectIfLessThan,
)

from .mul import (
    TimesEqual,
)

from .mult_add import (
    do_multiply_add,
    do_classical_multiply_add,
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
    OP_PHASE_FLIP,
    phase_flip,
    GlobalPhaseOp,
)

from .toggle import (
    Toggle,
)

from .unary import (
    UnaryRValue,
)

from .swap import (
    swap,
)
