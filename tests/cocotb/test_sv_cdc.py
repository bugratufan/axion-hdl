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

import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles, Timer

from test_axi_lite import (
    AxiLiteTestHelper,
    REG_STATUS,
    REG_TEMPERATURE,
    REG_CONTROL,
    REG_CONFIG,
    REG_CALIBRATION,
)
from test_cdc import start_clocks, reset_cdc_dut, _check_strobe_toggle_cdc


@cocotb.test()
async def test_sv_cdc_006_ro_path_sync(dut):
    """CDC-015: SV RO register path is synchronized module_clk -> axi_aclk"""
    axi_clk, mod_clk = await start_clocks(dut)
    assert mod_clk is not None, "SV CDC-006: module_clk must exist for a CDC-enabled DUT"

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
    assert mod_clk is not None, "SV CDC-007: module_clk must exist for a CDC-enabled DUT"

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
async def test_sv_cdc_pulse_sync_ratio_2x(dut):
    """CDC-018: SV write strobe toggle sync at a 2:1 clock ratio (module_clk 2x slower)"""
    assert getattr(dut, 'module_clk', None) is not None, \
        "module_clk must exist for a CDC-enabled DUT"
    await _check_strobe_toggle_cdc(
        dut, mod_period_ns=20, is_write=True,
        reg_addr=REG_CONTROL, strobe_signal_name='control_reg_wr_strobe')


@cocotb.test()
async def test_sv_cdc_pulse_sync_ratio_equal(dut):
    """CDC-018: SV write strobe toggle sync at a 1:1 clock ratio"""
    assert getattr(dut, 'module_clk', None) is not None, \
        "module_clk must exist for a CDC-enabled DUT"
    await _check_strobe_toggle_cdc(
        dut, mod_period_ns=10, is_write=True,
        reg_addr=REG_CONTROL, strobe_signal_name='control_reg_wr_strobe')


@cocotb.test()
async def test_sv_cdc_pulse_sync_module_faster(dut):
    """CDC-018: SV write strobe toggle sync, module_clk faster than axi_aclk"""
    assert getattr(dut, 'module_clk', None) is not None, \
        "module_clk must exist for a CDC-enabled DUT"
    await _check_strobe_toggle_cdc(
        dut, mod_period_ns=3, is_write=True,
        reg_addr=REG_CONTROL, strobe_signal_name='control_reg_wr_strobe')


@cocotb.test()
async def test_sv_cdc_pulse_sync_module_slower(dut):
    """CDC-018: SV write strobe toggle sync, module_clk 5x slower - must not be missed"""
    assert getattr(dut, 'module_clk', None) is not None, \
        "module_clk must exist for a CDC-enabled DUT"
    await _check_strobe_toggle_cdc(
        dut, mod_period_ns=50, is_write=True,
        reg_addr=REG_CONTROL, strobe_signal_name='control_reg_wr_strobe')


@cocotb.test()
async def test_sv_cdc_pulse_sync_prime_ratio(dut):
    """CDC-018: SV write strobe toggle sync at a worst-case (prime) clock ratio"""
    assert getattr(dut, 'module_clk', None) is not None, \
        "module_clk must exist for a CDC-enabled DUT"
    await _check_strobe_toggle_cdc(
        dut, mod_period_ns=17, is_write=True,
        reg_addr=REG_CONTROL, strobe_signal_name='control_reg_wr_strobe')


@cocotb.test()
async def test_sv_cdc_read_strobe_pulse_sync(dut):
    """CDC-018: SV read strobe toggle sync (module_clk slower than axi_aclk)"""
    assert getattr(dut, 'module_clk', None) is not None, \
        "module_clk must exist for a CDC-enabled DUT"
    await _check_strobe_toggle_cdc(
        dut, mod_period_ns=50, is_write=False,
        reg_addr=REG_TEMPERATURE, strobe_signal_name='temperature_reg_rd_strobe',
        ro_input_port='temperature_reg')


@cocotb.test()
async def test_sv_cdc_rw_register_both_strobes(dut):
    """CDC-018: SV RW register read+write strobes are independently synchronized"""
    assert getattr(dut, 'module_clk', None) is not None, \
        "module_clk must exist for a CDC-enabled DUT"
    await _check_strobe_toggle_cdc(
        dut, mod_period_ns=17, is_write=True,
        reg_addr=REG_CALIBRATION, strobe_signal_name='calibration_reg_wr_strobe')
    await _check_strobe_toggle_cdc(
        dut, mod_period_ns=17, is_write=False,
        reg_addr=REG_CALIBRATION, strobe_signal_name='calibration_reg_rd_strobe')


