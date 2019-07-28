from typing import Optional, Any, Tuple, Iterable

import cirq

import quantumpseudocode as qp
from .rvalue import RValue


@cirq.value_equality
class QubitRValue(RValue[bool]):
    def __init__(self, val: 'qp.Qubit'):
        self.val = val

    def resolve(self, sim_state: 'qp.ClassicalSimState', allow_mutate: bool):
        return self.val.resolve(sim_state, False)

    def _value_equality_values_(self):
        return self.val

    def qureg_deps(self) -> Iterable['qp.Qureg']:
        return [qp.RawQureg([self.val])]

    def value_from_resolved_deps(self, args: Tuple[int, ...]
                                 ) -> bool:
        return args[0] != 0

    def existing_storage_location(self) -> Any:
        return self.val

    def make_storage_location(self, name: Optional[str] = None):
        raise ValueError('existing storage')

    def init_storage_location(self,
                              location: Any,
                              controls: 'qp.QubitIntersection'):
        raise ValueError('existing storage')

    def del_storage_location(self,
                             location: Any,
                             controls: 'qp.QubitIntersection'):
        raise ValueError('existing storage')

    def __str__(self):
        return 'rval({})'.format(self.val)

    def __repr__(self):
        return 'qp.QubitRValue({!r})'.format(self.val)


@cirq.value_equality
class QuintRValue(RValue[int]):
    def __init__(self, val: 'qp.Quint'):
        self.val = val

    def resolve(self, sim_state: 'qp.ClassicalSimState', allow_mutate: bool):
        return self.val.resolve(sim_state, False)

    def _value_equality_values_(self):
        return self.val

    def qureg_deps(self) -> Iterable['qp.Qureg']:
        return [self.val.qureg]

    def value_from_resolved_deps(self, args: Tuple[int, ...]
                                 ) -> int:
        return args[0]

    def existing_storage_location(self) -> Any:
        return self.val

    def make_storage_location(self, name: Optional[str] = None):
        return qp.Quint(qp.NamedQureg(name, len(self.val)))

    def init_storage_location(self,
                              location: Any,
                              controls: 'qp.QubitIntersection'):
        qp.emit(qp.XorEqual(location, self.val).controlled_by(controls))

    def del_storage_location(self,
                             location: Any,
                             controls: 'qp.QubitIntersection'):
        qp.emit(qp.XorEqual(location, self.val).controlled_by(controls))

    def __str__(self):
        return 'rval({})'.format(self.val)

    def __repr__(self):
        return 'qp.QuintRValue({!r})'.format(self.val)
