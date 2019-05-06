import inspect
from typing import Union, Any, TypeVar, get_type_hints, Generic

import cirq

import quantumpseudocode
from .operation import Operation

T = TypeVar('T')


ArgTypes = Union[quantumpseudocode.RValue[Any], 'quantumpseudocode.Operation']


@cirq.value_equality
class SignatureOperation(Operation):
    def __init__(self,
                 gate: 'quantumpseudocode.SignatureGate',
                 args: quantumpseudocode.ArgsAndKwargs[ArgTypes]):
        self.gate = gate
        self.args = args

    def _value_equality_values_(self):
        return self.gate, self.args

    def state_locations(self):
        return self.args

    def mutate_state(self, forward: bool, args: 'quantumpseudocode.ArgsAndKwargs'):
        matched = args.match_parameters(self.gate.emulate, skip=1)

        def unwrap_immutable(a: quantumpseudocode.ArgParameter):
            if getattr(a.parameter_type, '__origin__', None) is quantumpseudocode.Mutable:
                assert isinstance(a.arg, quantumpseudocode.Mutable)
                return a.arg
            if isinstance(a.arg, quantumpseudocode.Mutable):
                return a.arg.val
            else:
                return a.arg
        unwrapped = matched.map(unwrap_immutable)

        def f(*args, **kwargs):
            self.gate.emulate(forward, *args, **kwargs)
        unwrapped.pass_into(f)

    def do(self, controls: 'quantumpseudocode.QubitIntersection'):
        with quantumpseudocode.HeldMultipleRValue(self.args, self.gate.register_name_prefix()) as args:
            try:
                self.gate.do(controls, *args.args, **args.kwargs)
            except TypeError as ex:
                if 'do()' in str(ex):
                    raise TypeError(str(ex) + '\n\nWhile calling:\n{}\n\nrepr:\n{!r}'.format(self, self))
                raise

    def inverse(self):
        inv_gate = cirq.inverse(self.gate, default=NotImplemented)
        if inv_gate is NotImplemented:
            return super().inverse()
        if inv_gate is self.gate:
            return self
        return SignatureOperation(inv_gate, self.args)

    def __str__(self):
        return self.args.pass_into(self.gate.describe)

    def __repr__(self):
        return 'quantumpseudocode.SignatureOperation({!r}, {!r})'.format(
            self.gate, self.args)
