from typing import Union, Any

import quantumpseudocode


class Operation:
    def do(self, controls: 'quantumpseudocode.QubitIntersection'):
        raise RuntimeError('Unprocessed terminal operation: {!r}'.format(self))

    def state_locations(self) -> 'quantumpseudocode.ArgsAndKwargs[Union[quantumpseudocode.Qureg, quantumpseudocode.Qubit, quantumpseudocode.Quint], Any]':
        raise NotImplementedError('state_locations not implemented by {!r}'.format(self))

    def mutate_state(self, forward: bool, *args, **kwargs):
        raise NotImplementedError('mutate_state not implemented by {!r}'.format(self))

    def inverse(self) -> 'Operation':
        return quantumpseudocode.InverseOperation(self)

    def controlled_by(self, controls: Union['quantumpseudocode.Qubit',
                                            'quantumpseudocode.QubitIntersection']):
        if isinstance(controls, quantumpseudocode.Qubit):
            return quantumpseudocode.ControlledOperation(self, quantumpseudocode.QubitIntersection((controls,)))
        if len(controls) == 0:
            return self
        return quantumpseudocode.ControlledOperation(self, controls)


class FlagOperation(Operation):
    def state_locations(self):
        return ()

    def mutate_state(self, forward: bool, *args, **kwargs):
        pass

    def inverse(self):
        raise NotImplementedError('{!r} has no defined inverse'.format(self))


class LetRValueOperation(Operation):
    def __init__(self, rvalue: 'quantumpseudocode.RValue', loc: Any):
        self.rvalue = rvalue
        self.loc = loc

    def inverse(self) -> 'quantumpseudocode.Operation':
        return DelRValueOperation(self.rvalue, self.loc)

    def do(self, controls: 'quantumpseudocode.QubitIntersection'):
        self.rvalue.init_storage_location(self.loc, controls)

    def __str__(self):
        return '{} := {}'.format(self.loc, self.rvalue)

    def __repr__(self):
        return 'quantumpseudocode.LetRValueOperation({!r}, {!r})'.format(self.rvalue,
                                                             self.loc)


class DelRValueOperation(Operation):
    def __init__(self, rvalue: 'quantumpseudocode.RValue', loc: Any):
        self.rvalue = rvalue
        self.loc = loc

    def inverse(self) -> 'quantumpseudocode.Operation':
        return LetRValueOperation(self.rvalue, self.loc)

    def do(self, controls: 'quantumpseudocode.QubitIntersection'):
        self.rvalue.init_storage_location(self.loc, controls)

    def __str__(self):
        return '{} := {}'.format(self.loc, self.rvalue)

    def __repr__(self):
        return 'quantumpseudocode.LetRValueOperation({!r}, {!r})'.format(self.rvalue,
                                                             self.loc)
