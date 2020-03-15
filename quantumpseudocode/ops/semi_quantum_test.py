from typing import Union

import cirq
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

    with qp.LogCirqCircuit(measure_bias=1) as circuit:
        v = f(2)
        assert isinstance(v, qp.Quint)
    cirq.testing.assert_has_diagram(circuit, """
_f_x[0]: -------alloc-------Mxc--------cxM---release---
                |           |          |     |
_f_x[1]: -------alloc---X---Mxc--------cxM---release---

global phase:                     pi
    """, use_unicode_characters=False)

    with qp.LogCirqCircuit(measure_bias=1) as circuit:
        v = f(True)
        assert isinstance(v, qp.Quint)
    cirq.testing.assert_has_diagram(circuit, """
_f_x_1: --------alloc---X---Mxc--------cxM---release---

global phase:                     pi
        """, use_unicode_characters=False)

    with qp.LogCirqCircuit(measure_bias=1) as circuit:
        rval = qp.LookupTable([1, 2, 3])[q]
        v = f(rval)
        assert isinstance(v, qp.Quint)
    cirq.testing.assert_has_diagram(circuit, """
_f_x[0]: ------------alloc-----------------------------------X-----------------------------------------X-----------------------------Mxc---X---@---X-------------------Z-------------------------------------X---------@---------Mxc--------cxM---cxM---release---
                     |                                       |                                         |                             |         |   |                   |                                     |         |                          |     |
_f_x[1]: ------------alloc-----------------------------------|-------X---------------------------------X-----------------------------Mxc-------X---@-------------------|---Z---------------------------------@---Mxc---|---cxM--------------------cxM---release---
                                                             |       |                                 |                                       |                       |   |                                           |
_lookup_prefix: -------------alloc---X---X-----------@---@---|---@---|---------@-------------------X---@---Mxc-------cxM---release-------------|-------alloc---X---X---@---@---X---Mxc-------cxM---release-------------|------------------------------------------
                                     |               |   |   |   |   |         |                                                               |               |                                                       |
_lookup_prefix_1: -------------------|-------alloc---X---X---@---X---@---Mxc---|---cxM---release-----------------------------------------------|---------------|-------------------------------------------------------|------------------------------------------
                                     |               |                         |                                                               |               |                                                       |
a[0]: -------------------------------|---------------@-------------------------Z---------------------------------------------------------------@---------------|-------------------------------------------------------Z------------------------------------------
                                     |                                                                                                                         |
a[1]: -------------------------------@---------------------------------------------------------------------------Z---------------------------------------------@-------------------------Z------------------------------------------------------------------------

global phase:                                                                                                                                                                                                                          pi
            """, use_unicode_characters=False)

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
    with qp.capture(measure_bias=0.5):
        q = f(False)
    assert q.name.key == '_test_x'


