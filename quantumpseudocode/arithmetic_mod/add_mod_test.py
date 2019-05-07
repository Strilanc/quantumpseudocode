import pytest
import random

import quantumpseudocode as qp


def assert_adds_correctly(modulus: int, t: int, v: int):
    v %= modulus

    assert_control_adds_correctly(modulus, t, v, False)
    assert_control_adds_correctly(modulus, t, v, True)

    def f(a: qp.QuintMod, b: int):
        a += b
    def g(a: qp.QuintMod, b: qp.Quint):
        a += b

    for e in f, g:
        r = qp.testing.sim_call(e,
                                qp.testing.ModInt(val=t, modulus=modulus),
                                v)
        assert r == qp.ArgsAndKwargs([
            (t + v) % modulus,
            v
        ], {})


def assert_control_adds_correctly(modulus: int, t: int, v: int, control: bool):
    def f(a: qp.QuintMod, b: int, c: qp.Qubit):
        with qp.controlled_by(c):
            a += b
    def g(a: qp.QuintMod, b: qp.Quint, c: qp.Qubit):
        with qp.controlled_by(c):
            a += b
    for e in f, g:
        r = qp.testing.sim_call(e,
                                qp.testing.ModInt(val=t, modulus=modulus),
                                v,
                                control)
        assert r == qp.ArgsAndKwargs([
            (t + v) % modulus if control else t,
            v,
            control
        ], {})


def make_cases():
    for modulus in range(1, 6):
        for v in range(modulus):
            for t in range(modulus):
                yield modulus, t, v
    for _ in range(10):
        modulus = random.randint(0, 1 << 50)
        t = random.randint(0, modulus - 1)
        v = random.randint(0, modulus - 1)
        yield modulus, t, v


@pytest.mark.parametrize('modulus,t,v', make_cases())
def test_function(modulus, t, v):
    assert_adds_correctly(modulus, t, v)
