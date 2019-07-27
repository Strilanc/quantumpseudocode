from typing import Union, Tuple, Any, TypeVar, Generic

import cirq

import quantumpseudocode as qp

T = TypeVar('T')


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
