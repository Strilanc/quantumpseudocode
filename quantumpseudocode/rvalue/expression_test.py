import cirq

import quantumpseudocode as qp


def test_let_and_circuit():
    with qp.Sim(enforce_release_at_zero=False):
        with qp.LogCirqCircuit() as circuit:
            with qp.qmanaged_int(bits=3, name='q') as q:
                q[0].init(q[1] & q[2])

    cirq.testing.assert_has_diagram(circuit, r"""
q[0]: ---X---
         |
q[1]: ---@---
         |
q[2]: ---@---
        """, use_unicode_characters=False)


def test_del_and_circuit():
    with qp.Sim(enforce_release_at_zero=False, phase_fixup_bias=True):
        with qp.LogCirqCircuit() as circuit:
            with qp.qmanaged_int(bits=3, name='q') as q:
                q[0].clear(q[1] & q[2])

    cirq.testing.assert_has_diagram(circuit, r"""
q[0]: ---Mxc-------

q[1]: ---------@---
               |
q[2]: ---------Z---
        """, use_unicode_characters=False)

    with qp.Sim(enforce_release_at_zero=False, phase_fixup_bias=False):
        with qp.LogCirqCircuit() as circuit:
            with qp.qmanaged_int(bits=3, name='b') as q:
                q[0].clear(q[1] & q[2])

    cirq.testing.assert_has_diagram(circuit, r"""
b[0]: ---Mxc---
        """, use_unicode_characters=False)
