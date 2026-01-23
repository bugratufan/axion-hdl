"""
Cocotb Extended Stress Tests for Axion-HDL

Verifies robustness under:
- High transaction volume
- Interleaved Read/Write operations
- Random resets under load
- Invalid address access storms
- Address map walking speed
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer, ClockCycles, Combine, Join
import random

# Reuse constants
REG_STATUS = 0x00
REG_CONFIG = 0x20
REG_MODE   = 0x28

class AxiLiteTestHelper:
    def __init__(self, dut):
        self.dut = dut
        self.clk = dut.axi_aclk

    async def write(self, addr, data, check_response=True):
        dut = self.dut
        await RisingEdge(self.clk)
        dut.axi_awaddr.value = addr
        dut.axi_awvalid.value = 1
        dut.axi_wdata.value = data
        dut.axi_wstrb.value = 0xF
        dut.axi_wvalid.value = 1
        dut.axi_bready.value = 1
        
        aw_done = False
        w_done = False
        
        # Timeout loop for write address/data handshake
        for _ in range(500):
            await RisingEdge(self.clk)
            if dut.axi_awready.value == 1:
                aw_done = True
                dut.axi_awvalid.value = 0
            if dut.axi_wready.value == 1:
                w_done = True
                dut.axi_wvalid.value = 0
            
            if aw_done and w_done:
                break
                
        if not (aw_done and w_done):
            raise TimeoutError("Write handshake timeout")
            
        # Timeout loop for write response
        resp_done = False
        for _ in range(500):
            if dut.axi_bvalid.value == 1:
                resp_done = True
                break
            await RisingEdge(self.clk)
            
        if not resp_done:
            raise TimeoutError("Write response timeout")
            
        resp = int(dut.axi_bresp.value)
        await RisingEdge(self.clk)
        dut.axi_bready.value = 0
        return resp

    async def read(self, addr):
        dut = self.dut
        await RisingEdge(self.clk)
        dut.axi_araddr.value = addr
        dut.axi_arvalid.value = 1
        dut.axi_rready.value = 1
        
        ar_done = False
        for _ in range(500):
            if dut.axi_arready.value == 1:
                ar_done = True
                break
            await RisingEdge(self.clk)
        
        if not ar_done:
             raise TimeoutError("Read address handshake timeout")
             
        dut.axi_arvalid.value = 0
        
        r_done = False
        for _ in range(500):
            if dut.axi_rvalid.value == 1:
                r_done = True
                break
            await RisingEdge(self.clk)
            
        if not r_done:
            raise TimeoutError("Read data timeout")
            
        try:
            data = int(dut.axi_rdata.value)
        except ValueError:
            data = 0 # Handle X/U values gracefully
            
        resp = int(dut.axi_rresp.value)
        await RisingEdge(self.clk)
        dut.axi_rready.value = 0
        return data, resp

async def setup_dut(dut):
    clk = dut.axi_aclk
    cocotb.start_soon(Clock(clk, 10, units="ns").start())
    if hasattr(dut, 'module_clk'):
        cocotb.start_soon(Clock(dut.module_clk, 17, units="ns").start())
    
    dut.axi_aresetn.value = 0
    await ClockCycles(clk, 10)
    dut.axi_aresetn.value = 1
    await ClockCycles(clk, 5)
    return clk

@cocotb.test()
async def test_stress_001_interleaved_rw(dut):
    """STRESS-001: 500 interleaved Read/Write transactions"""
    clk = await setup_dut(dut)
    helper = AxiLiteTestHelper(dut)
    
    # Use RW registers for target
    targets = [REG_CONFIG, REG_MODE]
    
    dut._log.info("Starting 500 interleaved transactions...")
    
    # Seed for reproducibility
    random.seed(12345)
    
    previous_writes = {addr: 0 for addr in targets}
    
    for i in range(500):
        is_write = random.choice([True, False])
        addr = random.choice(targets)
        
        if is_write:
            val = random.randint(0, 0xFFFFFFFF)
            await helper.write(addr, val)
            previous_writes[addr] = val
        else:
            # Read
            data, resp = await helper.read(addr)
            assert resp == 0, f"Read error at iter {i}"
            # Verify data matches last write
            expected = previous_writes[addr]
            assert data == expected, f"Data mismatch at iter {i}: wrote {expected:X}, read {data:X}"
            
        if i % 100 == 0:
            dut._log.info(f"Completed {i} transactions")
            
    dut._log.info("STRESS-001 PASSED: 500 transactions successful")

@cocotb.test()
async def test_stress_002_reset_under_load(dut):
    """STRESS-002: Assert reset randomly during traffic"""
    clk = await setup_dut(dut)
    helper = AxiLiteTestHelper(dut)
    
    # Start a background task that toggles reset
    async def toggle_reset():
        await ClockCycles(clk, 50) # Wait a bit
        dut._log.info("Asserting RESET under load!")
        dut.axi_aresetn.value = 0
        await ClockCycles(clk, 20)
        dut.axi_aresetn.value = 1
        dut._log.info("Released RESET")

    cocotb.start_soon(toggle_reset())
    
    # Try to perform transactions while reset hits
    try:
        for i in range(200):
            # We expect some of these to fail or hang when reset hits
            # But the simulation shouldn't crash
            try:
                # Use a short timeout version if possible, or just raw calls
                # Here we just use helper
                await helper.write(REG_CONFIG, i)
            except Exception:
                # Ignore transaction failures during reset
                pass
            await ClockCycles(clk, 1)
            
    except Exception as e:
        dut._log.info(f"Caught expected exception during reset: {e}")

    # Recovery Check
    # Wait for reset to definitely be released
    await ClockCycles(clk, 50)
    
    # Verify we can talk to the DUT again
    dut._log.info("Verifying recovery after reset...")
    resp = await helper.write(REG_CONFIG, 0xDEADBEEF)
    assert resp == 0, "Failed to write after reset recovery"
    
    val, _ = await helper.read(REG_CONFIG)
    assert val == 0xDEADBEEF, "Failed to read verify after reset recovery"
    
    dut._log.info("STRESS-002 PASSED: System recovered after reset under load")

@cocotb.test()
async def test_stress_003_address_map_walk(dut):
    """STRESS-003: Walk the entire address map rapidly"""
    clk = await setup_dut(dut)
    helper = AxiLiteTestHelper(dut)
    
    # Valid addresses from sensor_controller (0x00 to 0x34)
    # Stride 4
    addresses = range(0x00, 0x38, 4)
    
    dut._log.info("Walking address map...")
    
    for addr in addresses:
        # Just read everything. 
        # RO regs return value, WO return error/0, RW return value
        # We just want to ensure no lockups and valid bus behavior
        data, resp = await helper.read(addr)
        
        # Check that response is valid (0=OKAY, 2=SLVERR)
        assert resp in [0, 2], f"Invalid AXI response {resp} at {addr:X}"
        
    dut._log.info("STRESS-003 PASSED: Address map walk completed")

@cocotb.test()
async def test_stress_004_invalid_access_storm(dut):
    """STRESS-004: Storm of invalid address accesses"""
    clk = await setup_dut(dut)
    helper = AxiLiteTestHelper(dut)
    
    dut._log.info("Starting invalid access storm...")
    
    # Addresses likely to be invalid (gaps or out of range)
    invalid_addrs = [0x1000, 0x2000, 0x3005, 0xFFFFFFFC, 0x12]
    
    for _ in range(50):
        addr = random.choice(invalid_addrs)
        data, resp = await helper.read(addr)
        
        # Should return error (SLVERR=2 or DECERR=3)
        assert resp != 0, f"Expected error for invalid addr {addr:X}, got OKAY"
        
    dut._log.info("STRESS-004 PASSED: Invalid access storm handled correctly")
