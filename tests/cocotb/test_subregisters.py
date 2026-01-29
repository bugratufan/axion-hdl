"""
Cocotb Subregister (Bit-Field) Tests for Axion-HDL

Verifies:
- Bit-level access to registers
- Correct packing/unpacking of fields
- Read-Modify-Write operations behavior
- Field isolation

Register Map for sensor_controller_axion_reg used in tests:
  0x00 (0)   status_reg          RO  [0: data_valid, 1: error_flag, 2: fan, 3: heater, 4: alarm]
  0x14 (20)  control_reg         WO  [0: fan, 1: heater, 2: alarm]
  0x28 (40)  mode_reg            RW  (General purpose for RMW tests)
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer, ClockCycles

# Helper class for AXI transactions
class AxiLiteTestHelper:
    def __init__(self, dut, clk_name="axi_aclk", rst_name="axi_aresetn"):
        self.dut = dut
        self.clk = getattr(dut, clk_name)
        self.rst = getattr(dut, rst_name)

    async def write(self, addr, data, strb=0xF):
        self.dut.axi_awaddr.value = addr
        self.dut.axi_awvalid.value = 1
        self.dut.axi_wdata.value = data
        self.dut.axi_wstrb.value = strb
        self.dut.axi_wvalid.value = 1
        self.dut.axi_bready.value = 1

        aw_done = False
        w_done = False
        while not (aw_done and w_done):
            await RisingEdge(self.clk)
            if self.dut.axi_awready.value == 1:
                aw_done = True
                self.dut.axi_awvalid.value = 0
            if self.dut.axi_wready.value == 1:
                w_done = True
                self.dut.axi_wvalid.value = 0
                
        while self.dut.axi_bvalid.value != 1:
            await RisingEdge(self.clk)
            
        resp = int(self.dut.axi_bresp.value)
        await RisingEdge(self.clk)
        self.dut.axi_bready.value = 0
        return resp

    async def read(self, addr):
        self.dut.axi_araddr.value = addr
        self.dut.axi_arvalid.value = 1
        self.dut.axi_rready.value = 1
        
        while self.dut.axi_arready.value != 1:
            await RisingEdge(self.clk)
        self.dut.axi_arvalid.value = 0
        
        while self.dut.axi_rvalid.value != 1:
            await RisingEdge(self.clk)
            
        data = int(self.dut.axi_rdata.value)
        resp = int(self.dut.axi_rresp.value)
        await RisingEdge(self.clk)
        self.dut.axi_rready.value = 0
        return data, resp

async def setup_dut(dut):
    """Initialize clocks and reset"""
    clk = dut.axi_aclk
    
    # 1. Start Clocks BEFORE reset
    cocotb.start_soon(Clock(clk, 10, units="ns").start())
    
    # Force start module_clk - critical for CDC
    mod_clk = getattr(dut, 'module_clk', None)
    if mod_clk is not None:
        cocotb.start_soon(Clock(mod_clk, 17, units="ns").start())
    else:
        dut._log.warning("module_clk not found on DUT, CDC logic may fail if enabled")

    # 2. Hold Reset
    dut.axi_aresetn.value = 0
    # Wait detailed amount of time to ensure 'U' values propagate out
    await Timer(100, units="ns") 
    
    # 3. Release Reset
    dut.axi_aresetn.value = 1
    # Wait for reset release to sync
    await Timer(100, units="ns")
    
    return clk

# Register Addresses
REG_STATUS  = 0x00
REG_CONTROL = 0x14
REG_MODE    = 0x28

async def wait_for_signal_value(signal, expected_mask, expected_value, timeout_ns=1000):
    """Wait for signal to match expected value within timeout"""
    for _ in range(int(timeout_ns / 10)): # Poll every 10ns
        val = signal.value
        try:
            if (val.integer & expected_mask) == expected_value:
                return True
        except ValueError:
            pass # Handle 'X' or 'U' values
        await Timer(10, units="ns")
    return False

@cocotb.test()
async def test_subreg_001_single_bit_control(dut):
    """SUB-001: Verify individual bits in control_reg affect specific outputs"""
    clk = await setup_dut(dut)
    helper = AxiLiteTestHelper(dut)
    
    # 0. Check if module_clk is actually running
    mod_clk = getattr(dut, 'module_clk', None)
    if mod_clk is not None:
        initial_val = mod_clk.value
        await Timer(100, units="ns")
        final_val = mod_clk.value
        # If it was 0 and stayed 0, or 1 and stayed 1 (though Clock usually toggles)
        # Note: Clock runs at 17ns period. 100ns is enough for multiple edges.
        # But simply capturing value twice is not enough guarantee (aliasing).
        # Better: Wait for edge.
        try:
            await RisingEdge(mod_clk)
            dut._log.info("module_clk is toggling OK")
        except Exception:
            assert False, "module_clk is NOT toggling! CDC logic cannot work."
            
    # Default state check
    # Poll until reset propagation completes (signal becomes 0 instead of U)
    reset_ok = await wait_for_signal_value(dut.control_reg, 0xFFFFFFFF, 0, 500)
    assert reset_ok, f"Control reg output did not reset to 0, current: {dut.control_reg.value}"
    
    # 1. Enable Fan (Bit 0)
    # Write 0x00000001
    await helper.write(REG_CONTROL, 0x01)
    
    # Wait for CDC propagation (polling instead of fixed wait)
    success = await wait_for_signal_value(dut.control_reg, 0x01, 0x01)
    assert success, f"Bit 0 did not assert. Got: {dut.control_reg.value}"
    val = dut.control_reg.value.integer
    assert (val & 0x02) == 0, f"Bit 1 should be 0, got 0x{val:08X}"
    
    # 2. Enable Heater (Bit 1), Disable Fan
    # Write 0x00000002
    await helper.write(REG_CONTROL, 0x02)
    
    success = await wait_for_signal_value(dut.control_reg, 0x03, 0x02)
    assert success, f"Bit 1 did not assert or Bit 0 did not clear. Got: {dut.control_reg.value}"
    
    # 3. Enable Both + Alarm (Bit 2)
    # Write 0x00000007 (111 binary)
    await helper.write(REG_CONTROL, 0x07)
    
    success = await wait_for_signal_value(dut.control_reg, 0x07, 0x07)
    assert success, f"Bits 0,1,2 did not assert. Got: {dut.control_reg.value}"
    
    dut._log.info("SUB-001 PASSED: Individual control bits verified via DUT outputs")

@cocotb.test()
async def test_subreg_002_status_capture(dut):
    """SUB-002: Verify status_reg correctly captures input flags"""
    clk = await setup_dut(dut)
    helper = AxiLiteTestHelper(dut)
    
    # Input stimulus: data_valid=1 (bit 0), error_flag=0 (bit 1)
    dut.status_reg.value = 0x00000001
    
    # Wait for CDC (status_reg inputs are synchronized)
    # Since we can't probe internal signals easily, we rely on readback
    # Retry loop for readback to account for CDC delay
    
    matched = False
    for i in range(20): # Try for ~2000ns
        data, _ = await helper.read(REG_STATUS)
        if (data & 0x03) == 0x01:
            matched = True
            break
        await Timer(100, units="ns")
        
    assert matched, f"Bit 0 should be 1, Bit 1 should be 0. Got {data:08X}"
    
    # Change inputs: data_valid=0, error_flag=1 (bit 1)
    dut.status_reg.value = 0x00000002
    
    matched = False
    for i in range(20):
        data, _ = await helper.read(REG_STATUS)
        if (data & 0x03) == 0x02:
            matched = True
            break
        await Timer(100, units="ns")
        
    assert matched, f"Bit 0 should be 0, Bit 1 should be 1. Got {data:08X}"
    
    dut._log.info("SUB-002 PASSED: Input flags correctly mapped to status bits")

@cocotb.test()
async def test_subreg_003_read_modify_write(dut):
    """SUB-003: Simulated Read-Modify-Write operation on RW register"""
    clk = await setup_dut(dut)
    helper = AxiLiteTestHelper(dut)
    
    addr = REG_MODE
    
    # Initial state: Write 0x000000F0
    await helper.write(addr, 0xF0)
    
    # Scenario: User wants to set Bit 0 to '1' without changing others
    # 1. Read
    current_val, _ = await helper.read(addr)
    assert current_val == 0xF0
    
    # 2. Modify (Set bit 0)
    new_val = current_val | 0x01
    
    # 3. Write
    await helper.write(addr, new_val)
    
    # Verify: Should be 0xF1
    final_val, _ = await helper.read(addr)
    assert final_val == 0xF1, f"Expected 0xF1, got 0x{final_val:X}"
    
    # Scenario: Clear Bit 4 (0x10) without changing others
    # 1. Read
    current_val, _ = await helper.read(addr)
    
    # 2. Modify (Clear bit 4)
    new_val = current_val & ~0x10
    
    # 3. Write
    await helper.write(addr, new_val)
    
    # Verify: Should be 0xE1 (0xF1 & ~0x10 = 11110001 & 11101111 = 11100001 = 0xE1)
    final_val, _ = await helper.read(addr)
    assert final_val == 0xE1, f"Expected 0xE1, got 0x{final_val:X}"
    
    dut._log.info("SUB-003 PASSED: Read-Modify-Write operations successful")

@cocotb.test()
async def test_subreg_004_field_isolation(dut):
    """SUB-004: Verify writing to one field doesn't corrupt others"""
    clk = await setup_dut(dut)
    helper = AxiLiteTestHelper(dut)
    
    # Using mode_reg (RW) for this test
    # Let's treat it as 4 byte-fields
    
    # Write distinctive pattern
    pattern = 0xAA_BB_CC_DD
    await helper.write(REG_MODE, pattern)
    
    # Overwrite only the bottom byte using byte strobes 
    # (Simulating single field update if it was byte-aligned)
    await helper.write(REG_MODE, 0x000000FF, strb=0x1)
    
    data, _ = await helper.read(REG_MODE)
    
    # Top 3 bytes should remain unchanged (AABBCC)
    # Bottom byte should be FF
    expected = 0xAA_BB_CC_FF
    
    assert data == expected, f"Field isolation failed. Expected {expected:08X}, got {data:08X}"
    
    dut._log.info("SUB-004 PASSED: Field isolation verified via byte strobes")
