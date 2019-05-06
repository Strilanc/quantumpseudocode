import random

import cirq

import quantumpseudocode


def test_vs_emulation():
    with quantumpseudocode.Sim(enforce_release_at_zero=False) as sim:
        bits = 4
        with quantumpseudocode.qmanaged_int(bits=bits, name='lvalue') as lvalue:
            for _ in range(10):
                sim.randomize_location(lvalue)

                old_state = sim.snapshot()
                op = quantumpseudocode.PlusEqualTimesGate(
                    lvalue=lvalue,
                    quantum_factor=random.randint(0, 1 << bits),
                    const_factor=random.randint(0, 1 << bits))
                quantumpseudocode.emit(op)
                sim.apply_op_via_emulation(op, forward=False)
                assert sim.snapshot() == old_state
