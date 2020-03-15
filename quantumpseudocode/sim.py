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
        self._anon_alloc_counter = 0

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

    def do_allocate_qureg(self, args: 'qp.AllocArgs') -> 'qp.Qureg':
        if args.qureg_name is None:
            name = f'_anon_{self._anon_alloc_counter}'
            self._anon_alloc_counter += 1
        else:
            name = args.qureg_name

        result = qp.NamedQureg(name=name, length=args.qureg_length)
        assert result.name not in self._int_state, f"Double allocated {result.name!r}"
        self._int_state[result.name] = qp.IntBuf.raw(
            val=random.randint(0, (1 << args.qureg_length) - 1) if args.x_basis else 0,
            length=args.qureg_length)
        return result

    def did_allocate_qureg(self, args: 'qp.AllocArgs', qureg: 'qp.Qureg'):
        pass

    def do_release_qureg(self, op: 'qp.ReleaseQuregOperation'):
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

    def do_measure_qureg(self, op: 'qp.MeasureOperation'):
        assert op.raw_results is None
        reg = self.quint_buf(qp.Quint(op.targets))
        op.raw_results = tuple(reg[i] for i in range(len(reg)))
        if op.reset:
            reg[:] = 0

    def do_start_measurement_based_uncomputation(self, op: 'qp.StartMeasurementBasedUncomputation'):
        op.raw_results = []
        op.captured_phase_degrees = self.phase_degrees
        reg = self.quint_buf(qp.Quint(op.targets))
        chooser = self.measurement_based_uncomputation_result_chooser()

        # Simulate X basis measurements.
        for i in range(len(op.targets)):
            result = chooser()
            op.raw_results.append(result)
            if result and reg[i]:
                self.phase_degrees += 180

        # Reset target.
        reg[:] = 0

    def do_end_measurement_based_uncomputation(self, op: 'qp.EndMeasurementBasedComputationOp'):
        if self.phase_degrees != op.expected_phase_degrees:
            raise AssertionError('Failed to uncompute. Measurement based uncomputation failed to fix phase flips.')

    def do_phase_flip(self, controls: 'qp.QubitIntersection'):
        if self.resolve_location(controls, allow_mutate=False):
            self.phase_degrees += 180

    def do_toggle_qureg(self, targets: 'qp.Qureg', controls: 'qp.QubitIntersection'):
        assert set(targets).isdisjoint(controls.qubits)
        if controls.bit and all(self._read_qubit(q) for q in controls.qubits):
            for t in targets:
                self._write_qubit(t, not self._read_qubit(t))


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
