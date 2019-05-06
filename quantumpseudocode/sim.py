import random
from typing import List, Union, Callable, Any, Optional, Tuple, Set, Dict

import quantumpseudocode


def separate_controls(op: 'quantumpseudocode.Operation') -> 'Tuple[quantumpseudocode.Operation, quantumpseudocode.QubitIntersection]':
     if isinstance(op, quantumpseudocode.ControlledOperation):
         return op.uncontrolled, op.controls
     return op, quantumpseudocode.QubitIntersection.EMPTY


def _toggle_targets(lvalue: 'quantumpseudocode.Qureg') -> 'quantumpseudocode.Qureg':
    return lvalue


class Sim(quantumpseudocode.Lens):
    def __init__(self,
                 enforce_release_at_zero: bool = True,
                 phase_fixup_bias: Optional[bool] = None,
                 emulate_additions: bool = False):
        super().__init__()
        self._bool_state = {}  # type: Dict[quantumpseudocode.Qubit, bool]
        self.enforce_release_at_zero = enforce_release_at_zero
        self.phase_fixup_bias = phase_fixup_bias
        self.emulate_additions = emulate_additions

    def snapshot(self):
        return dict(self._bool_state)

    def _read_qubit(self, qubit: 'quantumpseudocode.Qubit') -> bool:
        return self._bool_state[qubit]

    def _write_qubit(self, qubit: 'quantumpseudocode.Qubit', new_val: bool):
        self._bool_state[qubit] = new_val

    def _read_quint(self, quint: 'quantumpseudocode.Quint') -> int:
        t = 0
        for q in reversed(quint):
            t <<= 1
            t |= 1 if self._read_qubit(q) else 0
        return t

    def _write_quint(self, quint: 'quantumpseudocode.Quint', new_val: int):
        for i, q in enumerate(quint):
            self._write_qubit(q, bool((new_val >> i) & 1))

    def apply_op_via_emulation(self, op: 'quantumpseudocode.Operation', *, forward: bool = True):
        locs = op.state_locations()
        args = self.resolve_location(locs)
        op.mutate_state(forward, args)
        self.overwrite_location(locs, args)

    def resolve_location(self, loc: Union[quantumpseudocode.Quint, quantumpseudocode.Qubit, quantumpseudocode.Qureg, quantumpseudocode.ArgsAndKwargs, quantumpseudocode.IntRValue, quantumpseudocode.BoolRValue], allow_mutate: bool = True):
        if isinstance(loc, quantumpseudocode.Qubit):
            val = self._read_qubit(loc)
            if allow_mutate:
                return quantumpseudocode.Mutable(val)
            return val
        if isinstance(loc, quantumpseudocode.Qureg):
            val = [self._read_qubit(q) for q in loc]
            if allow_mutate:
                return quantumpseudocode.Mutable(val)
            return val
        if isinstance(loc, quantumpseudocode.QubitIntersection):
            return all(self._read_qubit(q) for q in loc)
        if isinstance(loc, quantumpseudocode.Quint):
            t = self._read_quint(loc)
            if allow_mutate:
                return quantumpseudocode.Mutable(t)
            return t
        if isinstance(loc, quantumpseudocode.ArgsAndKwargs):
            return loc.map(self.resolve_location)
        if isinstance(loc, (quantumpseudocode.IntRValue, quantumpseudocode.BoolRValue)):
            return loc.val
        if isinstance(loc, (int, bool)):
            return loc
        if isinstance(loc, quantumpseudocode.ControlledRValue):
            if self.resolve_location(loc.controls):
                return self.resolve_location(loc.rvalue, allow_mutate=False)
            else:
                return 0
        if isinstance(loc, quantumpseudocode.LookupRValue):
            address = self.resolve_location(loc.address, allow_mutate=False)
            return loc.table.values[address]
        if isinstance(loc, quantumpseudocode.QuintRValue):
            return self.resolve_location(loc.val, allow_mutate=False)
        if isinstance(loc, quantumpseudocode.Operation):
            return quantumpseudocode.SubEffect(
                op=loc,
                args=self.resolve_location(loc.state_locations()))
        raise NotImplementedError(
            "Unrecognized type for resolve_location ({!r}): {!r}".format(type(loc), loc))

    def randomize_location(self, loc: Union[quantumpseudocode.Quint, quantumpseudocode.Qubit, quantumpseudocode.Qureg]):
        if isinstance(loc, quantumpseudocode.Qubit):
            self._write_qubit(loc, random.random() < 0.5)
        elif isinstance(loc, quantumpseudocode.Qureg):
            for q in loc:
                self._write_qubit(q, random.random() < 0.5)
        elif isinstance(loc, quantumpseudocode.Quint):
            for q in loc:
                self._write_qubit(q, random.random() < 0.5)
        elif isinstance(loc, quantumpseudocode.ControlledRValue):
            if self.resolve_location(loc.controls):
                self.randomize_location(loc.rvalue)
        else:
            raise NotImplementedError(
                "Unrecognized type for randomize_location {!r}".format(loc))

    def overwrite_location(self, loc: Union[quantumpseudocode.Quint, quantumpseudocode.Qubit, quantumpseudocode.Qureg, quantumpseudocode.ArgsAndKwargs], val: Union['quantumpseudocode.Mutable', Any]):
        if isinstance(loc, quantumpseudocode.Qubit):
            self._write_qubit(loc, val.val)
        elif isinstance(loc, quantumpseudocode.Qureg):
            for q, v in zip(loc, val.val):
                self._write_qubit(q, v)
        elif isinstance(loc, quantumpseudocode.Quint):
            self._write_quint(loc, val.val)
        elif isinstance(loc, quantumpseudocode.ArgsAndKwargs):
            loc.zip_map(val, self.overwrite_location)
        elif isinstance(loc, (quantumpseudocode.IntRValue, quantumpseudocode.BoolRValue)):
            assert self.resolve_location(loc) == loc.val
        elif isinstance(loc, (bool, int)):
            assert self.resolve_location(loc) == val
        elif isinstance(loc, quantumpseudocode.ControlledRValue):
            if self.resolve_location(loc.controls):
                self.overwrite_location(loc.rvalue, val)
        elif isinstance(loc, quantumpseudocode.LookupRValue):
            assert self.resolve_location(loc) == val
        elif isinstance(loc, quantumpseudocode.QuintRValue):
            assert self.resolve_location(loc) == val
        elif isinstance(loc, quantumpseudocode.Operation):
            self.overwrite_location(loc.state_locations(), val.args)
        else:
            raise NotImplementedError(
                "Unrecognized type for overwrite_location {!r}".format(loc))

    def modify(self, operation: 'quantumpseudocode.Operation'):
        op, cnt = separate_controls(operation)

        if isinstance(op, quantumpseudocode.AllocQuregOperation):
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
            if isinstance(op, quantumpseudocode.InverseOperation):
                if isinstance(op.sub, quantumpseudocode.SignatureOperation):
                    if op.sub.gate in [quantumpseudocode.PlusEqualGate,
                                       quantumpseudocode.IfLessThanThenGate]:
                        emulate = True
            elif isinstance(op, quantumpseudocode.SignatureOperation):
                if op.gate in [quantumpseudocode.PlusEqualGate,
                               quantumpseudocode.IfLessThanThenGate]:
                    emulate = True
            if emulate:
                self.apply_op_via_emulation(operation)
                return []

        if isinstance(op, quantumpseudocode.ReleaseQuregOperation):
            assert len(cnt) == 0
            for q in op.qureg:
                if self.enforce_release_at_zero and not op.dirty:
                    assert self._read_qubit(q) == 0, 'Failed to uncompute {}'.format(q)
                del self._bool_state[q]
            return []

        if isinstance(op, quantumpseudocode.MeasureOperation):
            assert len(cnt) == 0
            assert op.raw_results is None
            results = [self._read_qubit(q) for q in op.targets]
            if op.reset:
                for q in op.targets:
                    self._write_qubit(q, False)
            op.raw_results = tuple(results)
            return []

        if isinstance(op, quantumpseudocode.MeasureXForPhaseKickOperation):
            r = self.phase_fixup_bias
            if r is None:
                r = random.random() < 0.5
            op.result = r
            self._write_qubit(op.target, 0)
            return []

        if isinstance(op, quantumpseudocode.SignatureOperation):
            if op.gate == quantumpseudocode.OP_TOGGLE:
                targets = op.args.pass_into(_toggle_targets)
                assert set(targets).isdisjoint(cnt)
                if all(self._read_qubit(q) for q in cnt):
                    for t in targets:
                        self._write_qubit(t, not self._read_qubit(t))
                return []

        if op == quantumpseudocode.OP_PHASE_FLIP:
            # skip
            return []

        return [operation]
