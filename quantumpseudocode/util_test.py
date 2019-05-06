import quantumpseudocode


def test_ceil_lg2():
    f = quantumpseudocode.ceil_lg2
    assert f(0) == 0
    assert f(1) == 0
    assert f(2) == 1
    assert f(3) == 2
    assert f(4) == 2
    assert f(5) == 3
    assert f(6) == 3
    assert f(7) == 3
    assert f(8) == 3
    assert f(9) == 4
    assert f((1 << 100) - 1) == 100
    assert f((1 << 100)) == 100
    assert f((1 << 100) + 1) == 101


def test_floor_lg2():
    f = quantumpseudocode.floor_lg2
    assert f(1) == 0
    assert f(2) == 1
    assert f(3) == 1
    assert f(4) == 2
    assert f(5) == 2
    assert f(6) == 2
    assert f(7) == 2
    assert f(8) == 3
    assert f(9) == 3
    assert f((1 << 100) - 1) == 99
    assert f((1 << 100)) == 100
    assert f((1 << 100) + 1) == 100


def test_leading_zero_bit_count():
    f = quantumpseudocode.leading_zero_bit_count
    assert f(-3) == 0
    assert f(-2) == 1
    assert f(-1) == 0
    assert f(0) is None
    assert f(1) == 0
    assert f(2) == 1
    assert f(3) == 0
    assert f(4) == 2
    assert f(5) == 0
    assert f(6) == 1
    assert f(7) == 0
    assert f(8) == 3
    assert f(9) == 0
    assert f((1 << 100) - 2) == 1
    assert f((1 << 100) - 1) == 0
    assert f((1 << 100)) == 100
    assert f((1 << 100) + 1) == 0
