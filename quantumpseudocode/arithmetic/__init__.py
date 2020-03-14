from .xor import (
    do_xor,
    do_xor_const,
)

from .add import (
    do_addition,
    do_subtraction,
)

from .cmp import (
    IfLessThanRVal,
    EffectIfLessThan,
    QuintEqConstRVal,
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
    OP_PHASE_FLIP,
    phase_flip,
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