def test_qubit_borrowed():
    @qp.semi_quantum
    def f(x: qp.Qubit.Borrowed):
        return x

    q = qp.Qubit('a', 10)
    assert f(q) is q

    with qp.LogCirqCircuit(measure_bias=1) as circuit:
        v = f(True)
        assert isinstance(v, qp.Qubit)
        del v
    cirq.testing.assert_has_diagram(circuit, """
_f_x: ----------alloc---X---Mxc--------cxM---release---

global phase:                     pi
                """, use_unicode_characters=False)

    with qp.LogCirqCircuit(measure_bias=1) as circuit:
        v = f(0)
        assert isinstance(v, qp.Qubit)
        del v
    cirq.testing.assert_has_diagram(circuit, """
_f_x: ---alloc---Mxc---cxM---release---
                """, use_unicode_characters=False)

    with qp.LogCirqCircuit(measure_bias=1) as circuit:
        rval = qp.Quint(qp.NamedQureg('a', 3)) > qp.Quint(qp.NamedQureg('b', 3))
        v = f(rval)
        assert isinstance(v, qp.Qubit)
        del v
    cirq.testing.assert_has_diagram(circuit, """
_do_if_less_than_or_equal: -----------alloc---@---X---@-------------------------------------------------------@---X---@---Mxc---cxM---release---------alloc---@---X---@-------------------------------------------------------@---X---@---Mxc---cxM---release-------------------
                                              |   |   |                                                       |   |   |                                       |   |   |                                                       |   |   |
_f_x: ------------------------alloc-----------|---|---|---------------------------X---------------------------|---|---|-------------------------Mxc-----------|---|---|-------------------------------------------------------|---|---|-------------------------cxM---release---
                                              |   |   |                           |                           |   |   |                                       |   |   |                                                       |   |   |
a_1[0]: --------------------------------------|---@---X---@---X---@---------------|---------------@---X---@---X---@---|---------------------------------------|---@---X---@---X---@-------------------------------@---X---@---X---@---|-----------------------------------------
                                              |       |   |   |   |               |               |   |   |   |       |                                       |       |   |   |   |                               |   |   |   |       |
a_1[1]: --------------------------------------|-------|---|---@---X---@---X---@---|---@---X---@---X---@---|---|-------|---------------------------------------|-------|---|---@---X---@---X---@-------@---X---@---X---@---|---|-------|-----------------------------------------
                                              |       |   |       |   |   |   |   |   |   |   |   |       |   |       |                                       |       |   |       |   |   |   |       |   |   |   |       |   |       |
a_1[2]: --------------------------------------|-------|---|-------|---|---@---X---@---X---@---|---|-------|---|-------|---------------------------------------|-------|---|-------|---|---@---X---Z---X---@---|---|-------|---|-------|-----------------------------------------
                                              |       |   |       |   |       |       |       |   |       |   |       |                                       |       |   |       |   |       |       |       |   |       |   |       |
b[0]: ----------------------------------------X-------@---|-------|---|-------|-------|-------|---|-------|---@-------X---------------------------------------X-------@---|-------|---|-------|-------|-------|---|-------|---@-------X-----------------------------------------
                                                          |       |   |       |       |       |   |       |                                                               |       |   |       |       |       |   |       |
b[1]: ----------------------------------------------------X-------@---|-------|-------|-------|---@-------X---------------------------------------------------------------X-------@---|-------|-------|-------|---@-------X-----------------------------------------------------
                                                                      |       |       |       |                                                                                       |       |       |       |
b[2]: ----------------------------------------------------------------X-------@-------@-------X---------------------------------------------------------------------------------------X-------@-------@-------X-----------------------------------------------------------------
        """, use_unicode_characters=False)

    with pytest.raises(TypeError, match='quantum boolean expression'):
        _ = f('test')


def test_qubit_control():
    @qp.semi_quantum
    def f(x: qp.Qubit.Control):
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
    with qp.LogCirqCircuit(measure_bias=1) as circuit:
        v = f(q & q2)
        assert isinstance(v, qp.QubitIntersection)
        del v
    cirq.testing.assert_has_diagram(circuit, """
_f_x: ----alloc---X---Mxc-------cxM---release---
                  |
a[10]: -----------@---------@-------------------
                  |         |
b[8]: ------------@---------Z-------------------
        """, use_unicode_characters=False)

    # Arbitrary expression
    with qp.LogCirqCircuit(measure_bias=1) as circuit:
        rval = qp.Quint(qp.NamedQureg('a', 2)) > qp.Quint(qp.NamedQureg('b', 2))
        v = f(rval)
        assert isinstance(v, qp.QubitIntersection)
        q = v.qubits[0]
        assert q.name.key == '_f_x'
        del q
        del v
    cirq.testing.assert_has_diagram(circuit, """
_do_if_less_than_or_equal: -----------alloc---@---X---@-------------------------------@---X---@---Mxc---cxM---release---------alloc---@---X---@-------------------------------@---X---@---Mxc---cxM---release-------------------
                                              |   |   |                               |   |   |                                       |   |   |                               |   |   |
_f_x: ------------------------alloc-----------|---|---|---------------X---------------|---|---|-------------------------Mxc-----------|---|---|-------------------------------|---|---|-------------------------cxM---release---
                                              |   |   |               |               |   |   |                                       |   |   |                               |   |   |
a_1[0]: --------------------------------------|---@---X---@---X---@---|---@---X---@---X---@---|---------------------------------------|---@---X---@---X---@-------@---X---@---X---@---|-----------------------------------------
                                              |       |   |   |   |   |   |   |   |   |       |                                       |       |   |   |   |       |   |   |   |       |
a_1[1]: --------------------------------------|-------|---|---@---X---@---X---@---|---|-------|---------------------------------------|-------|---|---@---X---Z---X---@---|---|-------|-----------------------------------------
                                              |       |   |       |       |       |   |       |                                       |       |   |       |       |       |   |       |
b_1[0]: --------------------------------------X-------@---|-------|-------|-------|---@-------X---------------------------------------X-------@---|-------|-------|-------|---@-------X-----------------------------------------
                                                          |       |       |       |                                                               |       |       |       |
b_1[1]: --------------------------------------------------X-------@-------@-------X---------------------------------------------------------------X-------@-------@-------X-----------------------------------------------------
        """, use_unicode_characters=False)

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
    with qp.LogCirqCircuit(measure_bias=1) as circuit:
        add(a, 10, control=True)
    assert len(circuit) >= 5


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
        qp.phase_flip()

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
