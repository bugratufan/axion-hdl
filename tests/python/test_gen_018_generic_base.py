import pytest
import os
from axion_hdl.generator import VHDLGenerator

def test_gen_018_base_addr_generic():
    """Verify GEN-018: VHDL uses BASE_ADDR generic."""
    
    module_data = {
        'name': 'test_generic_mod',
        'file': 'test.json',
        'base_address': 0x12340000,
        'cdc_enabled': False,
        'cdc_stages': 2,
        'registers': [
            {
                'reg_name': 'ctrl',
                'description': 'Control Register',
                'address': '0x0',
                'address_int': 0,
                'width': 32,
                'access_mode': 'RW', # Changed from 'mod': 'RW' to 'access_mode'
                'default_value': 0,
                'signal_type': '[31:0]',
                'signal_name': 'ctrl',
                'read_strobe': False,
                'write_strobe': False
            },
            {
                'reg_name': 'status',
                'description': 'Status Register',
                'address': '0x4',
                'address_int': 4,
                'width': 32,
                'access_mode': 'RO',
                'default_value': 0,
                'signal_type': '[31:0]',
                'signal_name': 'status',
                'read_strobe': True,
                'write_strobe': False
            }
        ],
        'packed_registers': []
    }
    
    generator = VHDLGenerator(output_dir="/tmp")
    vhdl_code = generator._generate_vhdl_code(module_data)
    
    # 1. Check for Generic Definition
    assert "generic (" in vhdl_code
    assert 'BASE_ADDR : std_logic_vector(31 downto 0) := x"12340000"' in vhdl_code
    
    # 2. Check for Write Address Decoding using BASE_ADDR
    # Should look like: if unsigned(axi_awaddr) = unsigned(BASE_ADDR) + 0 then
    assert "if unsigned(axi_awaddr) = unsigned(BASE_ADDR) + 0 then" in vhdl_code
    
    # 3. Check for Read Address Decoding using BASE_ADDR
    # Should look like: if unsigned(axi_araddr) = unsigned(BASE_ADDR) + 4 then
    assert "if unsigned(axi_araddr) = unsigned(BASE_ADDR) + 4 then" in vhdl_code
    
    # 4. Check for Register Write Logic (Internal)
    # wr_addr_reg check
    assert "if unsigned(wr_addr_reg) = unsigned(BASE_ADDR) + 0 then" in vhdl_code

    # 5. Check for Strobe Logic (Concurrent)
    # status read strobe
    assert "status_rd_strobe <= '1' when (axi_state = RD_DATA and axi_rready = '1' and unsigned(rd_addr_reg) = unsigned(BASE_ADDR) + 4) else '0';" in vhdl_code

if __name__ == "__main__":
    test_gen_018_base_addr_generic()
