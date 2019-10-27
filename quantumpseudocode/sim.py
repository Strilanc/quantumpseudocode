import random
from typing import List, Union, Callable, Any, Optional, Tuple, Set, Dict, Iterable

import quantumpseudocode as qp
import quantumpseudocode.operating_context
import quantumpseudocode.ops.operation


class Sim(quantumpseudocode.operating_context.OperatingContext, quantumpseudocode.ops.operation.ClassicalSimState):
    def __init__(self,
                 enforce_release_at_zero: bool = True,
                 phase_fixup_bias: Optional[bool] = None,
                 emulate_additions: bool = False):
        super().__init__()
        self._int_state: Dict[str, 'qp.IntBuf'] = {}
        self.enforce_release_at_zero = enforce_release_at_zero
        self.phase_fixup_bias = phase_fixup_bias
        self.emulate_additions = emulate_additions
        self._phase_degrees = 0

    @property
    def phase_degrees(self):
        return self._phase_degrees

    @phase_degrees.setter
    def phase_degrees(self, new_value):
        self._phase_degrees = new_value % 360

    def __enter__(self):
        # HACK: Prevent name pollution across simulation runs.
        super().__enter__()
        qp.UniqueHandle._free_handles = {}
        qp.UniqueHandle._next_handle = {}
        return self

    def snapshot(self):
        return dict(self._int_state)

    def _read_qubit(self, qubit: 'qp.Qubit') -> bool:
        return self._int_state[qubit.name][qubit.index or 0]

    def _write_qubit(self, qubit: 'qp.Qubit', new_val: bool):
        self._int_state[qubit.name][qubit.index or 0] = new_val

    def quint_buf(self, quint: 'qp.Quint') -> qp.IntBuf:
        if len(quint) == 0:
            return qp.IntBuf.raw(val=0, length=0)
        if isinstance(quint.qureg, qp.NamedQureg):
            return self._int_state[quint.qureg.name]
        fused = _fuse(quint.qureg)
        return qp.IntBuf(qp.RawConcatBuffer.balanced_concat([
            self._int_state[name][rng]._buf for name, rng in fused
        ]))

    def resolve_location(self, loc: Any, allow_mutate: bool = True):
        resolver = getattr(loc, 'resolve', None)
        if resolver is not None:
            return resolver(self, allow_mutate)
        if isinstance(loc, (int, bool)):
            return loc
        raise NotImplementedError(
            "Don't know how to resolve type {!r}. Value: {!r}".format(type(loc), loc))

    def randomize_location(self, loc: Union[qp.Quint, qp.Qubit, qp.Qureg]):
        if isinstance(loc, qp.Qubit):
            self._write_qubit(loc, random.random() < 0.5)
        elif isinstance(loc, qp.Qureg):
            for q in loc:
                self._write_qubit(q, random.random() < 0.5)
        elif isinstance(loc, qp.Quint):
            for q in loc:
                self._write_qubit(q, random.random() < 0.5)
        elif isinstance(loc, qp.ControlledRValue):
            if self.resolve_location(loc.controls):
                self.randomize_location(loc.rvalue)
        else:
            raise NotImplementedError(
                "Unrecognized type for randomize_location {!r}".format(loc))

    def measurement_based_uncomputation_result_chooser(self) -> Callable[[], bool]:
        if self.phase_fixup_bias is not None:
            return lambda: self.phase_fixup_bias
        return lambda: random.random() < 0.5

    def alloc(self, name: str, length: int, *, x_basis: bool = False):
        assert name not in self._int_state, "Double allocated {}".format(name)
        self._int_state[name] = qp.IntBuf.raw(
            val=random.randint(0, (1 << length) - 1) if x_basis else 0,
            length=length)

    def release(self, name: str, *, dirty: bool = False):
        assert name in self._int_state
        if self.enforce_release_at_zero and not dirty:
            b = self._int_state[name]
            assert int(b) == 0, 'Failed to uncompute {}={} before release'.format(name, b)
        del self._int_state[name]

    def do(self, operation: 'qp.Operation'):
        op, cnt = qp.ControlledOperation.split(operation)
        op.validate_controls(cnt)
        if self.resolve_location(cnt, False):
            op.mutate_state(self, True)
        return []


def _fuse(qubits: Iterable[qp.Qubit]) -> List[Tuple[str, slice]]:
    result: List[Tuple[str, slice]] = []
    cur_name = None
    cur_start = None
    cur_end = None

    def flush():
        if cur_name is not None and cur_end > cur_start:
            result.append((cur_name, slice(cur_start, cur_end)))

    for q in qubits:
        if q.name == cur_name and q.index == cur_end:
            cur_end += 1
        else:
            flush()
            cur_name = q.name
            cur_start = q.index or 0
            cur_end = cur_start + 1
    flush()
    return result
