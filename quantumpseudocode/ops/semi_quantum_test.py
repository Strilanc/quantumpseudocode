from typing import Union

import pytest

import quantumpseudocode as qp


def test_empty():
    @qp.semi_quantum
    def f():
        return 2
    assert f() == 2


def test_quint():
    @qp.semi_quantum
    def f(x: qp.Quint):
        return x
    q = qp.Quint(qp.NamedQureg('a', 10))
    assert f(q) is q
    with pytest.raises(TypeError, match='Expected a qp.Quint'):
        _ = f(2)
    with pytest.raises(TypeError, match='Expected a qp.Quint'):
        _ = f('a')
    with pytest.raises(TypeError, match='Expected a qp.Quint'):
        _ = f(qp.Qubit('a'))
    with pytest.raises(TypeError, match='Expected a qp.Quint'):
        _ = f(qp.IntRValue(2))


def test_quint_borrowed():
    @qp.semi_quantum
    def f(x: qp.Quint.Borrowed):
        return x

    q = qp.Quint(qp.NamedQureg('a', 10))
    assert f(q) is q

    with qp.capture() as out:
        v = f(2)
        assert isinstance(v, qp.Quint)
        assert out == [
            qp.AllocQuregOperation(v.qureg),
            qp.Toggle(v[1]),
            qp.StartMeasurementBasedUncomputation(v),
            qp.GlobalPhaseOp(180),
            qp.EndMeasurementBasedComputationOp(0),
            qp.ReleaseQuregOperation(v.qureg),
        ]
    assert len(out) == 6

    with qp.capture() as out:
        v = f(True)
        assert isinstance(v, qp.Quint)
        assert out == [
            qp.AllocQuregOperation(v.qureg),
            qp.Toggle(v[0]),
            qp.StartMeasurementBasedUncomputation(v),
            qp.GlobalPhaseOp(180),
            qp.EndMeasurementBasedComputationOp(0),
            qp.ReleaseQuregOperation(v.qureg),
        ]
    assert len(out) == 6

    with qp.capture() as out:
        rval = qp.LookupTable([1, 2, 3])[q]
        v = f(rval)
        assert isinstance(v, qp.Quint)
        n = len(out)
        assert n > 6
    assert len(out) == n

    with pytest.raises(TypeError, match='quantum integer expression'):
        _ = f('test')


def test_qubit():
    @qp.semi_quantum
    def f(x: qp.Qubit):
        return x
    q = qp.Qubit('a', 10)
    assert f(q) is q
    with pytest.raises(TypeError, match='Expected a qp.Qubit'):
        _ = f(2)
    with pytest.raises(TypeError, match='Expected a qp.Qubit'):
        _ = f('a')
    with pytest.raises(TypeError, match='Expected a qp.Qubit'):
        _ = f(qp.Quint(qp.NamedQureg('a', 10)))
    with pytest.raises(TypeError, match='Expected a qp.Qubit'):
        _ = f(qp.BoolRValue(True))


def test_qubit_parens():
    @qp.semi_quantum()
    def f(x: qp.Qubit):
        return x
    q = qp.Qubit('a', 10)
    assert f(q) is q


def test_prefix():
    @qp.semi_quantum(alloc_prefix='_test_')
    def f(x: qp.Qubit.Borrowed):
        return x
    with qp.capture():
        q = f(False)
    assert q.name.key == '_test_x'


def test_qubit_borrowed():
    @qp.semi_quantum
    def f(x: qp.Qubit.Borrowed):
        return x

    q = qp.Qubit('a', 10)
    assert f(q) is q

    with qp.capture() as out:
        v = f(True)
        assert isinstance(v, qp.Qubit)
        assert out == [
            qp.AllocQuregOperation(qp.RawQureg([v])),
            qp.Toggle(v),
            qp.StartMeasurementBasedUncomputation(v),
            qp.GlobalPhaseOp(180),
            qp.EndMeasurementBasedComputationOp(0),
            qp.ReleaseQuregOperation(qp.RawQureg([v])),
        ]
    assert len(out) == 6

    with qp.capture() as out:
        v = f(0)
        assert isinstance(v, qp.Qubit)
        assert out == [
            qp.AllocQuregOperation(qp.RawQureg([v])),
            qp.StartMeasurementBasedUncomputation(v),
            qp.EndMeasurementBasedComputationOp(0),
            qp.ReleaseQuregOperation(qp.RawQureg([v])),
        ]
    assert len(out) == 4

    with qp.capture() as out:
        rval = qp.Quint(qp.NamedQureg('a', 10)) > qp.Quint(qp.NamedQureg('b', 10))
        v = f(rval)
        assert isinstance(v, qp.Qubit)
        n = len(out)
        assert n > 6
    assert len(out) == n

    with pytest.raises(TypeError, match='quantum boolean expression'):
        _ = f('test')


