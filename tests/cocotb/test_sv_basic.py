"""
Cocotb Benchmark for SystemVerilog Generated Modules
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer, ClockCycles

class AxiLiteTestHelper:
    """Helper class for AXI-Lite testing"""

    def __init__(self, dut, clk_name="axi_aclk", rst_name="axi_aresetn"):
        self.dut = dut
        self.clk = getattr(dut, clk_name)
        self.rst = getattr(dut, rst_name)

    async def write(self, addr, data, strb=0xF):
        """Perform AXI-Lite write transaction"""
        dut = self.dut

        # Start write transaction
        await RisingEdge(self.clk)
        dut.axi_awaddr.value = addr
        dut.axi_awvalid.value = 1
        dut.axi_wdata.value = data
        dut.axi_wstrb.value = strb
        dut.axi_wvalid.value = 1
        dut.axi_bready.value = 1

        # Wait for address ready
        while True:
            await RisingEdge(self.clk)
            if dut.axi_awready.value == 1:
                break
        dut.axi_awvalid.value = 0

        # Wait for write ready
        while dut.axi_wready.value != 1:
            await RisingEdge(self.clk)
        dut.axi_wvalid.value = 0

        # Wait for response
        while dut.axi_bvalid.value != 1:
            await RisingEdge(self.clk)

        resp = int(dut.axi_bresp.value)
        await RisingEdge(self.clk)
        dut.axi_bready.value = 0

        return resp

    async def read(self, addr):
        """Perform AXI-Lite read transaction"""
        dut = self.dut

        # Start read transaction
        await RisingEdge(self.clk)
        dut.axi_araddr.value = addr
        dut.axi_arvalid.value = 1
        dut.axi_rready.value = 1

        # Wait for address ready
        while True:
            await RisingEdge(self.clk)
            if dut.axi_arready.value == 1:
                break
        dut.axi_arvalid.value = 0

        # Wait for data valid
        while dut.axi_rvalid.value != 1:
            await RisingEdge(self.clk)

        data = int(dut.axi_rdata.value)
        resp = int(dut.axi_rresp.value)
        await RisingEdge(self.clk)
        dut.axi_rready.value = 0

        return data, resp

async def reset_dut(dut, clk):
    dut.axi_aresetn.value = 0
    await ClockCycles(clk, 10)
    dut.axi_aresetn.value = 1
    await ClockCycles(clk, 5)

@cocotb.test()
async def test_sv_basic_access(dut):
    """Test Basic Read/Write Access to SystemVerilog Module"""
    clk = dut.axi_aclk
    cocotb.start_soon(Clock(clk, 10, units="ns").start())
    
    await reset_dut(dut, clk)
    helper = AxiLiteTestHelper(dut)

    # Note: Address map depends on the DUT generated. 
    # Assuming standard sensor_controller map or similar if used.
    # For generic verification, we assume 0x00 is a valid register or we handle errors.
    
    dut._log.info("Starting SV Basic Access Test")
    
    # Try writing to 0x20 (Config Reg in many examples)
    # If it's a generated test module, we might need to know the map.
    # But basic connectivity check:
    
    # Write
    val = 0xDEADBEEF
    await helper.write(0x20, val)
    
    # Read back (if RW)
    data, resp = await helper.read(0x20)

    dut._log.info(f"Read Match: {data == val} (Got 0x{data:X})")
    assert resp == 0, f"Expected OKAY response (0), got {resp}"
    assert data == val, f"Read-back mismatch: wrote 0x{val:X}, got 0x{data:X}"
