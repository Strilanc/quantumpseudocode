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
            qp.LetRValueOperation(qp.rval(2), v),
            qp.DelRValueOperation(qp.rval(2), v),
            qp.ReleaseQuregOperation(v.qureg),
        ]
    assert len(out) == 4

    with qp.capture() as out:
        v = f(True)
        assert isinstance(v, qp.Quint)
        assert out == [
            qp.AllocQuregOperation(v.qureg),
            qp.LetRValueOperation(qp.rval(1), v),
            qp.DelRValueOperation(qp.rval(1), v),
            qp.ReleaseQuregOperation(v.qureg),
        ]
    assert len(out) == 4

    with qp.capture() as out:
        rval = qp.LookupTable([1, 2, 3])[q]
        v = f(rval)
        assert isinstance(v, qp.Quint)
        assert out == [
            qp.AllocQuregOperation(v.qureg),
            qp.LetRValueOperation(rval, v),
            qp.DelRValueOperation(rval, v),
            qp.ReleaseQuregOperation(v.qureg),
        ]
    assert len(out) == 4

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
            qp.LetRValueOperation(qp.rval(True), v),
            qp.DelRValueOperation(qp.rval(True), v),
            qp.ReleaseQuregOperation(qp.RawQureg([v])),
        ]
    assert len(out) == 4

    with qp.capture() as out:
        v = f(0)
        assert isinstance(v, qp.Qubit)
        assert out == [
            qp.AllocQuregOperation(qp.RawQureg([v])),
            qp.LetRValueOperation(qp.rval(False), v),
            qp.DelRValueOperation(qp.rval(False), v),
            qp.ReleaseQuregOperation(qp.RawQureg([v])),
        ]
    assert len(out) == 4

    with qp.capture() as out:
        rval = qp.Quint(qp.NamedQureg('a', 10)) > qp.Quint(qp.NamedQureg('b', 10))
        v = f(rval)
        assert isinstance(v, qp.Qubit)
        assert out == [
            qp.AllocQuregOperation(qp.RawQureg([v])),
            qp.LetRValueOperation(rval, v),
            qp.DelRValueOperation(rval, v),
            qp.ReleaseQuregOperation(qp.RawQureg([v])),
        ]
    assert len(out) == 4

    with pytest.raises(TypeError, match='quantum boolean expression'):
        _ = f('test')


def test_qubit_control():
    @qp.semi_quantum
    def f(x: qp.Qubit.Control):
        return x

    q = qp.Qubit('a', 10)
    q2 = qp.Qubit('b', 8)

    # Definitely false.
    with qp.capture() as out:
        assert f(False) == qp.QubitIntersection.NEVER
    assert out == []
    with qp.capture() as out:
        assert f(qp.QubitIntersection.NEVER) == qp.QubitIntersection.NEVER
    assert out == []

    # Definitely true.
    with qp.capture() as out:
        assert f(qp.QubitIntersection.ALWAYS) == qp.QubitIntersection.ALWAYS
    assert out == []
    with qp.capture() as out:
        assert f(None) == qp.QubitIntersection.ALWAYS
    assert out == []
    with qp.capture() as out:
        assert f(True) == qp.QubitIntersection.ALWAYS
    assert out == []

    # Single qubit.
    with qp.capture() as out:
        assert f(q) == qp.QubitIntersection((q,))
    assert out == []
    with qp.capture() as out:
        assert f(qp.QubitIntersection((q,))) == qp.QubitIntersection((q,))
    assert out == []

    # Multi qubit intersection.
    with qp.capture() as out:
        v = f(q & q2)
        assert isinstance(v, qp.QubitIntersection)
        assert out == [
            qp.AllocQuregOperation(qp.RawQureg(v.qubits)),
            qp.LetRValueOperation(q & q2, v.qubits[0]),
            qp.DelRValueOperation(q & q2, v.qubits[0]),
            qp.ReleaseQuregOperation(qp.RawQureg(v.qubits)),
        ]
    assert len(out) == 4

    # Arbitrary expression
    with qp.capture() as out:
        rval = qp.Quint(qp.NamedQureg('a', 10)) > qp.Quint(qp.NamedQureg('b', 10))
        v = f(rval)
        assert isinstance(v, qp.QubitIntersection)
        assert out == [
            qp.AllocQuregOperation(qp.RawQureg(v.qubits)),
            qp.LetRValueOperation(rval, v.qubits[0]),
            qp.DelRValueOperation(rval, v.qubits[0]),
            qp.ReleaseQuregOperation(qp.RawQureg(v.qubits)),
        ]
    assert len(out) == 4

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
