import quantumpseudocode as qp


def test_controls_xor():
    def f(c: qp.Qubit, t: qp.Quint):
        t ^= 1 & qp.controlled_by(c)

    r = qp.testing.sim_call(f, True, 2)
    assert r == qp.ArgsAndKwargs([True, 3], {})

    r = qp.testing.sim_call(f, False, 2)
    assert r == qp.ArgsAndKwargs([False, 2], {})
