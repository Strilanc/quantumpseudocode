import quantumpseudocode as qp


def test_sim():
    v1 = 15
    v2 = 235
    offset = 4
    bits = 10
    with qp.Sim():
        with qp.hold(val=v1, name='a') as a:
            with qp.qalloc_int(bits=bits, name='out') as out:
                out += a * v2
                out += offset
                result = qp.measure(out, reset=True)
    assert result == (v1*v2 + offset) & ((1 << bits) - 1)


def test_count():
    v1 = 15
    v2 = 235
    offset = 4
    bits = 100
    with qp.Sim():
        with qp.CountNots() as counts:
            with qp.hold(val=v1, name='a') as a:
                with qp.qalloc_int(bits=bits, name='out') as out:
                    out += a * v2
                    out += offset
                    _ = qp.measure(out, reset=True)
    assert len(counts.keys()) == 3
    assert counts[0] > 0
    assert counts[1] > 0
    assert 0 < counts[2] <= 1000
