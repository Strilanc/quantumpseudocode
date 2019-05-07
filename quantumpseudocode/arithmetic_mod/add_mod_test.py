import random

import quantumpseudocode as qp


def assert_adds_correctly(modulus: int, t: int, v: int):
    v %= modulus

    assert_control_adds_correctly(modulus, t, v, False)
    assert_control_adds_correctly(modulus, t, v, True)

    def f(a: qp.QuintMod, b: int):
        a += b
    r = qp.testing.sim_call(f,
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
    r = qp.testing.sim_call(f,
                            qp.testing.ModInt(val=t, modulus=modulus),
                            v,
                            control)
    assert r == qp.ArgsAndKwargs([
        (t + v) % modulus if control else t,
        v,
        control
    ], {})


def test_function():
    for modulus in range(1, 6):
        for v in range(modulus):
            for t in range(modulus):
                assert_adds_correctly(modulus, t, v)

    for _ in range(10):
        modulus = random.randint(0, 1 << 100)
        t = random.randint(0, modulus - 1)
        v = random.randint(0, modulus - 1)
        assert_adds_correctly(modulus, t, v)
