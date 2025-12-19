import pytest
import os
from axion_hdl.generator import VHDLGenerator

def test_gen_018_base_addr_generic():
    """Verify GEN-018: VHDL uses BASE_ADDR generic with correct relative offsets."""
    
    base_addr = 0x12340000
    
    module_data = {
        'name': 'test_generic_mod',
        'file': 'test.json',
        'base_address': base_addr,
        'cdc_enabled': False,
        'cdc_stages': 2,
        'registers': [
            {
                'reg_name': 'ctrl',
                'description': 'Control Register (Offset 0x0)',
                'address': '0x12340000',
                'address_int': base_addr + 0,
                'relative_address_int': 0,
                'width': 32,
                'access_mode': 'RW', 
                'default_value': 0,
                'signal_type': '[31:0]',
                'signal_name': 'ctrl',
                'read_strobe': False,
                'write_strobe': False
            },
            {
                'reg_name': 'status',
                'description': 'Status Register (Offset 0x4)',
                'address': '0x12340004',
                'address_int': base_addr + 4,
                'relative_address_int': 4,
                'width': 32,
                'access_mode': 'RO',
                'default_value': 0,
                'signal_type': '[31:0]',
                'signal_name': 'status',
                'read_strobe': True,
                'write_strobe': False
            },
            {
                'reg_name': 'data',
                'description': 'Data Register (Offset 0x100)',
                'address': '0x12340100',
                'address_int': base_addr + 0x100,
                'relative_address_int': 0x100,
                'width': 32,
                'access_mode': 'RW',
                'default_value': 0,
                'signal_type': '[31:0]',
                'signal_name': 'data',
                'read_strobe': True,
                'write_strobe': True
            }
        ],
        'packed_registers': []
    }
    
    generator = VHDLGenerator(output_dir="/tmp")
    vhdl_code = generator._generate_vhdl_code(module_data)
    
    # 1. Check for Generic Definition
    assert "generic (" in vhdl_code
    assert 'BASE_ADDR : std_logic_vector(31 downto 0) := x"12340000"' in vhdl_code
    
    # 2. Check for Address Decoding (should use relative offset)
    # Reg 0 (Offset 0): BASE_ADDR + 0
    assert "if unsigned(axi_awaddr) = unsigned(BASE_ADDR) + 0 then" in vhdl_code
    
    # Reg 1 (Offset 4): BASE_ADDR + 4
    assert "if unsigned(axi_araddr) = unsigned(BASE_ADDR) + 4 then" in vhdl_code
    
    # Reg 2 (Offset 0x100 = 256): BASE_ADDR + 256
    assert "if unsigned(axi_awaddr) = unsigned(BASE_ADDR) + 256 then" in vhdl_code
    
    # 3. Check for Strobe Logic (Concurrent)
    # Should correspond to relative offsets
    # Status (Offset 4)
    assert "status_rd_strobe <= '1' when (axi_state = RD_DATA and axi_rready = '1' and unsigned(rd_addr_reg) = unsigned(BASE_ADDR) + 4) else '0';" in vhdl_code
    
    # Data (Offset 256)
    assert "data_wr_strobe <= '1' when (axi_state = WR_DO_WRITE and unsigned(wr_addr_reg) = unsigned(BASE_ADDR) + 256) else '0';" in vhdl_code

if __name__ == "__main__":
    test_gen_018_base_addr_generic()
