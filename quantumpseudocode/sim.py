import random
from typing import List, Union, Callable, Any, Optional, Tuple, Set, Dict, Iterable

import quantumpseudocode as qp
import quantumpseudocode.logger
import quantumpseudocode.ops.operation


def _toggle_targets(lvalue: 'qp.Qureg') -> 'qp.Qureg':
    return lvalue


class Sim(quantumpseudocode.logger.Logger, quantumpseudocode.ops.operation.ClassicalSimState):
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
        qp.UniqueHandle._free_handles = {}
        qp.UniqueHandle._next_handle = {}
        return super().__enter__()

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

    def log(self, operation: 'qp.Operation'):
        op, cnt = qp.ControlledOperation.split(operation)

        if isinstance(op, qp.AllocQuregOperation):
            assert cnt == qp.QubitIntersection.ALWAYS
            if isinstance(op.qureg, qp.NamedQureg):
                assert op.qureg.name not in self._int_state, "Double allocated {}".format(op.qureg.name)
                self._int_state[op.qureg.name] = qp.IntBuf.raw(
                    val=random.randint(0, (1 << len(op.qureg)) - 1) if op.x_basis else 0,
                    length=len(op.qureg))
            else:
                for q in op.qureg:
                    assert q.name not in self._int_state, "Double allocated {}".format(q.name)
                    self._int_state[q.name] = qp.IntBuf.raw(
                        val=random.randint(0, 1) if op.x_basis else 0,
                        length=1)
        elif isinstance(op, qp.ReleaseQuregOperation):
            assert cnt == qp.QubitIntersection.ALWAYS

            for q in op.qureg:
                if self.enforce_release_at_zero and not op.dirty:
                    assert self._read_qubit(q) == 0, 'Failed to uncompute {} before release'.format(q)

            if isinstance(op.qureg, qp.NamedQureg):
                assert op.qureg.name in self._int_state
                del self._int_state[op.qureg.name]
            else:
                for q in op.qureg:
                    assert q.name in self._int_state
                    del self._int_state[q.name]
        elif isinstance(op, (qp.MeasureOperation,
                             qp.StartMeasurementBasedUncomputation,
                             qp.EndMeasurementBasedComputationOp)):
            assert cnt == qp.QubitIntersection.ALWAYS
            op.mutate_state(self, True)
        elif isinstance(op, qp.Toggle):
            targets = op.lvalue
            assert set(targets).isdisjoint(cnt.qubits)
            if cnt.bit and all(self._read_qubit(q) for q in cnt.qubits):
                for t in targets:
                    self._write_qubit(t, not self._read_qubit(t))
        elif op == qp.OP_PHASE_FLIP:
            if self.resolve_location(cnt, allow_mutate=False):
                self.phase_degrees += 180
        else:
            raise NotImplementedError(f"Unrecognized operation: {op!r}")


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
