import functools
import inspect
import random
from typing import Any, Callable, Iterable, Sequence, get_type_hints, Union, Dict, TypeVar, Generic, List

import quantumpseudocode as qp
from quantumpseudocode.testing.verify_semi_quantum import _apply_quantum, _sample

TSample = TypeVar('TSample')


def assert_self_inverse_is_consistent(
        func: Callable,
        *,
        fuzz_space: Dict[str, Any] = None,
        fuzz_count: int = 0,
        fixed: Sequence[Dict[str, Any]] = ()):
    assert fuzz_count or fixed
    sig = inspect.signature(func)

    # Note: functools.partial gives incorrect type hints.
    def partial(f, **cs):
        @functools.wraps(f)
        def w(**ks):
            f(**ks, **cs)
        return w

    if 'forward' in sig.parameters:
        forward_func = partial(func, forward=True)
        inverse_func = partial(func, forward=False)
    elif 'inverse' in sig.parameters:
        forward_func = partial(func, inverse=False)
        inverse_func = partial(func, inverse=True)
    else:
        forward_func = func
        inverse_func = func

    assert_inverse_is_consistent(
        forward_func,
        inverse_func,
        fuzz_space=fuzz_space,
        fuzz_count=fuzz_count,
        fixed=fixed)


def assert_inverse_is_consistent(
        func: Callable,
        inverse_func: Callable,
        *,
        fuzz_space: Dict[str, Any] = None,
        fuzz_count: int = 0,
        fixed: Sequence[Dict[str, Any]] = ()):
    assert fuzz_count or fixed
    has_control = 'control' in inspect.signature(func).parameters
    for kwargs in fixed:
        _assert_inverse_is_consistent(func,
                                      inverse_func,
                                      kwargs,
                                      has_control)
    for _ in range(fuzz_count):
        _assert_inverse_is_consistent(func,
                                      inverse_func,
                                      _sample(fuzz_space),
                                      has_control)


def _assert_inverse_is_consistent(
        func: Callable,
        inverse_func: Callable,
        kwargs: Dict[str, Any],
        has_control: bool):

    if 'control' not in kwargs and has_control:
        for control in [False, True]:
            _assert_inverse_is_consistent(func,
                                          inverse_func,
                                          {**kwargs, 'control': control},
                                          True)
        return

    def compose(f1, f2):
        @functools.wraps(f1)
        def f(**ks):
            f1(**ks)
            f2(**ks)
        return f

    @functools.wraps(func)
    def identity(**ks):
        pass

    f_then_i = _apply_quantum(compose(func, inverse_func), kwargs)
    i_then_f = _apply_quantum(compose(inverse_func, func), kwargs)
    i = _apply_quantum(identity, kwargs)
    assert f_then_i == i_then_f == i, '\n'.join([
        'Inconsistent inverse.\n'
        '\n'
        f'func: {repr(func)}\n'
        f'inverse_func: {repr(func)}\n'
        f'kwargs: {repr(kwargs)}\n'
        '\n'
        f'result of identity:\n'
        f'{repr(i)}\n'
        f'result of func then inverse_func:\n'
        f'{repr(f_then_i)}\n'
        f'result of inverse_func then func:\n'
        f'{repr(i_then_f)}\n'
    ])
