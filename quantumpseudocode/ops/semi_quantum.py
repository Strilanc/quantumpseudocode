import functools
import inspect
from typing import Union, Callable, get_type_hints, ContextManager, Dict, List

import quantumpseudocode as qp


def semi_quantum(func: Callable) -> Callable:
    """Decorator that allows sending classical values and RValues into a function expecting quantum values.

    Args:
        func: The function to decorate. This function must have type annotations for its parameters. The type
            annotations are used to define how incoming values are wrapped. For example, a `qp.Qubit.Borrowed` can
            accept a `qp.Qubit`, a raw `bool`, or any `qp.RValue[int]` (e.g. the expression `a > b` where `a` and `b`
            are both quints produces such an rvalue.
    """

    sig = inspect.signature(func)
    type_hints = get_type_hints(func)

    # Empty state to be filled in with parameter handling information.
    type_string_map: Dict[str, type] = {}
    remap_string_map: Dict[str, Callable] = {}
    param_strings: List[str] = []
    assignment_strings: List[str] = []
    indent = '    '
    arg_strings: List[str] = []
    forced_keywords = False

    # Process each parameter individually.
    for parameter in sig.parameters.values():
        val = parameter.name
        t = type_hints[val]
        type_string = f'{getattr(t, "__name__", "type")}_{len(type_string_map)}'
        type_string_map[type_string] = t

        # Sending and receiving arguments.
        if parameter.kind == inspect.Parameter.KEYWORD_ONLY and not forced_keywords:
            forced_keywords = True
            param_strings.append('*')
        param_strings.append(f'{val}: {type_string}')
        arg_strings.append(f'{val}={val}' if forced_keywords else val)

        # Transforming arguments.
        transform = _type_to_transform.get(t, None)
        if transform is not None:
            holder, exposer = transform
            if holder is not None:
                remap_string_map[holder.__name__] = holder
                assignment_strings.append(f'{indent}with {holder.__name__}({val}, {repr(val)}) as {val}:')
                indent += '    '
            if exposer is not None:
                remap_string_map[exposer.__name__] = exposer
                assignment_strings.append(f'{indent}{val} = {exposer.__name__}({val})')

    # Assemble into a function body.
    func_name = f'_decorated_{func.__name__}'
    lines = [
        f'def {func_name}({", ".join(param_strings)}):',
        *assignment_strings,
        f'{indent}return func({", ".join(arg_strings)})'
    ]
    body = '\n'.join(lines)

    # Evaluate generated function code.
    exec_locals = {}
    exec_globals = {**type_string_map, **remap_string_map, 'func': func, 'qp': qp}
    try:
        exec(body, exec_globals, exec_locals)
    except Exception as ex:
        raise RuntimeError('Failed to build decorator transformation.\n'
                           '\n'
                           'Source:\n'
                           '{body}\n'
                           '\n'
                           f'Globals: {exec_globals}\n'
                           f'Locals: {exec_locals}') from ex

    # Make the decorated function look like the original function under inspection.
    result = functools.wraps(func)(exec_locals[func_name])
    result.__doc__ = (result.__doc__ or '') + f'\n\n==== Decorator body ====\n{body}'
    return result


def _rval_quint_manager(val: 'qp.Quint.Borrowed', name: str) -> ContextManager:
    if isinstance(val, qp.Quint):
        return qp.EmptyManager(val)
    if isinstance(val, (bool, int)):
        return qp.HeldRValueManager(qp.IntRValue(int(val)), name=name)
    if isinstance(val, qp.RValue):
        return qp.HeldRValueManager(val, name=name)
    raise TypeError('Expected a classical or quantum integer expression (a quint, int, or RVal[int]) '
                    'but got {!r}.'.format(val))


def _lval_quint_checker(val: 'qp.Quint') -> 'qp.Quint':
    if not isinstance(val, qp.Quint):
        raise TypeError('Expected a qp.Quint but got {!r}'.format(val))
    return val


def _rval_qubit_manager(val: 'qp.Qubit.Borrowed', name: str) -> ContextManager:
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


def _control_qubit_manager(val: 'qp.Qubit.Control', name: str) -> ContextManager:
    if val is None or val in [True, 1, qp.QubitIntersection.ALWAYS]:
        return qp.EmptyManager(qp.QubitIntersection.ALWAYS)
    if val in [False, 0, qp.QubitIntersection.NEVER]:
        return qp.EmptyManager(qp.QubitIntersection.NEVER)
    if isinstance(val, qp.Qubit):
        return qp.EmptyManager(qp.QubitIntersection((val,)))
    if isinstance(val, qp.QubitIntersection) and len(val.qubits) == 1:
        return qp.EmptyManager(val)
    if isinstance(val, qp.RValue):
        return qp.HeldRValueManager(val, name=name)
    raise TypeError('Expected a quantum control expression (a None, qubit, or RValue[bool]) '
                    'but got {!r}.'.format(val))


def _control_qubit_exposer(val: Union['qp.Qubit', 'qp.QubitIntersection']) -> 'qp.QubitIntersection':
    if isinstance(val, qp.Qubit):
        return qp.QubitIntersection((val,))
    assert isinstance(val, qp.QubitIntersection)
    return val


def _generate_type_to_transform():
    result = {
        qp.Quint: (None, _lval_quint_checker),
        qp.Quint.Borrowed: (_rval_quint_manager, None),
        qp.Qubit: (None, _lval_qubit_checker),
        qp.Qubit.Borrowed: (_rval_qubit_manager, None),
        qp.Qubit.Control: (_control_qubit_manager, _control_qubit_exposer),
    }
    for t, v in list(result.items()):
        def _f() -> t:
            pass
        t2 = get_type_hints(_f)['return']
        result[t2] = v
    return result


_type_to_transform = _generate_type_to_transform()
