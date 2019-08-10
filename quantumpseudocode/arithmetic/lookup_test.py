import random

import cirq

import quantumpseudocode as qp


def test_xor_lookup():
    with qp.Sim(phase_fixup_bias=True, enforce_release_at_zero=False):
        with qp.LogCirqCircuit() as circuit:
            with qp.qmanaged_int(bits=4, name='addr') as addr:
                with qp.qmanaged_int(bits=8, name='out') as out:
                    with qp.qmanaged(name='cnt') as cnt:
                        out ^= qp.LookupTable(range(1, 17))[addr] & qp.controlled_by(cnt)

    cirq.testing.assert_has_diagram(circuit, r"""
_lookup_prefix: -----X---X---@---@-------------------------------------------------------------------------------------@-------------------------------------------------------------------------------------------@---X---@---@-------------------------------------------------------------------------------------@-------------------------------------------------------------------------------------------@---Mxc-------
                     |   |   |   |                                                                                     |                                                                                           |   |   |   |                                                                                     |                                                                                           |
_lookup_prefix_1: ---|---|---X---X---@---@---------------------------------@---------------------------------------@---X---@---@---------------------------------@---------------------------------------@---Mxc---|---|---X---X---@---@---------------------------------@---------------------------------------@---X---@---@---------------------------------@---------------------------------------@---Mxc---|-------------
                     |   |   |       |   |                                 |                                       |       |   |                                 |                                       |         |   |   |       |   |                                 |                                       |       |   |                                 |                                       |         |
_lookup_prefix_2: ---|---|---|-------X---X---@---@-------@-------------@---X---@---@-------@-------------@---Mxc---|-------X---X---@---@-------@-------------@---X---@---@-------@-------------@---Mxc---|---------|---|---|-------X---X---@---@-------@-------------@---X---@---@-------@-------------@---Mxc---|-------X---X---@---@-------@-------------@---X---@---@-------@-------------@---Mxc---|---------|-------------
                     |   |   |       |       |   |       |             |       |   |       |             |         |       |       |   |       |             |       |   |       |             |         |         |   |   |       |       |   |       |             |       |   |       |             |         |       |       |   |       |             |       |   |       |             |         |         |
_lookup_prefix_3: ---|---|---|-------|-------X---X---@---X---@---Mxc---|-------X---X---@---X---@---Mxc---|---------|-------|-------X---X---@---X---@---Mxc---|-------X---X---@---X---@---Mxc---|---------|---------|---|---|-------|-------X---X---@---X---@---Mxc---|-------X---X---@---X---@---Mxc---|---------|-------|-------X---X---@---X---@---Mxc---|-------X---X---@---X---@---Mxc---|---------|---------|-------------
                     |   |   |       |       |       |       |         |       |       |       |         |         |       |       |       |       |         |       |       |       |         |         |         |   |   |       |       |       |       |         |       |       |       |         |         |       |       |       |       |         |       |       |       |         |         |         |
addr[0]: ------------|---|---|-------|-------@-------|-------|---------Z-------@-------|-------|---------Z---------|-------|-------@-------|-------|---------Z-------@-------|-------|---------Z---------|---------|---|---|-------|-------@-------|-------|---------Z-------@-------|-------|---------Z---------|-------|-------@-------|-------|---------Z-------@-------|-------|---------Z---------|---------|-------------
                     |   |   |       |               |       |                         |       |                   |       |               |       |                         |       |                   |         |   |   |       |               |       |                         |       |                   |       |               |       |                         |       |                   |         |
addr[1]: ------------|---|---|-------@---------------|-------|-------------------------|-------|-------------------Z-------@---------------|-------|-------------------------|-------|-------------------Z---------|---|---|-------@---------------|-------|-------------------------|-------|-------------------Z-------@---------------|-------|-------------------------|-------|-------------------Z---------|-------------
                     |   |   |                       |       |                         |       |                                           |       |                         |       |                             |   |   |                       |       |                         |       |                                           |       |                         |       |                             |
addr[2]: ------------|---|---@-----------------------|-------|-------------------------|-------|-------------------------------------------|-------|-------------------------|-------|-----------------------------Z---|---@-----------------------|-------|-------------------------|-------|-------------------------------------------|-------|-------------------------|-------|-----------------------------Z-------------
                     |   |                           |       |                         |       |                                           |       |                         |       |                                 |                           |       |                         |       |                                           |       |                         |       |
addr[3]: ------------@---|---------------------------|-------|-------------------------|-------|-------------------------------------------|-------|-------------------------|-------|---------------------------------|---------------------------|-------|-------------------------|-------|-------------------------------------------|-------|-------------------------|-------|---------------------------------------Z---
                     |   |                           |       |                         |       |                                           |       |                         |       |                                 |                           |       |                         |       |                                           |       |                         |       |                                       |
cnt: ----------------@---@---------------------------|-------|-------------------------|-------|-------------------------------------------|-------|-------------------------|-------|---------------------------------@---------------------------|-------|-------------------------|-------|-------------------------------------------|-------|-------------------------|-------|---------------------------------------@---
                                                     |       |                         |       |                                           |       |                         |       |                                                             |       |                         |       |                                           |       |                         |       |
out[0]: ---------------------------------------------X-------|-------------------------X-------|-------------------------------------------X-------|-------------------------X-------|-------------------------------------------------------------X-------|-------------------------X-------|-------------------------------------------X-------|-------------------------X-------|-------------------------------------------
                                                             |                         |       |                                           |       |                         |       |                                                             |       |                         |       |                                           |       |                         |       |
out[1]: -----------------------------------------------------X-------------------------X-------|-------------------------------------------|-------X-------------------------X-------|-------------------------------------------------------------|-------X-------------------------X-------|-------------------------------------------|-------X-------------------------X-------|-------------------------------------------
                                                                                               |                                           |       |                         |       |                                                             |       |                         |       |                                           |       |                         |       |
out[2]: ---------------------------------------------------------------------------------------X-------------------------------------------X-------X-------------------------X-------|-------------------------------------------------------------|-------|-------------------------|-------X-------------------------------------------X-------X-------------------------X-------|-------------------------------------------
                                                                                                                                                                                     |                                                             |       |                         |       |                                           |       |                         |       |
out[3]: -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------X-------------------------------------------------------------X-------X-------------------------X-------X-------------------------------------------X-------X-------------------------X-------|-------------------------------------------
                                                                                                                                                                                                                                                                                                                                                                                   |
out[4]: ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------X-------------------------------------------
        """, use_unicode_characters=False)


