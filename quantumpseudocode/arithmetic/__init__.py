from .xor import (
    OP_XOR,
    OP_XOR_C,
)

from .add import (
    PlusEqual,
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
    OP_TOGGLE,
)

from .unary import (
    UnaryRValue,
)
