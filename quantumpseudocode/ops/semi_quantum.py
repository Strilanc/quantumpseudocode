import functools
import inspect
from typing import Union, Callable, get_type_hints, ContextManager, Dict, List, Optional, Any, NamedTuple

import quantumpseudocode as qp


def semi_quantum(func: Callable = None,
                 *,
                 alloc_prefix: Optional[str] = None,
                 classical: Callable = None) -> Callable:
    """Decorator that allows sending classical values and RValues into a function expecting quantum values.

    Args:
        func: The function to decorate. This function must have type annotations for its parameters. The type
            annotations are used to define how incoming values are wrapped. For example, a `qp.Qubit.Borrowed` can
            accept a `qp.Qubit`, a raw `bool`, or any `qp.RValue[int]` (e.g. the expression `a > b` where `a` and `b`
            are both quints produces such an rvalue.
        alloc_prefix: An optional string argument that determines how temporarily allocated qubits and quints are
            named. Defaults to the name of the decorated function with underscores on either side.
        classical: A function with the same arguments as `func` (except that a `control: qp.Qubit.Control` parameter
            can be omitted), but with types such as `qp.Quint` replaced by `qp.IntBuf`. The understanding is that
            the emulator's effect on mutable buffers should be equivalent to the quantum function's effect on
            corresponding qubits and quints.
    """

    # If keyword arguments were specified, python invokes the decorator method
    # without a `func` argument, then passes `func` into the result.
    if func is None:
        return lambda deferred_func: semi_quantum(deferred_func,
                                                  alloc_prefix=alloc_prefix,
                                                  classical=classical)

    if alloc_prefix is None:
        alloc_prefix = func.__name__
        if not alloc_prefix.startswith('_'):
            alloc_prefix = '_' + alloc_prefix
        if not alloc_prefix.endswith('_'):
            alloc_prefix = alloc_prefix + '_'
    type_hints = get_type_hints(func)

    # Empty state to be filled in with parameter handling information.
    type_string_map: Dict[str, type] = {}
    remap_string_map: Dict[str, Callable] = {}
    param_strings: List[str] = []
    assignment_strings: List[str] = []
    indent = '    '
    arg_strings: List[str] = []
    forced_keywords = False
    resolve_lines: List[str] = []
    resolve_arg_strings: List[str] = []

    classical_type_hints = get_type_hints(classical) if classical is not None else {}
    quantum_sig = inspect.signature(func)
    classical_sig = inspect.signature(classical) if classical is not None else None

    # Process each parameter individually.
    for parameter in quantum_sig.parameters.values():
        val = parameter.name
        t = type_hints[val]
        type_string = f'{getattr(t, "__name__", "type")}_{len(type_string_map)}'
        type_string_map[type_string] = t
        if parameter.default is not inspect.Parameter.empty:
            def_val = f'_default_val_{len(type_string_map)}'
            def_str = f' = {def_val}'
            type_string_map[def_val] = parameter.default
        else:
            def_str = ''
        if classical_sig is not None and val in classical_sig.parameters:
            if parameter.default != classical_sig.parameters[val].default:
                raise TypeError('Inconsistent default value. Quantum has {}={!r} but classical has {}={!r}'.format(
                    val,
                    parameter.default,
                    val,
                    classical_sig.parameters[val].default))
        parameter: inspect.Parameter

        # Sending and receiving arguments.
        if parameter.kind == inspect.Parameter.KEYWORD_ONLY and not forced_keywords:
            forced_keywords = True
            param_strings.append('*')
        param_strings.append(f'{val}: {type_string}{def_str}')
        arg_string = f'{val}={val}' if forced_keywords else val
        arg_strings.append(arg_string)

        # Transforming arguments.
        semi_data = TYPE_TO_SEMI_DATA.get(t, None)
        if semi_data is not None:
            holder = semi_data.context_manager_func
            if holder is not None:
                remap_string_map[holder.__name__] = holder
                assignment_strings.append(
                    f'{indent}with {holder.__name__}({val}, {repr(alloc_prefix + val)}) as {val}:')
                indent += '    '

            exposer = semi_data.transform_func
            if exposer is not None:
                remap_string_map[exposer.__name__] = exposer
                assignment_strings.append(f'{indent}{val} = {exposer.__name__}({val})')

            if val in classical_type_hints:
                remap_string_map[semi_data.resolve_func.__name__] = semi_data.resolve_func
                resolve_lines.append(f'    {val} = {semi_data.resolve_func.__name__}(sim_state, {val})')
                resolve_arg_strings.append(arg_string)

    # Assemble into a function body.
    func_name = f'_decorated_{func.__name__}'
    lines = [
        f'def {func_name}({", ".join(param_strings)}):',
        *assignment_strings,
        f'{indent}return func({", ".join(arg_strings)})'
    ]
    body = '\n'.join(lines)

    # Evaluate generated function code.
    result = _eval_body_func(body,
                             func,
                             func_name,
                             exec_globals={**type_string_map, **remap_string_map, 'func': func, 'qp': qp})
    if classical is not None:
        result.classical = classical
        if 'control' in type_hints and 'control' not in classical_type_hints:
            assert TYPE_TO_SEMI_DATA[type_hints['control']] is TYPE_TO_SEMI_DATA[qp.Qubit.Control]
            resolve_lines.insert(0, '    if not sim_state.resolve_location(control):')
            resolve_lines.insert(1, '        return')

        new_args = list(classical_type_hints.keys() - type_hints.keys() - {'sim_state'})
        for arg in list(new_args):
            if classical_sig.parameters[arg].default is not inspect.Parameter.empty:
                new_args.remove(arg)
        if new_args:
            raise TypeError('classical function cannot introduce new parameters '
                            '(besides sim+state and arguments with default values), '
                            'but {} introduced {!r}'.format(classical, new_args))
        missing_args = list(set(type_hints.keys()) - classical_type_hints.keys() - {'control'})
        if missing_args:
            raise TypeError('classical function cannot omit parameters (except control), '
                            'but missed {!r}'.format(missing_args))

        if 'sim_state' in classical_type_hints:
            resolve_arg_strings.insert(0, 'sim_state')

        resolve_body = '\n'.join([
            f'def sim(sim_state: qp.ClassicalSimState, {", ".join(param_strings)}):',
            *resolve_lines,
            f'    return classical_func({", ".join(resolve_arg_strings)})'
        ])

        result.sim = _eval_body_func(resolve_body,
                                     classical,
                                     'sim',
                                     {'classical_func': classical, 'qp': qp, **type_string_map, **remap_string_map})

    result.raw = func
    return result


