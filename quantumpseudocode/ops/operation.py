from typing import Union, Any

import quantumpseudocode as qp


class Operation:
    def emit_ops(self, controls: 'qp.QubitIntersection'):
        raise RuntimeError('Unprocessed terminal operation: {!r}'.format(self))

    def state_locations(self) -> 'qp.ArgsAndKwargs[Union[qp.Qureg, qp.Qubit, qp.Quint], Any]':
        raise NotImplementedError('state_locations not implemented by {!r}'.format(self))

    def mutate_state(self, forward: bool, args: 'qp.ArgsAndKwargs') -> None:
        raise NotImplementedError('mutate_state not implemented by {!r}'.format(self))

    def inverse(self) -> 'Operation':
        return qp.InverseOperation(self)

    def controlled_by(self, controls: Union['qp.Qubit',
                                            'qp.QubitIntersection']):
        if isinstance(controls, qp.Qubit):
            return qp.ControlledOperation(self, qp.QubitIntersection((controls,)))
        if len(controls) == 0:
            return self
        return qp.ControlledOperation(self, controls)


class FlagOperation(Operation):
    def state_locations(self):
        return ()

    def mutate_state(self, forward: bool, args: 'qp.ArgsAndKwargs'):
        pass

    def inverse(self):
        raise NotImplementedError('{!r} has no defined inverse'.format(self))


class LetRValueOperation(Operation):
    def __init__(self, rvalue: 'qp.RValue', loc: Any):
        self.rvalue = rvalue
        self.loc = loc

    def inverse(self) -> 'qp.Operation':
        return DelRValueOperation(self.rvalue, self.loc)

    def emit_ops(self, controls: 'qp.QubitIntersection'):
        self.rvalue.init_storage_location(self.loc, controls)

    def __str__(self):
        return '{} := {}'.format(self.loc, self.rvalue)

    def __repr__(self):
        return 'qp.LetRValueOperation({!r}, {!r})'.format(self.rvalue,
                                                             self.loc)


class DelRValueOperation(Operation):
    def __init__(self, rvalue: 'qp.RValue', loc: Any):
        self.rvalue = rvalue
        self.loc = loc

    def inverse(self) -> 'qp.Operation':
        return LetRValueOperation(self.rvalue, self.loc)

    def emit_ops(self, controls: 'qp.QubitIntersection'):
        self.rvalue.del_storage_location(self.loc, controls)

    def __str__(self):
        return '{} := {}'.format(self.loc, self.rvalue)

    def __repr__(self):
        return 'qp.LetRValueOperation({!r}, {!r})'.format(self.rvalue,
                                                          self.loc)
