import cirq

import quantumpseudocode


def test_xor_lookup():
    with quantumpseudocode.Sim(phase_fixup_bias=True, enforce_release_at_zero=False):
        with quantumpseudocode.LogCirqCircuit() as circuit:
            with quantumpseudocode.qmanaged_int(bits=4, name='addr') as addr:
                with quantumpseudocode.qmanaged_int(bits=8, name='out') as out:
                    with quantumpseudocode.qmanaged(name='cnt') as cnt:
                        with quantumpseudocode.condition(cnt):
                            out ^= quantumpseudocode.LookupTable(range(1, 17))[addr]

    cirq.testing.assert_has_diagram(circuit, r"""
_lookup_prefix: -----X---X---@---@-------------------------------------------------------------------@-------------------------------------------------------------------@---X---@---@-------------------------------------------------------------------@-------------------------------------------------------------------@---X---
                     |   |   |   |                                                                   |                                                                   |   |   |   |                                                                   |                                                                   |   |
_lookup_prefix_1: ---|---|---X---X---@---@---------------------------@---------------------------@---X---@---@---------------------------@---------------------------@---X---|---X---X---@---@---------------------------@---------------------------@---X---@---@---------------------------@---------------------------@---X---|---
                     |   |   |       |   |                           |                           |       |   |                           |                           |   |   |   |       |   |                           |                           |       |   |                           |                           |   |   |
_lookup_prefix_2: ---|---|---|-------X---X---@---@-------@-------@---X---@---@-------@-------@---X-------X---X---@---@-------@-------@---X---@---@-------@-------@---X---|---|---|-------X---X---@---@-------@-------@---X---@---@-------@-------@---X-------X---X---@---@-------@-------@---X---@---@-------@-------@---X---|---|---
                     |   |   |       |       |   |       |       |       |   |       |       |   |       |       |   |       |       |       |   |       |       |   |   |   |   |       |       |   |       |       |       |   |       |       |   |       |       |   |       |       |       |   |       |       |   |   |   |
_lookup_prefix_3: ---|---|---|-------|-------X---X---@---X---@---X-------X---X---@---X---@---X---|-------|-------X---X---@---X---@---X-------X---X---@---X---@---X---|---|---|---|-------|-------X---X---@---X---@---X-------X---X---@---X---@---X---|-------|-------X---X---@---X---@---X-------X---X---@---X---@---X---|---|---|---
                     |   |   |       |       |       |       |   |       |       |       |   |   |       |       |       |       |   |       |       |       |   |   |   |   |   |       |       |       |       |   |       |       |       |   |   |       |       |       |       |   |       |       |       |   |   |   |   |
addr[0]: ------------|---|---|-------|-------@-------|-------|---@-------@-------|-------|---@---|-------|-------@-------|-------|---@-------@-------|-------|---@---|---|---|---|-------|-------@-------|-------|---@-------@-------|-------|---@---|-------|-------@-------|-------|---@-------@-------|-------|---@---|---|---|---
                     |   |   |       |               |       |                   |       |       |       |               |       |                   |       |       |   |   |   |       |               |       |                   |       |       |       |               |       |                   |       |       |   |   |
addr[1]: ------------|---|---|-------@---------------|-------|-------------------|-------|-------@-------@---------------|-------|-------------------|-------|-------@---|---|---|-------@---------------|-------|-------------------|-------|-------@-------@---------------|-------|-------------------|-------|-------@---|---|---
                     |   |   |                       |       |                   |       |                               |       |                   |       |           |   |   |                       |       |                   |       |                               |       |                   |       |           |   |
addr[2]: ------------|---|---@-----------------------|-------|-------------------|-------|-------------------------------|-------|-------------------|-------|-----------@---|---@-----------------------|-------|-------------------|-------|-------------------------------|-------|-------------------|-------|-----------@---|---
                     |   |                           |       |                   |       |                               |       |                   |       |               |                           |       |                   |       |                               |       |                   |       |               |
addr[3]: ------------@---|---------------------------|-------|-------------------|-------|-------------------------------|-------|-------------------|-------|---------------|---------------------------|-------|-------------------|-------|-------------------------------|-------|-------------------|-------|---------------@---
                     |   |                           |       |                   |       |                               |       |                   |       |               |                           |       |                   |       |                               |       |                   |       |               |
cnt: ----------------@---@---------------------------|-------|-------------------|-------|-------------------------------|-------|-------------------|-------|---------------@---------------------------|-------|-------------------|-------|-------------------------------|-------|-------------------|-------|---------------@---
                                                     |       |                   |       |                               |       |                   |       |                                           |       |                   |       |                               |       |                   |       |
out[0]: ---------------------------------------------X-------|-------------------X-------|-------------------------------X-------|-------------------X-------|-------------------------------------------X-------|-------------------X-------|-------------------------------X-------|-------------------X-------|-------------------
                                                             |                   |       |                               |       |                   |       |                                           |       |                   |       |                               |       |                   |       |
out[1]: -----------------------------------------------------X-------------------X-------|-------------------------------|-------X-------------------X-------|-------------------------------------------|-------X-------------------X-------|-------------------------------|-------X-------------------X-------|-------------------
                                                                                         |                               |       |                   |       |                                           |       |                   |       |                               |       |                   |       |
out[2]: ---------------------------------------------------------------------------------X-------------------------------X-------X-------------------X-------|-------------------------------------------|-------|-------------------|-------X-------------------------------X-------X-------------------X-------|-------------------
                                                                                                                                                             |                                           |       |                   |       |                               |       |                   |       |
out[3]: -----------------------------------------------------------------------------------------------------------------------------------------------------X-------------------------------------------X-------X-------------------X-------X-------------------------------X-------X-------------------X-------|-------------------
                                                                                                                                                                                                                                                                                                                 |
out[4]: ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------X-------------------
        """, use_unicode_characters=False)


