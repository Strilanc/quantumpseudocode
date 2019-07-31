from typing import Union, Any, Callable

import cirq

import quantumpseudocode as qp


class ClassicalSimState:
    phase_degrees: float

    def measurement_based_uncomputation_result_chooser(self) -> Callable[[], bool]:
        raise NotImplementedError()

    def quint_buf(self, quint: 'qp.Quint') -> 'qp.IntBuf':
        raise NotImplementedError()

    def resolve_location(self, loc: Any, allow_mutate: bool) -> Any:
        pass


class Operation:
    def emit_ops(self, controls: 'qp.QubitIntersection'):
        raise RuntimeError('Unprocessed terminal operation: {!r}'.format(self))

    def mutate_state(self, sim_state: 'qp.ClassicalSimState', forward: bool) -> None:
        raise NotImplementedError('mutate_state not implemented by {!r}'.format(self))

    def inverse(self) -> 'Operation':
        return qp.InverseOperation(self)

    def controlled_by(self, controls: Union['qp.Qubit',
                                            'qp.QubitIntersection']):
        if isinstance(controls, qp.Qubit):
            return qp.ControlledOperation(self, qp.QubitIntersection((controls,)))
        if controls == qp.QubitIntersection.ALWAYS:
            return self
        return qp.ControlledOperation(self, controls)


class FlagOperation(Operation):
    def mutate_state(self, sim_state: 'qp.ClassicalSimState', forward: bool) -> None:
        pass

    def inverse(self):
        raise NotImplementedError('{!r} has no defined inverse'.format(self))


@cirq.value_equality
class LetRValueOperation(Operation):
    def __init__(self, rvalue: 'qp.RValue', loc: Any):
        self.rvalue = qp.rval(rvalue)
        self.loc = loc

    def inverse(self) -> 'qp.Operation':
        return DelRValueOperation(self.rvalue, self.loc)

    def _value_equality_values_(self):
        return self.rvalue, self.loc

    def emit_ops(self, controls: 'qp.QubitIntersection'):
        self.rvalue.init_storage_location(self.loc, controls)

    def __str__(self):
        return '{} := {}'.format(self.loc, self.rvalue)

    def __repr__(self):
        return 'qp.LetRValueOperation({!r}, {!r})'.format(self.rvalue,
                                                             self.loc)


@cirq.value_equality
class DelRValueOperation(Operation):
    def __init__(self, rvalue: 'qp.RValue', loc: Any):
        self.rvalue = qp.rval(rvalue)
        self.loc = loc

    def _value_equality_values_(self):
        return self.rvalue, self.loc

    def inverse(self) -> 'qp.Operation':
        return LetRValueOperation(self.rvalue, self.loc)

    def emit_ops(self, controls: 'qp.QubitIntersection'):
        self.rvalue.del_storage_location(self.loc, controls)

    def __str__(self):
        return '{} := {}'.format(self.loc, self.rvalue)

    def __repr__(self):
        return 'qp.LetRValueOperation({!r}, {!r})'.format(self.rvalue,
                                                          self.loc)
