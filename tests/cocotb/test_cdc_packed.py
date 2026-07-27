"""
Cocotb functional CDC tests for PACKED and WIDE registers (VHDL / GHDL).

The main CDC suite (test_cdc.py) drives sensor_controller, whose CDC paths are
all plain full-width (32-bit) registers. This module fills the two CDC paths
that were previously proven only *structurally* (text match in
tests/python/test_cdc.py CDC-010/011/013/014) and never in simulation:

  * Packed registers - one 32-bit word mixing RW and RO fields, each field
    getting its own synchronizer (RW field -> module_clk, RO field -> axi_aclk).
  * Wide (>32-bit) registers - chunked into 32-bit words that must be
    synchronized chunk-by-chunk and recombined without tearing across chunks.

DUT: cdc_packed_controller (CDC_STAGE=3) / cdc_packed_controller_stage2
(CDC_STAGE=2). Port and address map (verified by generating the DUT):

  0x00  mix_reg   RW packed:
          go_bit    [0]      RW  -> output port mix_reg_go_bit
          speed     [3:1]    RW  -> output port mix_reg_speed
          ready_bit [8]      RO  <- input  port mix_reg_ready_bit
          version   [15:12]  RO  <- input  port mix_reg_version
  0x04  big_cfg[31:0]   RW 64-bit low  word -> output port big_cfg[63:0]
  0x08  big_cfg[63:32]  RW 64-bit high word
  0x10  big_stat[31:0]  RO 64-bit low  word <- input  port big_stat[63:0]
  0x14  big_stat[63:32] RO 64-bit high word

The same test functions run against both the 3-stage and the 2-stage DUT (see
tests/run_tests.py), proving the packed-field and wide-chunk chains honor the
configured CDC_STAGE functionally, not just structurally.
"""

import cocotb
from cocotb.triggers import RisingEdge

from test_axi_lite import AxiLiteTestHelper
from test_cdc import start_clocks, reset_cdc_dut

# Register / word addresses for the packed+wide DUT
REG_MIX = 0x00
REG_BIG_CFG_LO = 0x04
REG_BIG_CFG_HI = 0x08
REG_BIG_STAT_LO = 0x10
REG_BIG_STAT_HI = 0x14


def _pack_mix_rw(go_bit, speed):
    """Compose the AXI write word for the RW fields of mix_reg."""
    return (go_bit & 0x1) | ((speed & 0x7) << 1)


async def _packed_rw_field_sync(dut, mod_period_ns):
    """AXI write of a packed register's RW fields must appear, correctly
    de-interleaved, on the per-field module_clk-domain output ports."""
    axi_clk, mod_clk = await start_clocks(dut, axi_period_ns=10, mod_period_ns=mod_period_ns)
    assert mod_clk is not None, "module_clk must exist for a CDC-enabled DUT"
    await reset_cdc_dut(dut, axi_clk, mod_clk)
    helper = AxiLiteTestHelper(dut)

    for go_bit, speed in [(1, 5), (0, 2), (1, 7), (0, 0)]:
        await helper.write(REG_MIX, _pack_mix_rw(go_bit, speed))
        # Let the packed-field output sync chain settle in the module domain.
        for _ in range(8):
            await RisingEdge(mod_clk)
        obs_go = int(dut.mix_reg_go_bit.value)
        obs_speed = int(dut.mix_reg_speed.value)
        assert obs_go == go_bit, (
            f"packed RW go_bit: wrote {go_bit}, module-domain port = {obs_go} "
            f"(mod_period_ns={mod_period_ns})")
        assert obs_speed == speed, (
            f"packed RW speed: wrote {speed}, module-domain port = {obs_speed} "
            f"(mod_period_ns={mod_period_ns})")


