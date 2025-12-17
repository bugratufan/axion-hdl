import pytest
import os
from axion_hdl.parser import VHDLParser
from axion_hdl.address_manager import AddressConflictError

def test_address_conflict_error_message():
    """Verify AddressConflictError string representation is clean."""
    err = AddressConflictError(0x1000, "reg_a", "reg_b", "mod_x")
    msg = str(err)
    
    assert "Address Conflict" in msg
    assert "0x1000" in msg
    assert "reg_a" in msg
    assert "reg_b" in msg
    # Assert ASCII art is NOT in the default string
    assert "╔" not in msg
    assert "VIOLATED REQUIREMENTS" not in msg
    
    # Assert formatted message is available
    assert "╔" in err.formatted_message

def test_parser_partial_loading_on_conflict():
    """Verify parser returns module with errors on conflict."""
    content = """
    library ieee;
    entity conflict_test is end;
    architecture rtl of conflict_test is
        -- @axion_def cdc_enabled=false
        
        signal reg_a : std_logic_vector(31 downto 0); -- @axion address=0x0 access=RW
        signal reg_b : std_logic_vector(31 downto 0); -- @axion address=0x0 access=RW
    begin
    end;
    """
    
    test_path = "/tmp/conflict_test.vhd"
    with open(test_path, 'w') as f:
        f.write(content)
        
    parser = VHDLParser()
    # Use internal parse to check dict directly
    data = parser._parse_vhdl_file(test_path)
    
    assert data is not None, "Parser should return data even with conflicts"
    assert data['name'] == 'conflict_test'
    
    # Check registers
    regs = {r['signal_name']: r for r in data['registers']}
    assert 'reg_a' in regs
    assert 'reg_b' in regs
    
    # Check errors
    assert 'parsing_errors' in data
    errors = data['parsing_errors']
    assert len(errors) > 0
    
    conflict_err = next((e for e in errors if "Address Conflict" in e['msg']), None)
    assert conflict_err is not None
    assert "Address 0x0000" in conflict_err['msg']
    
    os.remove(test_path)

if __name__ == "__main__":
    test_address_conflict_error_message()
    test_parser_partial_loading_on_conflict()
