import cirq

import quantumpseudocode as qp


def test_let_and_circuit_str():
    assert str(qp.LetAnd(lvalue=qp.Qubit('q'))) == 'let q := 1'
    assert repr(qp.LetAnd(lvalue=qp.Qubit('q'))) == "qp.LetAnd(lvalue=qp.Qubit(qp.UniqueHandle('q', 0), None))"

    assert str(qp.DelAnd(qp.Qubit('q'))) == 'del q =: 1'
    assert repr(qp.DelAnd(qp.Qubit('q'))) == "qp.DelAnd(qp.Qubit(qp.UniqueHandle('q', 0), None))"


def test_let_and_circuit():
    with qp.Sim(enforce_release_at_zero=False):
        with qp.LogCirqCircuit() as circuit:
            with qp.qmanaged_int(bits=3, name='q') as q:
                qp.emit(qp.LetAnd(q[0]).controlled_by(q[1] & q[2]))

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
                qp.emit(qp.DelAnd(q[0]).controlled_by(q[1] & q[2]))

    cirq.testing.assert_has_diagram(circuit, r"""
q[0]: ---Mxc-------

q[1]: ---------@---
               |
q[2]: ---------Z---
        """, use_unicode_characters=False)

    with qp.Sim(enforce_release_at_zero=False, phase_fixup_bias=False):
        with qp.LogCirqCircuit() as circuit:
            with qp.qmanaged_int(bits=3, name='b') as q:
                qp.emit(qp.DelAnd(q[0]).controlled_by(q[1] & q[2]))

    cirq.testing.assert_has_diagram(circuit, r"""
b[0]: ---Mxc---
        """, use_unicode_characters=False)