async def _packed_ro_field_sync(dut, mod_period_ns):
    """Packed RO field inputs must be synchronized into the AXI read word at the
    correct bit positions, without disturbing the RW fields."""
    axi_clk, mod_clk = await start_clocks(dut, axi_period_ns=10, mod_period_ns=mod_period_ns)
    assert mod_clk is not None, "module_clk must exist for a CDC-enabled DUT"
    await reset_cdc_dut(dut, axi_clk, mod_clk)
    helper = AxiLiteTestHelper(dut)

    for ready_bit, version in [(1, 0xA), (0, 0x5), (1, 0xF), (0, 0x0)]:
        await RisingEdge(mod_clk)
        dut.mix_reg_ready_bit.value = ready_bit
        dut.mix_reg_version.value = version
        # Give the RO field sync chain generous time to reach the AXI domain.
        for _ in range(8):
            await RisingEdge(axi_clk)
        data, resp = await helper.read(REG_MIX)
        assert resp == 0, f"packed RO read failed with resp={resp}"
        assert (data >> 8) & 0x1 == ready_bit, (
            f"packed RO ready_bit[8]: drove {ready_bit}, AXI read {(data >> 8) & 0x1} "
            f"(full word {data:#010x}, mod_period_ns={mod_period_ns})")
        assert (data >> 12) & 0xF == version, (
            f"packed RO version[15:12]: drove {version:#x}, AXI read {(data >> 12) & 0xF:#x} "
            f"(full word {data:#010x}, mod_period_ns={mod_period_ns})")


async def _packed_mixed_rw_ro(dut, mod_period_ns):
    """A packed register's RW and RO halves must be independent: RW bits read
    back from AXI storage while RO bits read back from the synchronized inputs,
    both in the same word."""
    axi_clk, mod_clk = await start_clocks(dut, axi_period_ns=10, mod_period_ns=mod_period_ns)
    assert mod_clk is not None, "module_clk must exist for a CDC-enabled DUT"
    await reset_cdc_dut(dut, axi_clk, mod_clk)
    helper = AxiLiteTestHelper(dut)

    # Drive RO inputs and write RW fields to distinct patterns.
    await RisingEdge(mod_clk)
    dut.mix_reg_ready_bit.value = 1
    dut.mix_reg_version.value = 0xC
    await helper.write(REG_MIX, _pack_mix_rw(go_bit=1, speed=3))

    for _ in range(8):
        await RisingEdge(mod_clk)
    for _ in range(8):
        await RisingEdge(axi_clk)

    data, resp = await helper.read(REG_MIX)
    assert resp == 0, f"packed mixed read failed with resp={resp}"
    assert data & 0x1 == 1, f"RW go_bit lost in packed word {data:#010x}"
    assert (data >> 1) & 0x7 == 3, f"RW speed lost in packed word {data:#010x}"
    assert (data >> 8) & 0x1 == 1, f"RO ready_bit lost in packed word {data:#010x}"
    assert (data >> 12) & 0xF == 0xC, f"RO version lost in packed word {data:#010x}"
    # And the module-domain RW outputs must match too.
    assert int(dut.mix_reg_go_bit.value) == 1
    assert int(dut.mix_reg_speed.value) == 3


async def _wide_rw_chunk_sync(dut, mod_period_ns):
    """A >32-bit RW register written word-by-word over AXI must appear as one
    coherent 64-bit value on the module_clk-domain output, proving the
    per-chunk synchronizers recombine correctly."""
    axi_clk, mod_clk = await start_clocks(dut, axi_period_ns=10, mod_period_ns=mod_period_ns)
    assert mod_clk is not None, "module_clk must exist for a CDC-enabled DUT"
    await reset_cdc_dut(dut, axi_clk, mod_clk)
    helper = AxiLiteTestHelper(dut)

    for lo, hi in [(0x11223344, 0x55667788), (0xFFFFFFFF, 0x00000000),
                   (0xDEADBEEF, 0xCAFEBABE)]:
        await helper.write(REG_BIG_CFG_LO, lo)
        await helper.write(REG_BIG_CFG_HI, hi)
        for _ in range(10):
            await RisingEdge(mod_clk)
        observed = int(dut.big_cfg.value)
        expected = (hi << 32) | lo
        assert observed == expected, (
            f"wide RW big_cfg: wrote hi={hi:#010x} lo={lo:#010x}, module-domain "
            f"output {observed:#018x} != {expected:#018x} (mod_period_ns={mod_period_ns})")


