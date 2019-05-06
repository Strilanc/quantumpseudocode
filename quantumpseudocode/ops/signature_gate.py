import inspect
from typing import List, Union, Any, get_type_hints, TypeVar

import quantumpseudocode as qp

T = TypeVar('T')


SignatureGateArgTypes = Union[qp.RValue[Any], 'qp.Operation']


class SignatureGate:
    def alloc_prefix(self):
        """String to describe temp registers created to perform this gate."""
        return ''

    def emulate(self, forward: bool, *args, **kwargs):
        raise NotImplementedError()

    def do(self, controls: 'qp.QubitIntersection', *args, **kwargs):
        raise NotImplementedError()

    def describe(self, *args) -> str:
        raise NotImplementedError()

    def _signature(self) -> List[type]:
        sig = inspect.signature(self.emulate)
        type_hints = get_type_hints(self.emulate)
        result = []
        saw_forward = False
        for p in sig.parameters.values():
            if not saw_forward:
                assert p.name == 'forward'
                saw_forward = True
                continue
            assert p.name in type_hints
            t = type_hints[p.name]
            result.append(t)
        assert saw_forward
        return result

    def operation(self, *args, **kwargs) -> 'qp.Operation':
        v = qp.ArgsAndKwargs(args, kwargs).match_parameters(self.do, skip=1)
        def wrap_constants(x: qp.ArgParameter):
            if x.parameter_type == qp.Quint:
                if isinstance(x.arg, int):
                    return qp.IntRValue(x.arg)
            if x.parameter_type == qp.Qubit:
                if isinstance(x.arg, bool):
                    return qp.BoolRValue(x.arg)
            return x.arg
        return qp.SignatureOperation(self, v.map(wrap_constants))

    def __call__(self, *args, **kwargs):
        return self.operation(*args, **kwargs)

    def __str__(self):
        try:
            return self.describe(*[str(e) for e in self._signature()])
        except TypeError:
            return '[DESCRIBE-ERR] ' + object.__str__(self)