def test_qubit_control():
    @qp.semi_quantum
    def f(x: qp.Qubit.Control) -> qp.QubitIntersection:
        assert isinstance(x, qp.QubitIntersection)
        return x

    q = qp.Qubit('a', 10)
    q2 = qp.Qubit('b', 8)

    # Note: The lack of capture context means we are implicitly asserting the following invokations perform no
    # quantum operations such as allocating a qubit.

    # Definitely false.
    assert f(False) == qp.QubitIntersection.NEVER
    assert f(qp.QubitIntersection.NEVER) == qp.QubitIntersection.NEVER

    # Definitely true.
    assert f(qp.QubitIntersection.ALWAYS) == qp.QubitIntersection.ALWAYS
    assert f(None) == qp.QubitIntersection.ALWAYS
    assert f(True) == qp.QubitIntersection.ALWAYS

    # Single qubit.
    assert f(q) == qp.QubitIntersection((q,))
    assert f(qp.QubitIntersection((q,))) == qp.QubitIntersection((q,))

    # Multi qubit intersection.
    with qp.capture() as out:
        v = f(q & q2)
        assert isinstance(v, qp.QubitIntersection)
        assert out == [
            qp.AllocQuregOperation(qp.RawQureg(v.qubits)),
            qp.Toggle(v.qubits).controlled_by(q & q2),
            qp.StartMeasurementBasedUncomputation(v.qubits),
            qp.GlobalPhaseOp(180).controlled_by(q & q2),
            qp.EndMeasurementBasedComputationOp(0),
            qp.ReleaseQuregOperation(qp.RawQureg(v.qubits)),
        ]
    assert len(out) == 6

    # Arbitrary expression
    with qp.capture() as out:
        rval = qp.Quint(qp.NamedQureg('a', 10)) > qp.Quint(qp.NamedQureg('b', 10))
        v = f(rval)
        assert isinstance(v, qp.QubitIntersection)
        q = v.qubits[0]
        assert q.name.key == '_f_x'
        n = len(out)
        assert n > 6
    assert len(out) == n

    with pytest.raises(TypeError, match='quantum control expression'):
        _ = f('test')
    with pytest.raises(TypeError, match='quantum control expression'):
        _ = f(qp.Quint(qp.NamedQureg('a', 10)))
    with pytest.raises(TypeError, match='quantum control expression'):
        _ = f(qp.Quint(qp.NamedQureg('a', 10)))


def test_multiple():
    @qp.semi_quantum
    def add(target: qp.Quint, offset: qp.Quint.Borrowed, *, control: qp.Qubit.Control = False):
        assert isinstance(target, qp.Quint)
        assert isinstance(offset, qp.Quint)
        assert isinstance(control, qp.QubitIntersection)
        target += offset & qp.controlled_by(control)

    a = qp.Quint(qp.NamedQureg('a', 5))
    with qp.capture() as out:
        add(a, 10, control=True)
    assert len(out) >= 5


def test_classical():
    def g(x: qp.IntBuf, y: int):
        assert isinstance(x, qp.IntBuf)
        assert isinstance(y, int)
        x ^= y

    @qp.semi_quantum(classical=g)
    def f(x: qp.Quint, y: qp.Quint.Borrowed):
        x ^= y

    assert f.classical is g

    with qp.Sim() as sim_state:
        q = qp.qalloc_int(bits=5)
        assert sim_state.resolve_location(q, False) == 0
        f.sim(sim_state, q, 3)
        assert sim_state.resolve_location(q, False) == 3
        f.sim(sim_state, q, 5)
        assert sim_state.resolve_location(q, False) == 6
        f.sim(sim_state, q, 6)
        qp.qfree(q)


def test_optional():
    def cf(x: qp.IntBuf, y: bool = True):
        x ^= int(y)

    @qp.semi_quantum(classical=cf)
    def qf(x: qp.Qubit, y: qp.Qubit.Borrowed = True):
        x ^= y

    b = qp.IntBuf.raw(val=0, length=1)
    qf.classical(b)
    assert int(b) == 1
    qf.classical(b)
    assert int(b) == 0
    qf.classical(b, True)
    assert int(b) == 1
    qf.classical(b, False)
    assert int(b) == 1

    with qp.Sim() as sim_state:
        q = qp.qalloc()
        assert not sim_state.resolve_location(q, False)
        qf(q)
        assert sim_state.resolve_location(q, False)
        qf(q)
        assert not sim_state.resolve_location(q, False)
        qf(q, True)
        assert sim_state.resolve_location(q, False)
        qf(q, False)
        assert sim_state.resolve_location(q, False)
        assert qp.measure(q, reset=True)
        qp.qfree(q)


def test_with_sim_state():
    def cf(sim_state: qp.ClassicalSimState):
        sim_state.phase_degrees += 180

    @qp.semi_quantum(classical=cf)
    def qf():
        qp.emit(qp.OP_PHASE_FLIP)

    with qp.Sim() as sim_state:
        assert sim_state.phase_degrees == 0
        qf()
        assert sim_state.phase_degrees == 180
        qf.sim(sim_state)
        assert sim_state.phase_degrees == 0


def test_inconsistent_optional():
    with pytest.raises(TypeError, match='Inconsistent default'):
        def cf(x: qp.IntBuf, y: bool):
            pass

        @qp.semi_quantum(classical=cf)
        def qf(x: qp.Qubit, y: qp.Qubit.Borrowed = True):
            pass

    with pytest.raises(TypeError, match='Inconsistent default'):
        def cf(x: qp.IntBuf, y: bool = False):
            pass

        @qp.semi_quantum(classical=cf)
        def qf(x: qp.Qubit, y: qp.Qubit.Borrowed = True):
            pass

    with pytest.raises(TypeError, match='Inconsistent default'):
        def cf(x: qp.IntBuf, y: bool = True):
            pass

        @qp.semi_quantum(classical=cf)
        def qf(x: qp.Qubit, y: qp.Qubit.Borrowed):
            pass
