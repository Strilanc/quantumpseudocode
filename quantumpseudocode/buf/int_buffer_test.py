import quantumpseudocode as qp


def test_int_buffer():
    e = qp.IntBuf.zero(10)
    assert not bool(e)
    assert int(e) == 0
    assert e[0] == 0
    assert e[1] == 0

    e += 2
    assert int(e) == 2
    assert bool(e)
    assert e[0] == 0
    assert e[1] == 1

    assert str(e) == '0100000000'
    assert str(e[1:5]) == '1000'

    e -= 43
    assert int(e) == 983
    e[2:] += 1
    assert int(e) == 987


def test_ref_iadd():
    e = qp.IntBuf.zero(10)
    e += 33
    assert int(e) == 33
    f = e[2:]
    f -= 1
    assert int(e) == 29
    f += 1
    assert int(e) == 33


def test_concat():
    a = qp.RawIntBuffer(0, 5)
    b = qp.RawIntBuffer(0, 5)
    c = qp.RawConcatBuffer(a, b)
    e = qp.IntBuf(c)

    e += 33
    assert int(e) == 33
    f = e[2:]
    f -= 1
    assert int(e) == 29
    f += 1
    assert int(e) == 33

    e[:] = 0b1001100101
    assert e[:5] == 0b00101
    assert e[5:] == 0b10011
    assert e[3:8] == 0b01100

    e[:] = 0
    e[:5] = 0b11111
    assert int(e) == 0b0000011111
    e[:] = 0
    e[5:] = 0b11111
    assert int(e) == 0b1111100000
    e[:] = 0
    e[3:8] = 0b11111
    assert int(e) == 0b0011111000


def test_window_flatten():
    a = qp.RawIntBuffer(0b101101, 6)
    b = qp.RawWindowBuffer(a, 1, 5)
    c = qp.RawWindowBuffer(b, 1, 3)
    assert repr(c) == 'RawWindowBuffer(RawIntBuffer(0b101101, 6), 2, 4)'