def _eval_body_func(body: str, func: Callable, func_name_in_body: str, exec_globals: Dict[str, Any]) -> Callable:
    # Evaluate the code.
    exec_locals = {}
    try:
        exec(body, exec_globals, exec_locals)
    except Exception as ex:
        raise RuntimeError('Failed to build decorator transformation.\n'
                           '\n'
                           'Source:\n'
                           f'{body}\n'
                           '\n'
                           f'Globals: {exec_globals}\n'
                           f'Locals: {exec_locals}') from ex

    # Make the decorated function look like the original function when inspected.
    result = functools.wraps(func)(exec_locals[func_name_in_body])
    result.__doc__ = (result.__doc__ or '') + f'\n\n==== Decorator body ====\n{body}'

    return result


def _expose_as_quint(val: qp.LValue):
    if isinstance(val, qp.Quint):
        return val
    if isinstance(val, qp.Qubit):
        return qp.Quint(qp.RawQureg([val]))
    raise TypeError('Expected an int-like lvalue but got {!r}.'.format(val))


def _rval_quint_manager(val: 'qp.Quint.Borrowed', name: str) -> ContextManager['qp.Quint']:
    if isinstance(val, qp.Quint):
        return qp.EmptyManager(val)
    if isinstance(val, qp.Qubit):
        return qp.EmptyManager(qp.Quint(qp.RawQureg([val])))
    if isinstance(val, (bool, int)):
        return qp.HeldRValueManager(qp.IntRValue(int(val)), name=name)
    if isinstance(val, qp.RValue):
        return qp.HeldRValueManager(val,
                                    name=name,
                                    loc_transform=_expose_as_quint)
    raise TypeError('Expected a classical or quantum integer expression (a quint, int, or RVal[int]) '
                    'but got {!r}.'.format(val))


