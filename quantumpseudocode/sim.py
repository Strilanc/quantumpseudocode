import random
from typing import List, Union, Callable, Any, Optional, Tuple, Set, Dict, Iterable

import quantumpseudocode as qp
import quantumpseudocode.ops.operation
import quantumpseudocode.lens


def separate_controls(op: 'qp.Operation') -> 'Tuple[qp.Operation, qp.QubitIntersection]':
     if isinstance(op, qp.ControlledOperation):
         return op.uncontrolled, op.controls
     return op, qp.QubitIntersection.EMPTY


def _toggle_targets(lvalue: 'qp.Qureg') -> 'qp.Qureg':
    return lvalue


class Sim(quantumpseudocode.lens.Lens, quantumpseudocode.ops.operation.ClassicalSimState):
    def __init__(self,
                 enforce_release_at_zero: bool = True,
                 phase_fixup_bias: Optional[bool] = None,
                 emulate_additions: bool = False):
        super().__init__()
        self._int_state: Dict[str, 'qp.IntBuf'] = {}
        self.enforce_release_at_zero = enforce_release_at_zero
        self.phase_fixup_bias = phase_fixup_bias
        self.emulate_additions = emulate_additions

    def snapshot(self):
        return dict(self._int_state)

    def _read_qubit(self, qubit: 'qp.Qubit') -> bool:
        return self._int_state[qubit.name][qubit.index or 0]

    def _write_qubit(self, qubit: 'qp.Qubit', new_val: bool):
        self._int_state[qubit.name][qubit.index or 0] = new_val

    def quint_buf(self, quint: 'qp.Quint') -> qp.IntBuf:
        if isinstance(quint.qureg, qp.NamedQureg):
            return self._int_state[quint.qureg.name]
        return qp.IntBuf(qp.RawConcatBuffer.balanced_concat([
            self._int_state[k][s] for k, s in _fuse(quint.qureg)
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

    def modify(self, operation: 'qp.Operation'):
        op, cnt = separate_controls(operation)

        if isinstance(op, qp.AllocQuregOperation):
            assert len(cnt) == 0
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
            return []

        if self.emulate_additions:
            emulate = False
            o = op
            if isinstance(op, qp.InverseOperation):
                o = op.sub
            if isinstance(o, (qp.PlusEqual, qp.EffectIfLessThan)):
                emulate = True
            if emulate:
                operation.mutate_state(self, True)
                return []

        if isinstance(op, qp.ReleaseQuregOperation):
            assert len(cnt) == 0

            for q in op.qureg:
                if self.enforce_release_at_zero and not op.dirty:
                    assert self._read_qubit(q) == 0, 'Failed to uncompute {}'.format(q)

            if isinstance(op.qureg, qp.NamedQureg):
                assert op.qureg.name in self._int_state
                del self._int_state[op.qureg.name]
            else:
                for q in op.qureg:
                    assert q.name in self._int_state
                    del self._int_state[q.name]

            return []

        if isinstance(op, qp.MeasureOperation):
            assert len(cnt) == 0
            assert op.raw_results is None
            results = [self._read_qubit(q) for q in op.targets]
            if op.reset:
                for q in op.targets:
                    self._write_qubit(q, False)
            op.raw_results = tuple(results)
            return []

        if isinstance(op, qp.MeasureXForPhaseKickOperation):
            r = self.phase_fixup_bias
            if r is None:
                r = random.random() < 0.5
            op.result = r
            self._write_qubit(op.target, False)
            return []

        if isinstance(op, qp.Toggle):
            targets = op._args.pass_into(_toggle_targets)
            assert set(targets).isdisjoint(cnt)
            if all(self._read_qubit(q) for q in cnt):
                for t in targets:
                    self._write_qubit(t, not self._read_qubit(t))
            return []

        if op == qp.OP_PHASE_FLIP:
            # skip
            return []

        return [operation]


def _fuse(qubits: Iterable[qp.Qubit]) -> List[Tuple[str, slice]]:
    result: List[Tuple[str, slice]] = []
    cur_name = None
    cur_start = None
    cur_end = None

    def flush():
        if cur_name is not None:
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
