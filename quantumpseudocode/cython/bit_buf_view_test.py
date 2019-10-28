import numpy as np
import pytest

import quantumpseudocode as qp


def test_memory():
    for _ in range(10):
        m = qp.create_buffer(64*4)
        s = m[0:8]
        np.testing.assert_equal(s.bits(), [0, 0, 0, 0, 0, 0, 0, 0])
        np.testing.assert_equal(s.uint64s(), [0])
        s.write_bits([1, 1, 0, 0, 1, 0, 1, 0])
        np.testing.assert_equal(s.bits(), [1, 1, 0, 0, 1, 0, 1, 0])
        np.testing.assert_equal(s.uint64s(), [0b01010011])


def test_memory_concat():
    for _ in range(10):
        m = qp.create_buffer(64*4)
        s = m[4:8].concat(m[10:14])
        np.testing.assert_equal(s.bits(), [0, 0, 0, 0, 0, 0, 0, 0])
        np.testing.assert_equal(s.uint64s(), [0])
        s.write_bits([1, 1, 0, 0, 1, 0, 1, 0])
        np.testing.assert_equal(s.bits(), [1, 1, 0, 0, 1, 0, 1, 0])
        np.testing.assert_equal(s.uint64s(), [0b01010011])


def test_xor():
    for _ in range(10):
        m = qp.create_buffer(64*4)
        m2 = qp.create_buffer(64*4)
        s1 = m[4:10].concat(m[30:54])
        s2 = m2[:len(s1)]
        s2 ^= s1
        s1.write_bits([1] * len(s1))
        s2 ^= s1
        assert list(s1.bits()) == [1] * len(s1)
        assert list(s2.bits()) == [1] * len(s1) + [0] * (len(s2) - len(s1))


def test_bit_view_slices():
    back = qp.create_buffer(500)
    v = back[:48].concat(back[100:200]).concat(back[300:400])
    v[:] = -1
    assert int(v) == 2**248 - 1
    assert list(back.uint64s()) == [
        0x0000ffffffffffff,
        0xfffffff000000000,
        0xffffffffffffffff,
        0x00000000000000ff,
        0xfffff00000000000,
        0xffffffffffffffff,
        0x000000000000ffff,
        0x0000000000000000,
    ]
