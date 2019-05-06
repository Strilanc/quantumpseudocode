from typing import Union, Any, TypeVar

import cirq

import quantumpseudocode as qp
from .operation import Operation

T = TypeVar('T')


ArgTypes = Union[qp.RValue[Any], 'qp.Operation']


@cirq.value_equality(distinct_child_types=True)
class SimpleOp(Operation):
    def __init__(self, *args, **kwargs):
        self._args = qp.ArgsAndKwargs(args, kwargs)

        # Trigger signature mismatch failures right away.
        _ = self.describe(*args, **kwargs)

    def _value_equality_values_(self):
        return self._args

    def alloc_prefix(self):
        return ''
    def emulate(self, *args, **kwargs):
        raise NotImplemented()
    def sigdo(self, *args, **kwargs):
        raise NotImplemented()
    def describe(self, *args, **kwargs):
        raise NotImplemented()
    def inv_type(self):
        return None

    def state_locations(self):
        return self._args

    def mutate_state(self, forward: bool, args: 'qp.ArgsAndKwargs'):
        if not forward:
            return self.inverse().mutate_state(True, args)

        matched = args.match_parameters(self.emulate)

        def unwrap_immutable(a: qp.ArgParameter):
            if getattr(a.parameter_type, '__origin__', None) is qp.Mutable:
                assert isinstance(a.arg, qp.Mutable)
                return a.arg
            if isinstance(a.arg, qp.Mutable):
                return a.arg.val
            else:
                return a.arg
        unwrapped = matched.map(unwrap_immutable)

        unwrapped.pass_into(self.emulate)

    def inverse(self):
        inv = self.inv_type()
        if inv is None:
            return super().inverse()
        return self._args.pass_into(inv)

    def __pow__(self, power):
        if power == 1:
            return self
        if power == -1:
            return self.inverse()

    def do(self, controls: 'qp.QubitIntersection'):
        def f(x: qp.ArgParameter):
            if x.parameter_type == qp.Quint:
                if isinstance(x.arg, int):
                    return qp.IntRValue(x.arg)
            if x.parameter_type == qp.Qubit:
                if isinstance(x.arg, bool):
                    return qp.BoolRValue(x.arg)
            return x.arg
        v = self._args.match_parameters(self.sigdo, skip=1).map(f)

        with qp.HeldMultipleRValue(v, self.alloc_prefix()) as args:
            try:
                self.sigdo(controls, *args.args, **args.kwargs)
            except TypeError as ex:
                if 'do()' in str(ex):
                    raise TypeError(str(ex) + '\n\nWhile calling:\n{}\n\nrepr:\n{!r}'.format(self, self))
                raise

    def __str__(self):
        return self._args.pass_into(self.describe)

    def __repr__(self):
        class_name = str(type(self))
        if "<class 'quantumpseudocode." in class_name:
            class_name = 'qp.' + type(self).__name__
        else:
            class_name = type(self).__name__
        return '{}({})'.format(class_name, self._args.repr_args())
