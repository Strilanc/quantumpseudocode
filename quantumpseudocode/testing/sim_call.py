from typing import Any, Callable

import quantumpseudocode as qp


def sim_call(func: Callable,
             *args, **kwargs) -> 'qp.ArgsAndKwargs':

    def qalloc_as_needed(a: qp.ArgParameter):
        if a.parameter_type is None:
            raise ValueError('Function arguments must be annotated, so that '
                             'quantum values can be allocated if needed.')

        if a.parameter_type is qp.Quint:
            if isinstance(a.arg, qp.IntBuf):
                n = len(a.arg)
            else:
                n = a.arg.bit_length()
            result = qp.qalloc_int(bits=n, name=a.parameter.name)
            result ^= int(a.arg)
            return result

        if a.parameter_type is qp.Qubit:
            result = qp.qalloc(name=a.parameter.name)
            if a.arg:
                result ^= True
            return result

        return a.arg

    def qfree_as_needed(a: Any):
        if isinstance(a, (qp.Quint, qp.Qureg, qp.Qubit)):
            result = qp.measure(a, reset=True)
            qp.qfree(a)
            return result
        return a

    matched = qp.ArgsAndKwargs(args, kwargs).match_parameters(func)
    with qp.Sim():
        allocated = matched.map(qalloc_as_needed)
        allocated.pass_into(func)
        return allocated.map(qfree_as_needed)
