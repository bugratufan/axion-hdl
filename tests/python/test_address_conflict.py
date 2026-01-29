import pytest
import os
import shutil
import tempfile
from axion_hdl import AxionHDL

@pytest.fixture
def temp_test_env():
    """Create a temporary directory for testing."""
    tmp = tempfile.mkdtemp()
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)

def test_address_conflict_detection(temp_test_env):
    """
    Test that address conflicts are properly detected and reported in module errors.
    Uses conflict between reg_alpha and reg_beta at address 0x00.
    """
    # Create VHDL with intentional conflict
    conflict_vhdl = """
library ieee;
use ieee.std_logic_1164.all;

-- @axion_def BASE_ADDR=0x0000

entity conflict_test is
    port (clk : in std_logic);
end entity;

architecture rtl of conflict_test is
    signal reg_alpha : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
    signal reg_beta  : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x00
begin
end architecture;
"""
    vhdl_file = os.path.join(temp_test_env, "conflict.vhd")
    with open(vhdl_file, 'w') as f:
        f.write(conflict_vhdl)
    
    axion = AxionHDL(output_dir=os.path.join(temp_test_env, "out"))
    axion.add_src(temp_test_env)
    
    # Analyze - This tool design logs errors instead of raising exceptions
    # to allow all errors to be collected and displayed in the GUI.
    axion.analyze()
    
    # Check for conflict in analyzed modules
    assert len(axion.analyzed_modules) == 1
    module = axion.analyzed_modules[0]
    errors = module.get('parsing_errors', [])
    
    # Find the address conflict error
    conflict_error = next((err for err in errors if "Address Conflict" in err['msg']), None)
    assert conflict_error is not None, f"Address conflict should be in module errors. Got: {errors}"
    
    error_msg = conflict_error['msg']
    assert "0x0000" in error_msg or "0x00" in error_msg
    assert "reg_alpha" in error_msg
    assert "reg_beta" in error_msg

def test_no_conflict_when_addresses_differ(temp_test_env):
    """Test that no error is raised when addresses are unique."""
    valid_vhdl = """
library ieee;
use ieee.std_logic_1164.all;

-- @axion_def BASE_ADDR=0x0000

entity valid_module is
    port (clk : in std_logic);
end entity;

architecture rtl of valid_module is
    signal reg_a : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
    signal reg_b : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x04
begin
end architecture;
"""
    vhdl_file = os.path.join(temp_test_env, "valid.vhd")
    with open(vhdl_file, 'w') as f:
        f.write(valid_vhdl)
    
    axion = AxionHDL(output_dir=os.path.join(temp_test_env, "out"))
    axion.add_src(temp_test_env)
    
    axion.analyze()
    
    assert len(axion.analyzed_modules) == 1
    module = axion.analyzed_modules[0]
    errors = module.get('parsing_errors', [])
    assert len(errors) == 0, f"Unexpected errors: {errors}"

def test_wide_signal_address_overlap(temp_test_env):
    """Test overlap detection for wide signals."""
    overlap_vhdl = """
library ieee;
use ieee.std_logic_1164.all;

-- @axion_def BASE_ADDR=0x0000

entity wide_overlap_test is
    port (clk : in std_logic);
end entity;

architecture rtl of wide_overlap_test is
    signal wide_reg : std_logic_vector(63 downto 0); -- @axion RO ADDR=0x00
    signal conflict_reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x04
begin
end architecture;
"""
    vhdl_file = os.path.join(temp_test_env, "wide_overlap.vhd")
    with open(vhdl_file, 'w') as f:
        f.write(overlap_vhdl)
    
    axion = AxionHDL(output_dir=os.path.join(temp_test_env, "out"))
    axion.add_src(temp_test_env)
    
    axion.analyze()
    
    assert len(axion.analyzed_modules) == 1
    module = axion.analyzed_modules[0]
    errors = module.get('parsing_errors', [])
    
    conflict_error = next((err for err in errors if "Address Conflict" in err['msg']), None)
    assert conflict_error is not None, f"Wide signal overlap should be detected. Errors: {errors}"
    
    assert "wide_reg" in conflict_error['msg']
    assert "conflict_reg" in conflict_error['msg']