def test_redundant_lookup():
    with quantumpseudocode.Sim(phase_fixup_bias=True, enforce_release_at_zero=False):
        with quantumpseudocode.LogCirqCircuit() as circuit:
            with quantumpseudocode.qmanaged_int(bits=4, name='addr') as addr:
                with quantumpseudocode.qmanaged_int(bits=8, name='out') as out:
                    with quantumpseudocode.qmanaged(name='cnt') as cnt:
                        with quantumpseudocode.condition(cnt):
                            out ^= quantumpseudocode.LookupTable([3] * 16)[addr]

    cirq.testing.assert_has_diagram(circuit, r"""
addr[0]: ---X-------X---
            |       |
addr[1]: ---X-------X---
            |       |
addr[2]: ---X-------X---
            |       |
addr[3]: ---X-------X---

cnt: -----------@-------
                |
out[0]: --------X-------
                |
out[1]: --------X-------
        """, use_unicode_characters=False)


def test_del_lookup():
    with quantumpseudocode.Sim(phase_fixup_bias=True, enforce_release_at_zero=False):
        with quantumpseudocode.LogCirqCircuit() as circuit:
            with quantumpseudocode.qmanaged_int(bits=4, name='addr') as addr:
                    with quantumpseudocode.qmanaged(name='cnt'):
                        with quantumpseudocode.hold(quantumpseudocode.LookupTable(range(1, 17))[addr], name='out'):
                            circuit[:] = []

    cirq.testing.assert_has_diagram(circuit, r"""
_lookup_prefix: -----X---X---@---@-------------------------------------------------------------------@-------------------------------------------------------------------@---X---@---@-------------------------------------------------------------------@-------------------------------------------------------------------@---X---
                     |       |   |                                                                   |                                                                   |       |   |                                                                   |                                                                   |   |
_lookup_prefix_1: ---|-------X---X---@---@---------------------------@---------------------------@---X---@---@---------------------------@---------------------------@---X-------X---X---@---@---------------------------@---------------------------@---X---@---@---------------------------@---------------------------@---X---|---
                     |       |       |   |                           |                           |       |   |                           |                           |   |       |       |   |                           |                           |       |   |                           |                           |   |   |
_lookup_prefix_2: ---|-------|-------X---X---@---@-------@-------@---X---@---@-------@-------@---X-------X---X---@---@-------@-------@---X---@---@-------@-------@---X---|-------|-------X---X---@---@-------@-------@---X---@---@-------@-------@---X-------X---X---@---@-------@-------@---X---@---@-------@-------@---X---|---|---
                     |       |       |       |   |       |       |       |   |       |       |   |       |       |   |       |       |       |   |       |       |   |   |       |       |       |   |       |       |       |   |       |       |   |       |       |   |       |       |       |   |       |       |   |   |   |
_lookup_prefix_3: ---|-------|-------|-------X---X---@---X---@---X-------X---X---@---X---@---X---|-------|-------X---X---@---X---@---X-------X---X---@---X---@---X---|---|-------|-------|-------X---X---@---X---@---X-------X---X---@---X---@---X---|-------|-------X---X---@---X---@---X-------X---X---@---X---@---X---|---|---|---
                     |       |       |       |       |       |   |       |       |       |   |   |       |       |       |       |   |       |       |       |   |   |   |       |       |       |       |       |   |       |       |       |   |   |       |       |       |       |   |       |       |       |   |   |   |   |
addr[0]: ------------|-------|-------|-------@-------|-------|---@-------@-------|-------|---@---|-------|-------@-------|-------|---@-------@-------|-------|---@---|---|-------|-------|-------@-------|-------|---@-------@-------|-------|---@---|-------|-------@-------|-------|---@-------@-------|-------|---@---|---|---|---
                     |       |       |               |       |                   |       |       |       |               |       |                   |       |       |   |       |       |               |       |                   |       |       |       |               |       |                   |       |       |   |   |
addr[1]: ------------|-------|-------@---------------|-------|-------------------|-------|-------@-------@---------------|-------|-------------------|-------|-------@---|-------|-------@---------------|-------|-------------------|-------|-------@-------@---------------|-------|-------------------|-------|-------@---|---|---
                     |       |                       |       |                   |       |                               |       |                   |       |           |       |                       |       |                   |       |                               |       |                   |       |           |   |
addr[2]: ------------|-------@-----------------------|-------|-------------------|-------|-------------------------------|-------|-------------------|-------|-----------@-------@-----------------------|-------|-------------------|-------|-------------------------------|-------|-------------------|-------|-----------@---|---
                     |                               |       |                   |       |                               |       |                   |       |                                           |       |                   |       |                               |       |                   |       |               |
addr[3]: ------------@-------------------------------|-------|-------------------|-------|-------------------------------|-------|-------------------|-------|-------------------------------------------|-------|-------------------|-------|-------------------------------|-------|-------------------|-------|---------------@---
                                                     |       |                   |       |                               |       |                   |       |                                           |       |                   |       |                               |       |                   |       |
out[0]: ---------------------------------------------X-------|-------------------X-------|-------------------------------X-------|-------------------X-------|-------------------------------------------X-------|-------------------X-------|-------------------------------X-------|-------------------X-------|-------------------
                                                             |                   |       |                               |       |                   |       |                                           |       |                   |       |                               |       |                   |       |
out[1]: -----------------------------------------------------X-------------------X-------|-------------------------------|-------X-------------------X-------|-------------------------------------------|-------X-------------------X-------|-------------------------------|-------X-------------------X-------|-------------------
                                                                                         |                               |       |                   |       |                                           |       |                   |       |                               |       |                   |       |
out[2]: ---------------------------------------------------------------------------------X-------------------------------X-------X-------------------X-------|-------------------------------------------|-------|-------------------|-------X-------------------------------X-------X-------------------X-------|-------------------
                                                                                                                                                             |                                           |       |                   |       |                               |       |                   |       |
out[3]: -----------------------------------------------------------------------------------------------------------------------------------------------------X-------------------------------------------X-------X-------------------X-------X-------------------------------X-------X-------------------X-------|-------------------
                                                                                                                                                                                                                                                                                                                 |
out[4]: ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------X-------------------
        """, use_unicode_characters=False)