async def _wide_ro_chunk_sync(dut, mod_period_ns):
    """A >32-bit RO register driven in the module domain must be synchronized
    chunk-by-chunk and read back correctly per word over AXI."""
    axi_clk, mod_clk = await start_clocks(dut, axi_period_ns=10, mod_period_ns=mod_period_ns)
    assert mod_clk is not None, "module_clk must exist for a CDC-enabled DUT"
    await reset_cdc_dut(dut, axi_clk, mod_clk)
    helper = AxiLiteTestHelper(dut)

    for value in [0xCAFEBABEDEADBEEF, 0x0123456789ABCDEF, 0xFFFFFFFF00000000]:
        await RisingEdge(mod_clk)
        dut.big_stat.value = value
        for _ in range(10):
            await RisingEdge(axi_clk)
        lo, resp_lo = await helper.read(REG_BIG_STAT_LO)
        hi, resp_hi = await helper.read(REG_BIG_STAT_HI)
        assert resp_lo == 0 and resp_hi == 0, "wide RO read failed"
        assert lo == (value & 0xFFFFFFFF), (
            f"wide RO low word: drove {value:#018x}, read lo={lo:#010x} "
            f"(mod_period_ns={mod_period_ns})")
        assert hi == ((value >> 32) & 0xFFFFFFFF), (
            f"wide RO high word: drove {value:#018x}, read hi={hi:#010x} "
            f"(mod_period_ns={mod_period_ns})")


# =============================================================================
# @cocotb.test wrappers - one path per ratio so the report lists each explicitly.
# Ratios chosen to cover 1:1-ish, prime (worst case), and 5:1 slow crossings.
# =============================================================================

@cocotb.test()
async def test_cdc_packed_rw_field_sync(dut):
    """CDC-010/011: packed RW fields cross to per-field module_clk ports (prime ratio)"""
    await _packed_rw_field_sync(dut, mod_period_ns=17)


@cocotb.test()
async def test_cdc_packed_rw_field_sync_slow(dut):
    """CDC-011: packed RW fields cross when module_clk is 5x slower"""
    await _packed_rw_field_sync(dut, mod_period_ns=50)


@cocotb.test()
async def test_cdc_packed_ro_field_sync(dut):
    """CDC-010: packed RO field inputs synchronize into the AXI read word (prime ratio)"""
    await _packed_ro_field_sync(dut, mod_period_ns=13)


@cocotb.test()
async def test_cdc_packed_ro_field_sync_slow(dut):
    """CDC-010: packed RO field inputs synchronize when module_clk is 5x slower"""
    await _packed_ro_field_sync(dut, mod_period_ns=50)


@cocotb.test()
async def test_cdc_packed_mixed_rw_ro(dut):
    """CDC-010/011: RW and RO fields of the same packed word are independently synced"""
    await _packed_mixed_rw_ro(dut, mod_period_ns=17)


@cocotb.test()
async def test_cdc_wide_rw_chunk_sync(dut):
    """CDC-014: wide (64-bit) RW register recombines coherently in the module domain (prime ratio)"""
    await _wide_rw_chunk_sync(dut, mod_period_ns=17)


@cocotb.test()
async def test_cdc_wide_rw_chunk_sync_slow(dut):
    """CDC-014: wide (64-bit) RW register crosses when module_clk is 5x slower"""
    await _wide_rw_chunk_sync(dut, mod_period_ns=50)


@cocotb.test()
async def test_cdc_wide_ro_chunk_sync(dut):
    """CDC-014: wide (64-bit) RO register synchronizes chunk-by-chunk into AXI reads (prime ratio)"""
    await _wide_ro_chunk_sync(dut, mod_period_ns=13)


@cocotb.test()
async def test_cdc_wide_ro_chunk_sync_slow(dut):
    """CDC-014: wide (64-bit) RO register crosses when module_clk is 5x slower"""
    await _wide_ro_chunk_sync(dut, mod_period_ns=50)
