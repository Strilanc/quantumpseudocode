import random
from typing import List, Union, Callable, Any, Optional, Tuple, Set, Dict

import quantumpseudocode as qp


def separate_controls(op: 'qp.Operation') -> 'Tuple[qp.Operation, qp.QubitIntersection]':
     if isinstance(op, qp.ControlledOperation):
         return op.uncontrolled, op.controls
     return op, qp.QubitIntersection.EMPTY


def _toggle_targets(lvalue: 'qp.Qureg') -> 'qp.Qureg':
    return lvalue


class Sim(qp.Lens):
    def __init__(self,
                 enforce_release_at_zero: bool = True,
                 phase_fixup_bias: Optional[bool] = None,
                 emulate_additions: bool = False):
        super().__init__()
        self._bool_state = {}  # type: Dict[qp.Qubit, bool]
        self.enforce_release_at_zero = enforce_release_at_zero
        self.phase_fixup_bias = phase_fixup_bias
        self.emulate_additions = emulate_additions

    def snapshot(self):
        return dict(self._bool_state)

    def _read_qubit(self, qubit: 'qp.Qubit') -> bool:
        return self._bool_state[qubit]

    def _write_qubit(self, qubit: 'qp.Qubit', new_val: bool):
        self._bool_state[qubit] = new_val

    def _read_quint(self, quint: 'qp.Quint') -> int:
        t = 0
        for q in reversed(quint):
            t <<= 1
            t |= 1 if self._read_qubit(q) else 0
        return t

    def _write_quint(self, quint: 'qp.Quint', new_val: int):
        for i, q in enumerate(quint):
            self._write_qubit(q, bool((new_val >> i) & 1))

    def apply_op_via_emulation(self, op: 'qp.Operation', *, forward: bool = True):
        locs = op.state_locations()
        args = self.resolve_location(locs)
        op.mutate_state(forward, args)
        self.overwrite_location(locs, args)

    def resolve_location(self, loc: Union[qp.Quint, qp.Qubit, qp.Qureg, qp.ArgsAndKwargs, qp.IntRValue, qp.BoolRValue], allow_mutate: bool = True):
        if isinstance(loc, qp.Qubit):
            val = self._read_qubit(loc)
            if allow_mutate:
                return qp.Mutable(val)
            return val
        if isinstance(loc, qp.Qureg):
            val = [self._read_qubit(q) for q in loc]
            if allow_mutate:
                return qp.Mutable(val)
            return val
        if isinstance(loc, qp.QubitIntersection):
            return all(self._read_qubit(q) for q in loc)
        if isinstance(loc, qp.Quint):
            t = self._read_quint(loc)
            if allow_mutate:
                return qp.Mutable(t)
            return t
        if isinstance(loc, qp.ArgsAndKwargs):
            return loc.map(self.resolve_location)
        if isinstance(loc, (qp.IntRValue, qp.BoolRValue)):
            return loc.val
        if isinstance(loc, (int, bool)):
            return loc
        if isinstance(loc, qp.ControlledRValue):
            if self.resolve_location(loc.controls):
                return self.resolve_location(loc.rvalue, allow_mutate=False)
            else:
                return 0
        if isinstance(loc, qp.LookupRValue):
            address = self.resolve_location(loc.address, allow_mutate=False)
            return loc.table.values[address]
        if isinstance(loc, qp.QuintRValue):
            return self.resolve_location(loc.val, allow_mutate=False)
        if isinstance(loc, qp.Operation):
            return qp.SubEffect(
                op=loc,
                args=self.resolve_location(loc.state_locations()))
        raise NotImplementedError(
            "Unrecognized type for resolve_location ({!r}): {!r}".format(type(loc), loc))

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

    def overwrite_location(self, loc: Union[qp.Quint, qp.Qubit, qp.Qureg, qp.ArgsAndKwargs], val: Union['qp.Mutable', Any]):
        if isinstance(loc, qp.Qubit):
            self._write_qubit(loc, val.val)
        elif isinstance(loc, qp.Qureg):
            for q, v in zip(loc, val.val):
                self._write_qubit(q, v)
        elif isinstance(loc, qp.Quint):
            self._write_quint(loc, val.val)
        elif isinstance(loc, qp.ArgsAndKwargs):
            loc.zip_map(val, self.overwrite_location)
        elif isinstance(loc, (qp.IntRValue, qp.BoolRValue)):
            assert self.resolve_location(loc) == loc.val
        elif isinstance(loc, (bool, int)):
            assert self.resolve_location(loc) == val
        elif isinstance(loc, qp.ControlledRValue):
            if self.resolve_location(loc.controls):
                self.overwrite_location(loc.rvalue, val)
        elif isinstance(loc, qp.LookupRValue):
            assert self.resolve_location(loc) == val
        elif isinstance(loc, qp.QuintRValue):
            assert self.resolve_location(loc) == val
        elif isinstance(loc, qp.Operation):
            self.overwrite_location(loc.state_locations(), val.args)
        else:
            raise NotImplementedError(
                "Unrecognized type for overwrite_location {!r}".format(loc))

    def modify(self, operation: 'qp.Operation'):
        op, cnt = separate_controls(operation)

        if isinstance(op, qp.AllocQuregOperation):
            assert len(cnt) == 0
            for q in op.qureg:
                assert q not in self._bool_state
                if op.x_basis:
                    self._write_qubit(q, random.random() < 0.5)
                else:
                    self._write_qubit(q, False)
            return []

        if self.emulate_additions:
            emulate = False
            o = op
            if isinstance(op, qp.InverseOperation):
                o = op.sub
            elif isinstance(o, (qp.PlusEqual, qp.EffectIfLessThan)):
                emulate = True
            if emulate:
                self.apply_op_via_emulation(operation)
                return []

        if isinstance(op, qp.ReleaseQuregOperation):
            assert len(cnt) == 0
            for q in op.qureg:
                if self.enforce_release_at_zero and not op.dirty:
                    assert self._read_qubit(q) == 0, 'Failed to uncompute {}'.format(q)
                del self._bool_state[q]
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

        if isinstance(op, qp.SignatureOperation):
            if op.gate == qp.OP_TOGGLE:
                targets = op.args.pass_into(_toggle_targets)
                assert set(targets).isdisjoint(cnt)
                if all(self._read_qubit(q) for q in cnt):
                    for t in targets:
                        self._write_qubit(t, not self._read_qubit(t))
                return []

        if op == qp.OP_PHASE_FLIP:
            # skip
            return []

        return [operation]
