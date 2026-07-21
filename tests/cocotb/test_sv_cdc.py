"""
Cocotb CDC (Clock Domain Crossing) Tests for SystemVerilog Generated Modules

Mirrors tests/cocotb/test_cdc.py for the SystemVerilog output, proving
CDC-015 (SystemVerilog CDC parity) and CDC-018/019 (strobe toggle
synchronizer, honoring the configured CDC_STAGE) hold functionally under
simulation, not just structurally in the generated source. Runs the exact
same assertions against the SV DUT (Verilator) that test_cdc.py runs
against the VHDL DUT (GHDL) - the same register/port names are generated
by both backends for the same source annotations.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles

from test_axi_lite import (
    AxiLiteTestHelper,
    REG_TEMPERATURE,
    REG_CONTROL,
    REG_CALIBRATION,
)
from test_cdc import start_clocks, reset_cdc_dut, _check_strobe_toggle_cdc


@cocotb.test()
async def test_sv_cdc_006_ro_path_sync(dut):
    """CDC-015: SV RO register path is synchronized module_clk -> axi_aclk"""
    axi_clk, mod_clk = await start_clocks(dut)
    if mod_clk is None:
        dut._log.warning("SV CDC-006: module_clk not found, skipping")
        return

    await reset_cdc_dut(dut, axi_clk, mod_clk)

    helper = AxiLiteTestHelper(dut)
    test_val = 0x2222
    await RisingEdge(mod_clk)
    dut.temperature_reg.value = test_val

    for _ in range(8):
        await RisingEdge(axi_clk)

    data, resp = await helper.read(REG_TEMPERATURE)
    assert resp == 0, f"SV CDC-006: read response must be OKAY, got {resp}"
    assert data == test_val, (
        f"SV CDC-006: expected synchronized temperature_reg={test_val:#x}, got {data:#x}")


@cocotb.test()
async def test_sv_cdc_007_rw_path_sync(dut):
    """CDC-015: SV RW register path is synchronized axi_aclk -> module_clk"""
    axi_clk, mod_clk = await start_clocks(dut)
    if mod_clk is None:
        dut._log.warning("SV CDC-007: module_clk not found, skipping")
        return

    await reset_cdc_dut(dut, axi_clk, mod_clk)

    helper = AxiLiteTestHelper(dut)
    test_val = 0xABCD1234
    await helper.write(REG_CALIBRATION, test_val)

    for _ in range(8):
        await RisingEdge(mod_clk)

    assert int(dut.calibration_reg.value) == test_val, (
        "SV CDC-007: calibration_reg module_clk-domain output "
        f"did not settle to {test_val:#010x}")


@cocotb.test()
async def test_sv_cdc_pulse_sync_ratio_equal(dut):
    """CDC-018: SV write strobe toggle sync at a 1:1 clock ratio"""
    if getattr(dut, 'module_clk', None) is None:
        return
    await _check_strobe_toggle_cdc(
        dut, mod_period_ns=10, is_write=True,
        reg_addr=REG_CONTROL, strobe_signal_name='control_reg_wr_strobe')


@cocotb.test()
async def test_sv_cdc_pulse_sync_module_faster(dut):
    """CDC-018: SV write strobe toggle sync, module_clk faster than axi_aclk"""
    if getattr(dut, 'module_clk', None) is None:
        return
    await _check_strobe_toggle_cdc(
        dut, mod_period_ns=3, is_write=True,
        reg_addr=REG_CONTROL, strobe_signal_name='control_reg_wr_strobe')


@cocotb.test()
async def test_sv_cdc_pulse_sync_module_slower(dut):
    """CDC-018: SV write strobe toggle sync, module_clk 5x slower - must not be missed"""
    if getattr(dut, 'module_clk', None) is None:
        return
    await _check_strobe_toggle_cdc(
        dut, mod_period_ns=50, is_write=True,
        reg_addr=REG_CONTROL, strobe_signal_name='control_reg_wr_strobe')


@cocotb.test()
async def test_sv_cdc_pulse_sync_prime_ratio(dut):
    """CDC-018: SV write strobe toggle sync at a worst-case (prime) clock ratio"""
    if getattr(dut, 'module_clk', None) is None:
        return
    await _check_strobe_toggle_cdc(
        dut, mod_period_ns=17, is_write=True,
        reg_addr=REG_CONTROL, strobe_signal_name='control_reg_wr_strobe')


@cocotb.test()
async def test_sv_cdc_read_strobe_pulse_sync(dut):
    """CDC-018: SV read strobe toggle sync (module_clk slower than axi_aclk)"""
    if getattr(dut, 'module_clk', None) is None:
        return
    await _check_strobe_toggle_cdc(
        dut, mod_period_ns=50, is_write=False,
        reg_addr=REG_TEMPERATURE, strobe_signal_name='temperature_reg_rd_strobe',
        ro_input_port='temperature_reg')


@cocotb.test()
async def test_sv_cdc_rw_register_both_strobes(dut):
    """CDC-018: SV RW register read+write strobes are independently synchronized"""
    if getattr(dut, 'module_clk', None) is None:
        return
    await _check_strobe_toggle_cdc(
        dut, mod_period_ns=17, is_write=True,
        reg_addr=REG_CALIBRATION, strobe_signal_name='calibration_reg_wr_strobe')
    await _check_strobe_toggle_cdc(
        dut, mod_period_ns=17, is_write=False,
        reg_addr=REG_CALIBRATION, strobe_signal_name='calibration_reg_rd_strobe')