# =============================================================================
# RO/RW data-path ratio-sweep and edge-case parity with tests/cocotb/test_cdc.py
#
# The strobe toggle-synchronizer ratio sweep above already has SV parity.
# These tests port the plain multi-bit data synchronizer coverage (RO
# module_clk -> axi_aclk, RW axi_aclk -> module_clk) that previously only
# existed for the VHDL/GHDL DUT, so a data-path CDC regression that only
# shows up in the SystemVerilog backend's generated sync chain would still
# be caught here.
# =============================================================================

@cocotb.test()
async def test_sv_cdc_clock_ratio_2x(dut):
    """CDC-015: SV RO data path correctness at a 2:1 clock ratio (module_clk 2x slower)"""
    axi_clk, mod_clk = await start_clocks(dut, axi_period_ns=10, mod_period_ns=20)
    assert mod_clk is not None, "module_clk must exist for a CDC-enabled DUT"
    await reset_cdc_dut(dut, axi_clk, mod_clk)
    helper = AxiLiteTestHelper(dut)

    for val in range(10):
        await RisingEdge(mod_clk)
        dut.status_reg.value = val
        for _ in range(8):
            await RisingEdge(axi_clk)
        data, resp = await helper.read(REG_STATUS)
        assert resp == 0, f"SV CDC 2:1 ratio: AXI read failed at val={val}"
        assert data == val, f"SV CDC 2:1 ratio: expected {val:#x}, got {data:#x}"


@cocotb.test()
async def test_sv_cdc_clock_ratio_prime(dut):
    """CDC-015: SV RO data path correctness at a worst-case prime clock ratio"""
    axi_clk, mod_clk = await start_clocks(dut, axi_period_ns=10, mod_period_ns=17)
    assert mod_clk is not None, "module_clk must exist for a CDC-enabled DUT"
    await reset_cdc_dut(dut, axi_clk, mod_clk)
    helper = AxiLiteTestHelper(dut)

    for val in [0xDEADBEEF, 0xCAFEBABE, 0x12345678, 0x87654321]:
        await RisingEdge(mod_clk)
        dut.status_reg.value = val
        for _ in range(10):
            await RisingEdge(axi_clk)
        data, resp = await helper.read(REG_STATUS)
        assert resp == 0, f"SV CDC prime ratio: AXI read failed at val={val:#x}"
        assert data == val, f"SV CDC prime ratio: expected {val:#x}, got {data:#x}"


@cocotb.test()
async def test_sv_cdc_slow_to_fast(dut):
    """CDC-015: SV RO path, module_clk 5x slower than axi_aclk"""
    axi_clk, mod_clk = await start_clocks(dut, axi_period_ns=10, mod_period_ns=50)
    assert mod_clk is not None, "module_clk must exist for a CDC-enabled DUT"
    await reset_cdc_dut(dut, axi_clk, mod_clk)
    helper = AxiLiteTestHelper(dut)

    for i in range(10):
        await RisingEdge(mod_clk)
        dut.status_reg.value = 0x10000000 + i
        for _ in range(10):
            await RisingEdge(axi_clk)
        data, resp = await helper.read(REG_STATUS)
        assert resp == 0, f"SV CDC Slow to Fast: AXI read failed at i={i}"
        assert data == 0x10000000 + i, (
            f"SV CDC Slow to Fast: expected {0x10000000 + i:#x}, got {data:#x}")


@cocotb.test()
async def test_sv_cdc_fast_to_slow(dut):
    """CDC-015: SV RW path, module_clk 5x slower than axi_aclk"""
    axi_clk, mod_clk = await start_clocks(dut, axi_period_ns=10, mod_period_ns=50)
    assert mod_clk is not None, "module_clk must exist for a CDC-enabled DUT"
    await reset_cdc_dut(dut, axi_clk, mod_clk)
    helper = AxiLiteTestHelper(dut)

    for i in range(5):
        test_value = 0x20000000 + i
        await helper.write(REG_CONFIG, test_value)
        for _ in range(6):
            await RisingEdge(mod_clk)
        observed = int(dut.config_reg.value)
        assert observed == test_value, (
            f"SV CDC Fast to Slow: expected {test_value:#010x}, got {observed:#010x}")


