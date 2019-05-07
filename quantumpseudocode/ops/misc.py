from typing import Union, Tuple, Any, TypeVar, Generic

import cirq

import quantumpseudocode as qp

T = TypeVar('T')


@cirq.value_equality(unhashable=True)
class Mutable(Generic[T]):
    def __init__(self, val: T):
        self.val = val

    def _value_equality_values_(self):
        return self.val

    def __str__(self):
        return 'mutable({})'.format(self.val)

    def __repr__(self):
        return 'qp.Mutable({!r})'.format(self.val)

    def __int__(self):
        return int(self.val)

    def __bool__(self):
        return bool(self.val)


class SubEffect:
    def __init__(self, *, op: 'qp.Operation', args: 'qp.ArgsAndKwargs'):
        self.op = op
        self.args = args


class HeldMultipleRValue:
    def __init__(self,
                 args: qp.ArgsAndKwargs['qp.SigHoldArgTypes'],
                 name_prefix: str = ''):
        def hold_map(key: Any,
                     e: 'qp.SigHoldArgTypes'
                     ) -> Tuple[bool,
                                Union['qp.Operation',
                                      'qp.HeldRValueManager']]:
            if isinstance(e, qp.RValue):
                return True, qp.HeldRValueManager(
                    e,
                    controls=qp.QubitIntersection.EMPTY,
                    name=name_prefix + str(key))
            return False, e

        self.holders = args.key_map(hold_map)

    def __enter__(self) -> qp.ArgsAndKwargs[Any]:
        def enter_map(x):
            b, e = x
            if b:
                return e.__enter__()
            return e
        return self.holders.map(enter_map)

    def __exit__(self, exc_type, exc_val, exc_tb):
        def exit_map(x):
            b, e = x
            if b:
                e.__exit__(exc_type, exc_val, exc_tb)
        _ = self.holders.map(exit_map)
