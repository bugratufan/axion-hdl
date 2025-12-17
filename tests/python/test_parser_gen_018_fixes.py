import pytest
import os
from axion_hdl.parser import VHDLParser

def test_parser_multiple_definitions():
    """Verify parser captures base_address from secondary @axion_def line."""
    content = """
    library ieee;
    entity test_multi_def is end;
    architecture rtl of test_multi_def is
        -- @axion_def cdc_enabled=false
        -- @axion_def base_address=0x1000
        
        signal reg_auto : std_logic_vector(31 downto 0); -- @axion access=RW
    begin
    end;
    """
    
    # Mocking file read by patching or just manually calling internal method if possible
    # But _parse_vhdl_file reads from disk.
    # Let's write a temp file.
    test_path = "/tmp/test_multi_def.vhd"
    with open(test_path, 'w') as f:
        f.write(content)
        
    parser = VHDLParser()
    data = parser.parse_file(test_path)
    
    assert data is not None
    assert data['base_addr'] == 0x1000, "Failed to parse base_address from second line"
    
    os.remove(test_path)

def test_parser_absolute_address_handling():
    """Verify parser converts absolute manual address to relative offset if >= base."""
    content = """
    library ieee;
    entity test_abs_addr is end;
    architecture rtl of test_abs_addr is
        -- @axion_def base_address=0x1000
        
        -- Absolute address 0x1004 should become offset 4
        signal reg_abs : std_logic_vector(31 downto 0); -- @axion address=0x1004 access=RO
        
        -- Relative address 0x8 should stay 0x8
        signal reg_rel : std_logic_vector(31 downto 0); -- @axion address=0x8 access=RO
    begin
    end;
    """
    
    test_path = "/tmp/test_abs_addr.vhd"
    with open(test_path, 'w') as f:
        f.write(content)
        
    parser = VHDLParser()
    data = parser._parse_vhdl_file(test_path) # Use internal to check details
    
    assert data is not None
    assert data['base_address'] == 0x1000
    
    regs = {r['signal_name']: r for r in data['registers']}
    
    # Check Reg Abs
    reg_abs = regs['reg_abs']
    assert reg_abs['address_int'] == 0x1004, "Absolute address should be preserved"
    assert reg_abs['relative_address_int'] == 4, "Relative address should be calculated as Offset (0x1004 - 0x1000)"
    
    # Check Reg Rel
    reg_rel = regs['reg_rel']
    assert reg_rel['address_int'] == 0x1008, "Absolute address should be base + offset (0x1000 + 0x8)"
    assert reg_rel['relative_address_int'] == 8, "Relative address should be preserved as 8"

    os.remove(test_path)

if __name__ == "__main__":
    test_parser_multiple_definitions()
    test_parser_absolute_address_handling()
