import inspect
import random
from typing import Any, Callable, Iterable, Sequence, get_type_hints, Union, Dict, TypeVar, Generic, List

import quantumpseudocode as qp


TSample = TypeVar('TSample')


def assert_semi_quantum_func_is_consistent(
        func: Callable,
        fuzz_space: Dict[str, Any] = None,
        fuzz_count: int = 0,
        fixed: Sequence[Dict[str, Any]] = ()):
    classical = getattr(func, 'classical', None)
    assert classical is not None, f'Function {func} does not specify a classical= decorator argument.'
    assert fuzz_count or fixed

    quantum_has_control = 'control' in get_type_hints(func)
    for kwargs in fixed:
        _assert_semi_quantum_func_is_consistent(func, quantum_has_control, classical, kwargs)
    for _ in range(fuzz_count):
        _assert_semi_quantum_func_is_consistent(func, quantum_has_control, classical, _sample(fuzz_space))


def _assert_semi_quantum_func_is_consistent(
        quantum_func: Callable,
        quantum_has_control: bool,
        classical_func: Callable,
        kwargs: Dict[str, Any]):

    if 'control' not in kwargs and quantum_has_control:
        for control in [False, True]:
            _assert_semi_quantum_func_is_consistent(quantum_func,
                                                    quantum_has_control,
                                                    classical_func,
                                                    {**kwargs, 'control': control})
        return

    classical_result = _apply_classical(classical_func, kwargs)
    quantum_result = _apply_quantum(quantum_func, kwargs)
    assert classical_result == quantum_result, '\n'.join([
        'Classical function disagreed with quantum function.'
        '',
        'Quantum function: {}'.format(quantum_func),
        'Classical function: {}'.format(classical_func),
        '',
        'Input: {!r}'.format(kwargs),
        '',
        'Quantum output: {!r}'.format(quantum_result),
        'Classical output: {!r}'.format(classical_result),
    ])


def _apply_quantum(func: Callable, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    with qp.Sim() as sim:
        type_hints = get_type_hints(func)
        mapped = {}
        for k, v in kwargs.items():
            if type_hints[k] == qp.Quint:
                assert isinstance(v, qp.IntBuf), 'Expected type qp.IntBuf for argument "{}"'.format(k)
                mapped[k] = qp.qalloc_int(bits=len(v), name=k)
                mapped[k] ^= int(v)
            elif type_hints[k] == qp.QuintMod:
                assert isinstance(v, qp.IntBufMod), 'Expected type qp.IntBufMod for argument "{}"'.format(k)
                mapped[k] = qp.qalloc_int_mod(modulus=v.modulus, name=k)
                as_quint = qp.Quint(mapped[k].qureg)
                as_quint ^= int(v)
            elif type_hints[k] == qp.Qubit:
                assert isinstance(v, qp.IntBuf) and len(v) == 1, 'Expected length 1 qp.IntBuf for argument "{}"'.format(
                    k)
                mapped[k] = qp.alloc(name=k)
                mapped[k] ^= int(v)
            else:
                mapped[k] = v

        func(**mapped)

        result = {}
        for k, v in kwargs.items():
            if type_hints[k] in [qp.Quint, qp.Qubit]:
                result[k] = qp.measure(mapped[k], reset=True)
        result['sim_state.phase_degrees'] = sim.phase_degrees
    return result


def _apply_classical(func: Callable, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    kwargs = {k: v.copy() if hasattr(v, 'copy') else v for k, v in kwargs.items()}

    type_hints = get_type_hints(func)
    if 'control' in kwargs and 'control' not in type_hints:
        run = kwargs['control']
        del kwargs['control']
    else:
        run = True

    if run:
        if 'sim_state' in type_hints:
            kwargs['sim_state'] = qp.Sim()
        func(**kwargs)

    result = {'sim_state.phase_degrees': 0}
    for k, v in kwargs.items():
        if isinstance(v, qp.IntBuf):
            result[k] = int(v)
        elif isinstance(v, qp.Sim):
            result['sim_state.phase_degrees'] = v.phase_degrees
    return result


def _sample(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    result = {}
    for k, space in kwargs.items():
        if isinstance(space, Callable):
            v = space(**{k: result[k] for k in inspect.signature(space).parameters})
        elif isinstance(space, Sequence):
            v = random.choice(space)
        else:
            v = space
        result[k] = v
    return result