@cocotb.test()
async def test_sv_cdc_async_reset(dut):
    """CDC-015: SV axi_aresetn clears the RO sync chain and RW storage (no module_resetn port)"""
    axi_clk, mod_clk = await start_clocks(dut)
    assert mod_clk is not None, "module_clk must exist for a CDC-enabled DUT"
    await reset_cdc_dut(dut, axi_clk, mod_clk)
    helper = AxiLiteTestHelper(dut)

    await RisingEdge(mod_clk)
    dut.status_reg.value = 0x7E7E7E7E
    for _ in range(8):
        await RisingEdge(axi_clk)
    data, _ = await helper.read(REG_STATUS)
    assert data == 0x7E7E7E7E, "SV CDC Async Reset: setup RO read failed before reset"

    await helper.write(REG_CONFIG, 0xDEADBEEF)
    data, _ = await helper.read(REG_CONFIG)
    assert data == 0xDEADBEEF, "SV CDC Async Reset: setup RW readback failed before reset"

    await RisingEdge(axi_clk)
    dut.axi_aresetn.value = 0
    await ClockCycles(axi_clk, 5)

    # Check the last RO synchronizer stage directly (status_reg_sync{N-1}
    # in the generated SV source is what the read mux uses, e.g.
    # `rdata_reg = status_reg_sync2` for a 3-stage DUT) while reset is
    # still held, rather than through an AXI read: the read handshake
    # takes several more axi_aclk edges, by which time the chain would
    # already have re-filled with the still-live module_clk input and mask
    # the behavior under test. The SV generator declares each stage as a
    # discrete scalar signal (status_reg_sync0, _sync1, ...), matching the
    # VHDL backend's naming, so these are accessed directly by name. The
    # stage count varies (3 for sensor_controller, 2 for
    # sensor_controller_stage2), so probe for the highest-numbered stage
    # that actually exists instead of hardcoding it.
    stage = 0
    while hasattr(dut, f"status_reg_sync{stage + 1}"):
        stage += 1
    last_stage_sig = getattr(dut, f"status_reg_sync{stage}")
    assert int(last_stage_sig.value) == 0, (
        f"SV CDC Async Reset: status_reg_sync{stage} (last RO sync stage) "
        "must be held at 0 while axi_aresetn is asserted, regardless of "
        "the live module_clk input")

    dut.axi_aresetn.value = 1

    data, _ = await helper.read(REG_CONFIG)
    assert data == 0, f"SV CDC Async Reset: RW register should reset to 0, got {data:#x}"

    for _ in range(8):
        await RisingEdge(axi_clk)
    data, resp = await helper.read(REG_STATUS)
    assert resp == 0, "SV CDC Async Reset: AXI read failed after reset release"
    assert data == 0x7E7E7E7E, (
        f"SV CDC Async Reset: RO path did not re-converge after reset, got {data:#x}")


@cocotb.test()
async def test_sv_cdc_ro_multibit_settle_no_torn_reads(dut):
    """CDC-015: SV RO synchronizer never exposes a torn/mixed value mid-crossing"""
    axi_clk, mod_clk = await start_clocks(dut, axi_period_ns=10, mod_period_ns=13)
    assert mod_clk is not None, "module_clk must exist for a CDC-enabled DUT"
    await reset_cdc_dut(dut, axi_clk, mod_clk)
    helper = AxiLiteTestHelper(dut)

    old_val, new_val = 0x00000000, 0xFFFFFFFF

    await RisingEdge(mod_clk)
    dut.status_reg.value = old_val
    for _ in range(8):
        await RisingEdge(axi_clk)
    data, _ = await helper.read(REG_STATUS)
    assert data == old_val, f"SV CDC data coherency: setup read got {data:#x}"

    await RisingEdge(mod_clk)
    dut.status_reg.value = new_val

    valid_values = {old_val, new_val}
    torn_reads = []
    for _ in range(10):
        await RisingEdge(axi_clk)
        data, resp = await helper.read(REG_STATUS)
        assert resp == 0, "SV CDC data coherency: AXI read failed during transition"
        if data not in valid_values:
            torn_reads.append(data)

    assert not torn_reads, (
        f"SV CDC data coherency: observed torn/mixed values: "
        f"{[hex(v) for v in torn_reads]}")

    data, _ = await helper.read(REG_STATUS)
    assert data == new_val, f"SV CDC data coherency: expected settle to {new_val:#x}, got {data:#x}"
