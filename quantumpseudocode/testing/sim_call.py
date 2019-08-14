from typing import Any, Callable

import quantumpseudocode as qp


class ModInt:
    def __init__(self, val: int, modulus: int):
        self.val = val
        self.modulus = modulus


def sim_call(func: Callable,
             *args, **kwargs) -> 'qp.ArgsAndKwargs':

    def qalloc_as_needed(a: qp.ArgParameter):
        if a.parameter_type is None:
            raise ValueError('Function arguments must be annotated, so that '
                             'quantum values can be allocated if needed.')

        if a.parameter_type is qp.Quint:
            if isinstance(a.arg, qp.IntBuf):
                n = len(a.arg)
            elif isinstance(a.arg, int):
                n = a.arg.bit_length()
            else:
                raise ValueError('Unsupported Quint input: {}'.format(a))
            result = qp.qalloc_int(bits=n, name=a.parameter.name)
            result.init(a.arg)
            return result

        if a.parameter_type is qp.QuintMod:
            assert isinstance(a.arg, ModInt)
            result = qp.qalloc_int_mod(modulus=a.arg.modulus,
                                       name=a.parameter.name)
            result.init(a.arg.val)
            return result

        if a.parameter_type is qp.Qubit:
            result = qp.alloc(name=a.parameter.name)
            result.init(a.arg)
            return result

        return a.arg

    def qfree_as_needed(a: Any):
        if isinstance(a, (qp.Quint, qp.Qureg, qp.Qubit, qp.QuintMod)):
            result = qp.measure(a, reset=True)
            qp.free(a)
            return result
        return a

    matched = qp.ArgsAndKwargs(args, kwargs).match_parameters(func)
    with qp.Sim():
        allocated = matched.map(qalloc_as_needed)
        allocated.pass_into(func)
        return allocated.map(qfree_as_needed)