def test_redundant_lookup():
    with qp.Sim(phase_fixup_bias=True, enforce_release_at_zero=False):
        with qp.LogCirqCircuit() as circuit:
            with qp.qmanaged_int(bits=4, name='addr') as addr:
                with qp.qmanaged_int(bits=8, name='out') as out:
                    with qp.qmanaged(name='cnt') as cnt:
                        out ^= qp.LookupTable([3] * 16)[addr] & qp.controlled_by(cnt)

    cirq.testing.assert_has_diagram(circuit, r"""
cnt: ------@---
           |
out[0]: ---X---
           |
out[1]: ---X---
        """, use_unicode_characters=False)


def test_del_lookup():
    with qp.Sim(phase_fixup_bias=True, enforce_release_at_zero=False):
        with qp.LogCirqCircuit() as circuit:
            with qp.qmanaged_int(bits=4, name='addr') as addr:
                    with qp.qmanaged(name='cnt'):
                        with qp.hold(qp.LookupTable(range(1, 17))[addr], name='out'):
                            circuit[:] = []

    cirq.testing.assert_has_diagram(circuit, r"""
_lookup_prefix: ---------------------------------------X---X---@---@---------------@-----------------@---X---@---@-------@---------------------@---Mxc-------------------------------------------------
                                                       |       |   |               |                 |       |   |       |                     |
_lookup_prefix_1: -------------------------------------|-------X---X---@---@---@---X---@---@---Mxc---|-------X---X---@---X---@---@---@---Mxc---|-------------------------------------------------------
                                                       |       |       |   |   |       |   |         |       |       |       |   |   |         |
addr[0]: ----------------------@-----------------------|-------|-------|---|---|-------|---|---------|-------|-------|-------|---|---|---------|---------------------------------------------@---------
                               |                       |       |       |   |   |       |   |         |       |       |       |   |   |         |                                             |
addr[1]: ----------------------|-------@-------@-------|-------|-------|---|---|-------|---|---------|-------|-------|-------|---|---|---------|---------------------------@---@-------------|---------
                               |       |       |       |       |       |   |   |       |   |         |       |       |       |   |   |         |                           |   |             |
addr[2]: ----------------------|-------|-------|-------|-------@-------|---|---|-------|---|---------Z-------@-------|-------|---|---|---------Z---------------------------|---|-------------|---------
                               |       |       |       |               |   |   |       |   |                         |       |   |   |                                     |   |             |
addr[3]: ----------------------|-------|-------|-------@---------------|---|---|-------|---|-------------------------|-------|---|---|-------------------Z-----------------|---|-------------|---------
                               |       |       |                       |   |   |       |   |                         |       |   |   |                                     |   |             |
out[0]: -------------Mxc---X---@---X---@---X---|-----------------------Z---|---|-------|---|-------------------------|-------Z---|---|-----------------------X-------------Z---|---X---------Z---Mxc---
                               |   |   |   |   |                           |   |       |   |                         |           |   |                       |                 |   |
out[1]: -------------Mxc-------X---@---|---|---@---X-----------------------Z---|-------|---|-------------------------|-----------Z---|-----------------------|---X-------------Z---@---Mxc-------------
                                       |   |   |   |                           |       |   |                         |               |                       |   |
out[2]: -------------Mxc---------------X---@---|---|---------------------------|-------Z---|-------------------------Z---------------|-----------------------@---|---Mxc-------------------------------
                                               |   |                           |           |                                         |                           |
out[3]: -------------Mxc-----------------------X---@---------------------------Z-----------Z-----------------------------------------Z---------------------------@---Mxc-------------------------------

out[4]: -------------Mxc-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        """, use_unicode_characters=False)


def test_do():
    for n in range(1, 10):
        qp.testing.assert_semi_quantum_func_is_consistent(
            qp.arithmetic.do_xor_lookup,
            fuzz_space={
                'table': lambda: qp.LookupTable.random(n, range(0, 10)),
                'address': lambda table: random.randint(0, len(table) - 1),
                'lvalue': lambda table: qp.IntBuf.random(length=table.output_len()),
            },
            fuzz_count=10)

        qp.testing.assert_semi_quantum_func_is_consistent(
            qp.arithmetic.del_xor_lookup,
            fuzz_space={
                'control': [False, True],
                'table': lambda: qp.LookupTable.random(n, range(0, 10)),
                'address': lambda table: random.randint(0, len(table) - 1),
                'lvalue': lambda control, address, table: qp.IntBuf.raw(length=table.output_len(),
                                                                        val=table.values[address] if control else 0),
            },
            fuzz_count=10)
