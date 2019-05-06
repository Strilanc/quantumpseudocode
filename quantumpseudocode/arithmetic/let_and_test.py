import cirq

import quantumpseudocode


def test_let_and_circuit():
    with quantumpseudocode.Sim(enforce_release_at_zero=False):
        with quantumpseudocode.LogCirqCircuit() as circuit:
            with quantumpseudocode.qmanaged_int(bits=3, name='q') as q:
                quantumpseudocode.emit(quantumpseudocode.LetAnd(q[0]).controlled_by(q[1] & q[2]))

    cirq.testing.assert_has_diagram(circuit, r"""
q[0]: ---X---
         |
q[1]: ---@---
         |
q[2]: ---@---
        """, use_unicode_characters=False)


def test_del_and_circuit():
    with quantumpseudocode.Sim(enforce_release_at_zero=False, phase_fixup_bias=True):
        with quantumpseudocode.LogCirqCircuit() as circuit:
            with quantumpseudocode.qmanaged_int(bits=3, name='q') as q:
                quantumpseudocode.emit(quantumpseudocode.DelAnd(q[0]).controlled_by(q[1] & q[2]))

    cirq.testing.assert_has_diagram(circuit, r"""
q[0]: ---Mxc-------

q[1]: ---------@---
               |
q[2]: ---------Z---
        """, use_unicode_characters=False)


    with quantumpseudocode.Sim(enforce_release_at_zero=False, phase_fixup_bias=False):
        with quantumpseudocode.LogCirqCircuit() as circuit:
            with quantumpseudocode.qmanaged_int(bits=3, name='b') as q:
                quantumpseudocode.emit(quantumpseudocode.DelAnd(q[0]).controlled_by(q[1] & q[2]))

    cirq.testing.assert_has_diagram(circuit, r"""
b[0]: ---Mxc---
        """, use_unicode_characters=False)
