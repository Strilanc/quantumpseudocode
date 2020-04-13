from typing import Union, Any, Optional, Iterable

import cirq

import quantumpseudocode as qp


def test_quint_intersection():
    with qp.Sim():
        a = qp.qalloc_int(bits=5, name="a")
        b = qp.qalloc_int(bits=6, name="b")
        c = qp.qalloc_int(bits=3, name="c")

        d = a & 3
        assert isinstance(d, qp.Quint)
        assert d.qureg == a.qureg[:2]
        d = 3 & a
        assert isinstance(d, qp.Quint)
        assert d.qureg == a.qureg[:2]

        d = a & b
        assert isinstance(d, qp.QuintIntersection)
        assert len(d.quints) == 2
        assert d.mask == -1
        assert str(d) == 'a & b[:5]'

        d = a & b & 5 & c
        assert isinstance(d, qp.QuintIntersection)
        assert len(d.quints) == 3
        assert d.mask == 5
        assert str(d) == 'a[:3] & b[:3] & c & 5'
        d = 5 & (a & b & c)
        assert str(d) == 'a[:3] & b[:3] & c & 5'

        with qp.LogCirqCircuit() as circuit:
            a ^= b & c
        cirq.testing.assert_has_diagram(circuit, r"""
a[0]: ---X-----------
         |
a[1]: ---|---X-------
         |   |
a[2]: ---|---|---X---
         |   |   |
b[0]: ---@---|---|---
         |   |   |
b[1]: ---|---@---|---
         |   |   |
b[2]: ---|---|---@---
         |   |   |
c[0]: ---@---|---|---
             |   |
c[1]: -------@---|---
                 |
c[2]: -----------@---
        """, use_unicode_characters=False)
