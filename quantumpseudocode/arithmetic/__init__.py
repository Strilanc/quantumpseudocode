from .xor import (
    XorEqual,
    XorEqualConst,
)

from .add import (
    PlusEqual,
    do_addition,
)

from .cmp import (
    IfLessThanRVal,
    EffectIfLessThan,
)

from .mul import (
    TimesEqual,
)

from .mult_add import (
    PlusEqualProduct,
)

from .measure import (
    measure,
    measure_x_for_phase_fixup_and_reset,
    MeasureOperation,
    MeasureXForPhaseKickOperation,
)

from .lookup import (
    LookupTable,
    LookupRValue,
    XorLookup,
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
