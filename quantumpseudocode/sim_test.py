from typing import List, Union, Callable, Any, Optional

import cirq
import quantumpseudocode


def test_sim():
    v1 = 15
    v2 = 235
    offset = 4
    bits = 10
    with quantumpseudocode.Sim():
        with quantumpseudocode.hold(val=v1, name='a') as a:
            with quantumpseudocode.qmanaged_int(bits=bits, name='out') as out:
                out += a * v2
                out += offset
                result = quantumpseudocode.measure(out, reset=True)
    assert result == (v1*v2 + offset) & ((1 << bits) - 1)


def test_count():
    v1 = 15
    v2 = 235
    offset = 4
    bits = 100
    with quantumpseudocode.Sim():
        with quantumpseudocode.CountNots() as counts:
            with quantumpseudocode.hold(val=v1, name='a') as a:
                with quantumpseudocode.qmanaged_int(bits=bits, name='out') as out:
                    out += a * v2
                    out += offset
                    _ = quantumpseudocode.measure(out, reset=True)
    assert len(counts.keys()) == 3
    assert counts[0] > 0
    assert counts[1] > 0
    assert 0 < counts[2] <= 1000
