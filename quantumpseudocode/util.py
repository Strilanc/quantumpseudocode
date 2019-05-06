import cirq
import inspect
from typing import Callable, TypeVar, Generic, List, Dict, Iterable, Any, get_type_hints, Optional, Tuple

T = TypeVar('T')
T2 = TypeVar('T2')
R = TypeVar('R')


def ceil_lg2(x: int) -> int:
    if x <= 1:
        return 0
    return (x - 1).bit_length()


def floor_lg2(x: int) -> int:
    assert x >= 1
    return x.bit_length() - 1


class ArgParameter:
    def __init__(self,
                 arg: Any,
                 parameter: inspect.Parameter,
                 parameter_type: Optional[type]):
        self.arg = arg
        self.parameter = parameter
        self.parameter_type = parameter_type

    def __repr__(self):
        return 'qp.ArgParameter({!r}, {!r}, {!r})'.format(
            self.arg,
            self.parameter,
            self.parameter_type)


@cirq.value_equality(unhashable=True)
class ArgsAndKwargs(Generic[T]):
    def __init__(self, args: List[T], kwargs: Dict[str, T]):
        self.args = args
        self.kwargs = kwargs

    def _value_equality_values_(self):
        return self.args, self.kwargs

    def pass_into(self, func: Callable[[Any], R]) -> R:
        return func(*self.args, **self.kwargs)

    def match_parameters(self,
                         func: Callable,
                         skip: int = 0) -> 'ArgsAndKwargs[ArgParameter]':
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
        result_args = []

        for p, a in zip(list(sig.parameters.values())[skip:], self.args):
            assert p.name not in self.kwargs
            assert p.kind in [inspect.Parameter.POSITIONAL_ONLY,
                              inspect.Parameter.POSITIONAL_OR_KEYWORD]
            t = type_hints.get(p.name, None)
            result_args.append(ArgParameter(a, p, t))

        result_kwargs = {}
        for k, a in self.kwargs.items():
            p = sig.parameters[k]
            assert p.kind in [inspect.Parameter.KEYWORD_ONLY,
                              inspect.Parameter.POSITIONAL_OR_KEYWORD]
            t = type_hints.get(k, None)
            result_kwargs[k] = ArgParameter(a, p, t)

        if len(result_args) + len(result_kwargs) + skip != len(sig.parameters):
            raise AssertionError(
                'Unmatched arguments.\n'
                'Args: {}\nKwargs: {}\nSkip: {!r}\nSignature: {}'.format(
                    result_args,
                    sorted(result_kwargs.keys()),
                    skip,
                    sig.parameters))
        assert len(result_args) + len(result_kwargs) + skip == len(sig.parameters)
        return ArgsAndKwargs(result_args, result_kwargs)

    def map(self, func: Callable[[T], R]) -> 'ArgsAndKwargs[R]':
        return ArgsAndKwargs(
            [func(e) for e in self.args],
            {k: func(v) for k, v in self.kwargs.items()})

    def key_map(self, func: Callable[[Any, T], R]) -> 'ArgsAndKwargs[R]':
        return ArgsAndKwargs(
            [func(i, e) for i, e in enumerate(self.args)],
            {k: func(k, v) for k, v in self.kwargs.items()})

    def zip_map(self,
                other: 'ArgsAndKwargs[T2]',
                func: Callable[[T, T2], R]
                ) -> 'ArgsAndKwargs[R]':
        assert len(self.args) == len(other.args)
        assert self.kwargs.keys() == other.kwargs.keys()
        return ArgsAndKwargs(
            [
                func(e1, e2)
                for e1, e2 in zip(self.args, other.args)
            ],
            {
                k: func(self.kwargs[k], other.kwargs[k])
                for k in self.kwargs.keys()
            })

    def __str__(self):
        parts = []
        for arg in self.args:
            parts.append(str(arg))
        for k, v in self.kwargs.items():
            parts.append('{}={}'.format(k, v))
        return '({})'.format(', '.join(parts))

    def repr_args(self):
        parts = []
        for arg in self.args:
            parts.append(repr(arg))
        for k, v in self.kwargs.items():
            parts.append('{}={!r}'.format(k, v))
        return ', '.join(parts)

    def __repr__(self):
        return 'qp.ArgsAndKwargs({!r}, {!r})'.format(
            self.args,
            self.kwargs)


class MultiWith:
    def __init__(self, items: Iterable[Any]):
        self.items = tuple(items)

    def __enter__(self):
        return tuple(item.__enter__() for item in self.items)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for item in self.items:
            item.__exit__(exc_type, exc_val, exc_tb)


def leading_zero_bit_count(v: int) -> Optional[int]:
    """Returns the largest integer k such that v is divisible by 2**k."""
    if v == 0:
        return None
    return (v ^ (v - 1)).bit_length() - 1


def _extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
    x0, x1, y0, y1 = 0, 1, 1, 0
    while a != 0:
        q, b, a = b // a, a, b % a
        y0, y1 = y1, y0 - q * y1
        x0, x1 = x1, x0 - q * x1
    return b, x0, y0


def modular_multiplicative_inverse(a: int, modulus: int) -> Optional[int]:
    g, x, y = _extended_gcd(a % modulus, modulus)
    if g != 1:
        return None
    return x % modulus


def popcnt(x: int) -> int:
    assert x >= 0
    t = 0
    while x:
        x &= x - 1
        t += 1
    return t
