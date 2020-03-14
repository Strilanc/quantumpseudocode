import functools
import inspect
from typing import Union, Any, get_type_hints, List, Callable, Dict

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
        raise NotImplemented()
    def describe(self, *args, **kwargs):
        raise NotImplemented()
    def inv_type(self):
        return None

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

    def mutate_state(self, sim_state: 'qp.ClassicalSimState', forward: bool) -> None:
        do_sig = _paramsNameToTypeMap(self.do, ['controls'])
        if hasattr(self, 'biemulate'):
            emu_sig = _paramsNameToTypeMap(self.biemulate, ['forward'])
        elif hasattr(self, 'emulate'):
            emu_sig = _paramsNameToTypeMap(self.emulate, [])
        else:
            raise NotImplementedError(
                '{} must implement emulate or biemulate.'.format(
                    type(self).__name__))
        desc_sig = _paramsNameToTypeMap(self.describe, [], allow_none=True)

        assert do_sig.keys() == emu_sig.keys() == desc_sig.keys() == self._args.kwargs.keys()
        assert len(self._args.args) == 0
        args = self._args.resolve(sim_state, True)
        if hasattr(self, 'biemulate'):
            args.pass_into(functools.partial(self.biemulate, forward))
        else:
            if not forward:
                self.inverse().mutate_state(sim_state, True)
                return
            args.pass_into(functools.partial(self.emulate))


def _paramsNameToTypeMap(func: Callable,
                         skipped_parameters: List[str],
                         allow_none: bool = False) -> Dict[str, type]:
    result: Dict[str, type] = {}
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)
    for parameter in sig.parameters.values():
        if parameter.name not in skipped_parameters:
            assert parameter.kind == inspect.Parameter.KEYWORD_ONLY, (
                f'Parameter {parameter.name} must be keyword-only '
                '(i.e. come after a "*," or "*args," argument) on function '
                f'{func}.'
            )
            t = type_hints.get(parameter.name, None)
            assert t is not None or allow_none
            result[parameter.name] = t
    return result


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
