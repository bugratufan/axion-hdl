"""
Cocotb functional CDC tests for PACKED and WIDE registers (SystemVerilog / Verilator).

SV parity for test_cdc_packed.py: the generator emits the same port and register
names for both backends, so these tests reuse the exact same stimulus/assertion
helpers against the Verilator-built SV DUT. This closes the last functional-parity
gap - packed-field and wide-chunk CDC were previously proven in simulation only
for the VHDL backend (and only structurally, via text match, for SV in
tests/python/test_cdc.py CDC-015).

Runs against both cdc_packed_controller (CDC_STAGE=3) and
cdc_packed_controller_stage2 (CDC_STAGE=2); see tests/run_tests.py.
"""

import cocotb

from test_cdc_packed import (
    _packed_rw_field_sync,
    _packed_ro_field_sync,
    _packed_mixed_rw_ro,
    _wide_rw_chunk_sync,
    _wide_ro_chunk_sync,
)


@cocotb.test()
async def test_sv_cdc_packed_rw_field_sync(dut):
    """CDC-015: SV packed RW fields cross to per-field module_clk ports (prime ratio)"""
    await _packed_rw_field_sync(dut, mod_period_ns=17)


@cocotb.test()
async def test_sv_cdc_packed_rw_field_sync_slow(dut):
    """CDC-015: SV packed RW fields cross when module_clk is 5x slower"""
    await _packed_rw_field_sync(dut, mod_period_ns=50)


@cocotb.test()
async def test_sv_cdc_packed_ro_field_sync(dut):
    """CDC-015: SV packed RO field inputs synchronize into the AXI read word (prime ratio)"""
    await _packed_ro_field_sync(dut, mod_period_ns=13)


@cocotb.test()
async def test_sv_cdc_packed_ro_field_sync_slow(dut):
    """CDC-015: SV packed RO field inputs synchronize when module_clk is 5x slower"""
    await _packed_ro_field_sync(dut, mod_period_ns=50)


@cocotb.test()
async def test_sv_cdc_packed_mixed_rw_ro(dut):
    """CDC-015: SV RW and RO fields of the same packed word are independently synced"""
    await _packed_mixed_rw_ro(dut, mod_period_ns=17)


@cocotb.test()
async def test_sv_cdc_wide_rw_chunk_sync(dut):
    """CDC-015: SV wide (64-bit) RW register recombines coherently in module domain (prime ratio)"""
    await _wide_rw_chunk_sync(dut, mod_period_ns=17)


@cocotb.test()
async def test_sv_cdc_wide_rw_chunk_sync_slow(dut):
    """CDC-015: SV wide (64-bit) RW register crosses when module_clk is 5x slower"""
    await _wide_rw_chunk_sync(dut, mod_period_ns=50)


@cocotb.test()
async def test_sv_cdc_wide_ro_chunk_sync(dut):
    """CDC-015: SV wide (64-bit) RO register synchronizes chunk-by-chunk into AXI reads (prime ratio)"""
    await _wide_ro_chunk_sync(dut, mod_period_ns=13)


@cocotb.test()
async def test_sv_cdc_wide_ro_chunk_sync_slow(dut):
    """CDC-015: SV wide (64-bit) RO register crosses when module_clk is 5x slower"""
    await _wide_ro_chunk_sync(dut, mod_period_ns=50)
