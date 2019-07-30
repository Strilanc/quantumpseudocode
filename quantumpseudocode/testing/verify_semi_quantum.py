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
    with qp.Sim():
        type_hints = get_type_hints(func)
        mapped = {}
        for k, v in kwargs.items():
            if type_hints[k] == qp.Quint:
                assert isinstance(v, qp.IntBuf), 'Expected type qp.IntBuf for argument "{}"'.format(k)
                mapped[k] = qp.qalloc_int(bits=len(v), name=k)
                mapped[k] ^= int(v)
            elif type_hints[k] == qp.Qubit:
                assert isinstance(v, qp.IntBuf) and len(v) == 1, 'Expected length 1 qp.IntBuf for argument "{}"'.format(
                    k)
                mapped[k] = qp.qalloc(name=k)
                mapped[k] ^= int(v)
            else:
                mapped[k] = v

        func(**mapped)

        result = {}
        for k, v in kwargs.items():
            if type_hints[k] in [qp.Quint, qp.Qubit]:
                result[k] = qp.measure(mapped[k], reset=True)
    return result


def _apply_classical(func: Callable, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    kwargs = {k: v.copy() if hasattr(v, 'copy') else v for k, v in kwargs.items()}

    if 'control' in kwargs and 'control' not in get_type_hints(func):
        run = kwargs['control']
        del kwargs['control']
    else:
        run = True

    if run:
        func(**kwargs)

    return {k: int(v) for k, v in kwargs.items() if isinstance(v, qp.IntBuf)}


def _sample(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    return {
        k: v() if isinstance(v, Callable) else random.choice(v) if isinstance(v, Sequence) else v
        for k, v in kwargs.items()}
