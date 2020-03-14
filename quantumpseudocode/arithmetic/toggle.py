import quantumpseudocode as qp
from quantumpseudocode.ops import Operation


class Toggle(Operation):
    def __init__(self, lvalue: 'qp.Qureg'):
        assert isinstance(lvalue, qp.Qureg)
        self.lvalue = lvalue

    def emit_ops(self, controls: 'qp.QubitIntersection'):
        qp.emit(self.controlled_by(controls))

    def mutate_state(self, sim_state: 'qp.ClassicalSimState', forward: bool) -> None:
        buf = sim_state.quint_buf(qp.Quint(self.lvalue))
        buf ^= -1

    def __repr__(self):
        return f'qp.Toggle({self.lvalue!r})'