def _mutable_resolve(sim_state: 'qp.ClassicalSimState', val: Any):
    return sim_state.resolve_location(val, allow_mutate=True)


def _immutable_resolve(sim_state: 'qp.ClassicalSimState', val: Any):
    return sim_state.resolve_location(val, allow_mutate=False)


def _lval_quint_checker(val: 'qp.Quint') -> 'qp.Quint':
    if not isinstance(val, qp.Quint):
        raise TypeError('Expected a qp.Quint but got {!r}'.format(val))
    return val


def _lval_quint_mod_checker(val: 'qp.QuintMod') -> 'qp.QuintMod':
    if not isinstance(val, qp.QuintMod):
        raise TypeError('Expected a qp.QuintMod but got {!r}'.format(val))
    return val


def _rval_qubit_manager(val: 'qp.Qubit.Borrowed', name: str) -> ContextManager['qp.Qubit']:
    if isinstance(val, qp.Qubit):
        return qp.EmptyManager(val)
    if val in [False, True]:
        return qp.HeldRValueManager(qp.BoolRValue(bool(val)), name=name)
    if isinstance(val, qp.RValue):
        return qp.HeldRValueManager(val, name=name)
    raise TypeError('Expected a classical or quantum boolean expression (a qubit, bool, or RValue[bool]) '
                    'but got {!r}.'.format(val))


def _lval_qubit_checker(val: 'qp.Qubit') -> 'qp.Qubit':
    if not isinstance(val, qp.Qubit):
        raise TypeError('Expected a qp.Qubit but got {!r}'.format(val))
    return val


def _control_qubit_manager(val: 'qp.Qubit.Control', name: str) -> ContextManager['qp.QubitIntersection']:
    if val is None or val in [True, 1, qp.QubitIntersection.ALWAYS]:
        return qp.EmptyManager(qp.QubitIntersection.ALWAYS)
    if val in [False, 0, qp.QubitIntersection.NEVER]:
        return qp.EmptyManager(qp.QubitIntersection.NEVER)
    if isinstance(val, qp.Qubit):
        return qp.EmptyManager(qp.QubitIntersection((val,)))
    if isinstance(val, qp.QubitIntersection) and len(val.qubits) == 1:
        return qp.EmptyManager(val)
    if isinstance(val, qp.RValue) and not isinstance(val, qp.Quint):
        return qp.HeldRValueManager(val, name=name)
    raise TypeError('Expected a quantum control expression (a None, qubit, or RValue[bool]) '
                    'but got {!r}.'.format(val))


def _control_qubit_exposer(val: Union['qp.Qubit', 'qp.QubitIntersection']) -> 'qp.QubitIntersection':
    if isinstance(val, qp.Qubit):
        return qp.QubitIntersection((val,))
    assert isinstance(val, qp.QubitIntersection)
    return val


SemiQuantumTypeData = NamedTuple(
    'SemiQuantumType',
    [
        ('context_manager_func', Optional[Callable[[Any], ContextManager]]),
        ('transform_func', Optional[Callable[[Any], Any]]),
        ('resolve_func', Callable[[Any], Any]),
    ]
)


TYPE_TO_SEMI_DATA: Dict[type, SemiQuantumTypeData] = {
    qp.QuintMod: SemiQuantumTypeData(
        context_manager_func=None,
        transform_func=_lval_quint_mod_checker,
        resolve_func=_mutable_resolve),
    qp.Quint: SemiQuantumTypeData(
        context_manager_func=None,
        transform_func=_lval_quint_checker,
        resolve_func=_mutable_resolve),
    qp.Quint.Borrowed: SemiQuantumTypeData(
        context_manager_func=_rval_quint_manager,
        transform_func=None,
        resolve_func=_immutable_resolve),
    qp.Qubit: SemiQuantumTypeData(
        context_manager_func=None,
        transform_func=_lval_qubit_checker,
        resolve_func=_mutable_resolve),
    qp.Qubit.Borrowed: SemiQuantumTypeData(
        context_manager_func=_rval_qubit_manager,
        transform_func=None,
        resolve_func=_immutable_resolve),
    qp.Qubit.Control: SemiQuantumTypeData(
        context_manager_func=_control_qubit_manager,
        transform_func=_control_qubit_exposer,
        resolve_func=_mutable_resolve),
}
