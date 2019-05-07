import quantumpseudocode as qp


def test_iadd():
    def f(a: qp.QuintMod, b: int):
        a += b

    r = qp.testing.sim_call(
        f,
        a=qp.testing.ModInt(5, 12),
        b=9,
    )
    assert r == qp.ArgsAndKwargs([], {
        'a': 2,
        'b': 9
    })
