import functools
from typing import Union, Any

import cirq

import quantumpseudocode as qp
from .operation import Operation


SigHoldArgTypes = Union[qp.RValue[Any], 'qp.Operation']


@cirq.value_equality(distinct_child_types=True)
class Op(Operation):
    def __init__(self, *args, **kwargs):
        self._args = qp.ArgsAndKwargs(args, kwargs)

        # Trigger signature mismatch failures right away.
        _ = self.describe(*args, **kwargs)

    def _value_equality_values_(self):
        return self._args

    def alloc_prefix(self):
        return ''
    def do(self, controls: 'qp.QubitIntersection', *args, **kwargs):
        if self.inv_type() is not None:
            qp.emit(qp.InverseOperation(self.inverse()))
        raise NotImplemented()
    def describe(self, *args, **kwargs):
        raise NotImplemented()
    def inv_type(self):
        return None

    def state_locations(self):
        return self._args

    def inverse(self):
        inv = self.inv_type()
        if inv is None:
            return super().inverse()
        return self._args.pass_into(inv)

    def emit_ops(self, controls: 'qp.QubitIntersection'):
        v = self._args.match_parameters(self.do, skip=1).map(_rval_wrap)

        with qp.HeldMultipleRValue(v, self.alloc_prefix()) as args:
            try:
                self.do(controls, *args.args, **args.kwargs)
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

    def mutate_state(self, forward: bool, args: 'qp.ArgsAndKwargs'):
        if hasattr(self, 'biemulate'):
            matched = args.match_parameters(self.biemulate, skip=1)
            unwrapped = matched.map(_unwrap_untagged_mutable)
            unwrapped.pass_into(functools.partial(self.biemulate, forward))
            return

        if hasattr(self, 'emulate'):
            if not forward:
                self.inverse().mutate_state(True, args)
                return
            matched = args.match_parameters(self.emulate)
            unwrapped = matched.map(_unwrap_untagged_mutable)
            unwrapped.pass_into(self.emulate)
            return

        raise NotImplementedError(
            '{} must implement emulate or biemulate.'.format(
                type(self).__name__))


def _unwrap_untagged_mutable(a: qp.ArgParameter):
    assert a.parameter_type is not None, (
        f'Parameter "{a.parameter.name}" must have a type annotation.')
    assert isinstance(a.arg, a.parameter_type), (
        f'Parameter "{a.parameter.name}" has '
        f'type annotation "{a.parameter_type}" '
        f'but was passed an argument of type {type(a.arg)}.\n'
        f'Arg: {a.arg}.')
    return a.arg


def _rval_wrap(x: qp.ArgParameter):
    if x.parameter_type == qp.Quint:
        if isinstance(x.arg, int):
            return qp.IntRValue(x.arg)
    if x.parameter_type == qp.Qubit:
        if isinstance(x.arg, bool):
            return qp.BoolRValue(x.arg)
    return x.arg
