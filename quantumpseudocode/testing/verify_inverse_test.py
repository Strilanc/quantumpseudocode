import functools
import inspect
import random
from typing import Any, Callable, Iterable, Sequence, get_type_hints, Union, Dict, TypeVar, Generic, List

import pytest

import quantumpseudocode as qp


def test_verify_inverse():
    def xor1(a: qp.Quint, b: qp.Quint, c: qp.Quint):
        a ^= b
        b ^= c

    def xor2(a: qp.Quint, b: qp.Quint, c: qp.Quint):
        b ^= c
        a ^= b

    def xor2_bad(a: qp.Quint, b: qp.Quint, c: qp.Quint):
        b ^= c

    qp.testing.assert_inverse_is_consistent(
        xor1,
        xor2,
        fuzz_space={
            'a': qp.IntBuf.random(5),
            'b': qp.IntBuf.random(5),
            'c': qp.IntBuf.random(5)
        },
        fuzz_count=10)

    with pytest.raises(AssertionError, match='Inconsistent inverse'):
        qp.testing.assert_inverse_is_consistent(
            xor1,
            xor2_bad,
            fuzz_space={
                'a': qp.IntBuf.random(5),
                'b': qp.IntBuf.random(5),
                'c': qp.IntBuf.random(5)
            },
            fuzz_count=100)


def test_verify_self_inverse():

    def xor_sym(a: qp.Quint, b: qp.Quint, c: qp.Quint):
        a ^= b
        b ^= a
        a ^= b
    qp.testing.assert_self_inverse_is_consistent(xor_sym,
                                                 fuzz_space={
                                                     'a': qp.IntBuf.random(5),
                                                     'b': qp.IntBuf.random(5),
                                                     'c': qp.IntBuf.random(5)
                                                 },
                                                 fuzz_count=10)

    def xor_known(a: qp.Quint, b: qp.Quint, c: qp.Quint, forward: bool):
        if forward:
            a ^= b
            b ^= c
        else:
            b ^= c
            a ^= b
    qp.testing.assert_self_inverse_is_consistent(xor_known,
                                                 fuzz_space={
                                                     'a': qp.IntBuf.random(5),
                                                     'b': qp.IntBuf.random(5),
                                                     'c': qp.IntBuf.random(5)
                                                 },
                                                 fuzz_count=10)

    def xor_known2(a: qp.Quint, b: qp.Quint, c: qp.Quint, inverse: bool):
        if inverse:
            a ^= b
            b ^= c
        else:
            b ^= c
            a ^= b
    qp.testing.assert_self_inverse_is_consistent(xor_known2,
                                                 fuzz_space={
                                                     'a': qp.IntBuf.random(5),
                                                     'b': qp.IntBuf.random(5),
                                                     'c': qp.IntBuf.random(5)
                                                 },
                                                 fuzz_count=10)

    def xor_raw(a: qp.Quint, b: qp.Quint, c: qp.Quint):
        a ^= b
        b ^= c
    with pytest.raises(AssertionError, match='Inconsistent inverse'):
        qp.testing.assert_self_inverse_is_consistent(
            xor_raw,
            fuzz_space={
                'a': qp.IntBuf.random(5),
                'b': qp.IntBuf.random(5),
                'c': qp.IntBuf.random(5)
            },
            fuzz_count=100)

    def xor_forward(a: qp.Quint, b: qp.Quint, c: qp.Quint, forward: bool):
        a ^= b
        b ^= c
    with pytest.raises(AssertionError, match='Inconsistent inverse'):
        qp.testing.assert_self_inverse_is_consistent(
            xor_forward,
            fuzz_space={
                'a': qp.IntBuf.random(5),
                'b': qp.IntBuf.random(5),
                'c': qp.IntBuf.random(5)
            },
            fuzz_count=100)

    def xor_inverse(a: qp.Quint, b: qp.Quint, c: qp.Quint, inverse: bool):
        a ^= b
        b ^= c
    with pytest.raises(AssertionError, match='Inconsistent inverse'):
        qp.testing.assert_self_inverse_is_consistent(
            xor_inverse,
            fuzz_space={
                'a': qp.IntBuf.random(5),
                'b': qp.IntBuf.random(5),
                'c': qp.IntBuf.random(5)
            },
            fuzz_count=100)
