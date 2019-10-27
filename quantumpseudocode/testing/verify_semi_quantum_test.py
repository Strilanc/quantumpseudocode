import random
from typing import Any, Callable, Iterable, Sequence, get_type_hints, Union, Dict, TypeVar, Generic, List

import pytest

import quantumpseudocode as qp


TSample = TypeVar('TSample')


def test_correct():
    def classical_cnot_pairs(zs: int, xs: qp.IntBuf):
        parity = 0
        while zs:
            zs &= zs - 1
            parity += 1
        if parity & 1:
            xs ^= -1

    @qp.semi_quantum(classical=classical_cnot_pairs)
    def quantum_cnot_pairs(zs: qp.Quint.Borrowed, xs: qp.Quint):
        for z in zs:
            for x in xs:
                x ^= z

    qp.testing.assert_semi_quantum_func_is_consistent(
        quantum_cnot_pairs,
        fixed=[
            {'xs': qp.IntBuf.raw(length=0, val=0), 'zs': 0}
        ],
        fuzz_count=100,
        fuzz_space={
            'xs': lambda: qp.IntBuf.random(range(0, 6)),
            'zs': lambda: random.randint(0, 63)
        })


def test_bad_uncompute():
    def cf(c: bool, t: qp.IntBuf):
        t ^= c
        c ^= int(t)

    @qp.semi_quantum(classical=cf)
    def qf(c: qp.Qubit.Borrowed, t: qp.Qubit):
        t ^= c
        c ^= t

    with pytest.raises(AssertionError, match='Failed to uncompute'):
        qp.testing.assert_semi_quantum_func_is_consistent(
            qf,
            fuzz_space={'t': lambda: qp.IntBuf.random(1), 'c': [False, True]},
            fuzz_count=100)


def test_bad_control():
    def classical_flip(t: qp.IntBuf):
        t ^= 1

    @qp.semi_quantum(classical=classical_flip)
    def quantum_cnot_pairs(control: qp.Qubit.Control, t: qp.Qubit):
        t ^= 1

    # Catch issue when control is allowed to be False.
    with pytest.raises(AssertionError, match='disagreed'):
        qp.testing.assert_semi_quantum_func_is_consistent(
            quantum_cnot_pairs,
            fixed=[
                {'t': qp.IntBuf.raw(length=1, val=0), 'control': False}
            ])
    with pytest.raises(AssertionError, match='disagreed'):
        qp.testing.assert_semi_quantum_func_is_consistent(
            quantum_cnot_pairs,
            fixed=[
                {'t': qp.IntBuf.raw(length=1, val=0)}
            ])
    with pytest.raises(AssertionError, match='disagreed'):
        qp.testing.assert_semi_quantum_func_is_consistent(
            quantum_cnot_pairs,
            fuzz_count=100,
            fuzz_space={
                't': qp.IntBuf.raw(length=1, val=0)
            })
    with pytest.raises(AssertionError, match='disagreed'):
        qp.testing.assert_semi_quantum_func_is_consistent(
            quantum_cnot_pairs,
            fuzz_count=100,
            fuzz_space={
                't': qp.IntBuf.raw(length=1, val=0),
                'control': [False, True]
            })
    with pytest.raises(AssertionError, match='disagreed'):
        qp.testing.assert_semi_quantum_func_is_consistent(
            quantum_cnot_pairs,
            fuzz_count=100,
            fuzz_space={
                't': qp.IntBuf.raw(length=1, val=0),
                'control': lambda: random.randint(0, 1)
            })
    with pytest.raises(AssertionError, match='disagreed'):
        qp.testing.assert_semi_quantum_func_is_consistent(
            quantum_cnot_pairs,
            fuzz_count=100,
            fuzz_space={
                't': qp.IntBuf.raw(length=1, val=0),
                'control': [False]
            })
    with pytest.raises(AssertionError, match='disagreed'):
        qp.testing.assert_semi_quantum_func_is_consistent(
            quantum_cnot_pairs,
            fuzz_count=100,
            fuzz_space={
                't': qp.IntBuf.raw(length=1, val=0),
                'control': False
            })

    # Fail to catch when control is forced to be true.
    qp.testing.assert_semi_quantum_func_is_consistent(
        quantum_cnot_pairs,
        fixed=[
            {'t': qp.IntBuf.raw(length=1, val=0), 'control': True}
        ])
    qp.testing.assert_semi_quantum_func_is_consistent(
        quantum_cnot_pairs,
        fuzz_count=20,
        fuzz_space={
            't': qp.IntBuf.raw(length=1, val=0),
            'control': [True]
        })
    qp.testing.assert_semi_quantum_func_is_consistent(
        quantum_cnot_pairs,
        fuzz_count=20,
        fuzz_space={
            't': qp.IntBuf.raw(length=1, val=0),
            'control': True
        })
    qp.testing.assert_semi_quantum_func_is_consistent(
        quantum_cnot_pairs,
        fuzz_count=20,
        fuzz_space={
            't': qp.IntBuf.raw(length=1, val=0),
            'control': lambda: 1
        })


def test_phase_match():
    def cf(sim_state: qp.ClassicalSimState):
        sim_state.phase_degrees += 180

    @qp.semi_quantum(classical=cf)
    def qf():
        qp.do_atom(qp.OP_PHASE_FLIP)

    qp.testing.assert_semi_quantum_func_is_consistent(
        qf,
        fixed=[{}])


def test_phase_mismatch():
    def cf(sim_state: qp.ClassicalSimState):
        sim_state.phase_degrees += 90

    @qp.semi_quantum(classical=cf)
    def qf():
        qp.do_atom(qp.OP_PHASE_FLIP)

    with pytest.raises(AssertionError, match='disagreed'):
        qp.testing.assert_semi_quantum_func_is_consistent(
            qf,
            fixed=[{}])
