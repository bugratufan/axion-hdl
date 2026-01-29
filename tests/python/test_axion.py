import pytest
import os
import shutil
import tempfile
from axion_hdl import AxionHDL

@pytest.fixture
def test_setup():
    """Set up a temporary environment with a sample VHDL file."""
    tmp_dir = tempfile.mkdtemp()
    output_dir = os.path.join(tmp_dir, "output")
    
    # Create sample VHDL
    vhdl_content = """
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x1000
entity sample_mod is
    port (clk : in std_logic);
end entity;
architecture rtl of sample_mod is
    signal ctrl : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x00
begin
end architecture;
"""
    vhdl_file = os.path.join(tmp_dir, "sample.vhd")
    with open(vhdl_file, 'w') as f:
        f.write(vhdl_content)
        
    yield tmp_dir, output_dir
    
    shutil.rmtree(tmp_dir, ignore_errors=True)

def test_axion_full_workflow(test_setup):
    """Verify the full Axion HDL workflow: analyze -> generate all."""
    tmp_dir, output_dir = test_setup
    
    axion = AxionHDL(output_dir=output_dir)
    axion.add_src(tmp_dir)
    
    # Analyze
    assert axion.analyze() is True
    assert len(axion.analyzed_modules) == 1
    assert axion.analyzed_modules[0]['name'] == 'sample_mod'
    
    # Generate All
    axion.generate_all(doc_format="md")
    
    # Verify file existence with correct naming conventions
    expected_files = [
        "sample_mod_axion_reg.vhd",
        "register_map.md",
        "sample_mod_regs.xml",
        "sample_mod_regs.h",
        "sample_mod_regs.yaml",
        "sample_mod_regs.json"
    ]
    
    for filename in expected_files:
        filepath = os.path.join(output_dir, filename)
        assert os.path.exists(filepath), f"Missing generated file: {filename}"
        
        # Verify basic content
        with open(filepath, 'r') as f:
            content = f.read()
            assert len(content) > 0
            if filename.endswith(".vhd"):
                assert "entity sample_mod_axion_reg" in content
            elif filename.endswith(".h"):
                assert "SAMPLE_MOD" in content.upper()

def test_axion_exclude_logic(test_setup):
    """Verify that exclusion logic works correctly."""
    tmp_dir, output_dir = test_setup
    
    # Create an "error_cases" directory that should be excluded
    err_dir = os.path.join(tmp_dir, "error_cases")
    os.makedirs(err_dir)
    with open(os.path.join(err_dir, "bad.vhd"), 'w') as f:
        f.write("garbage content")
        
    axion = AxionHDL(output_dir=output_dir)
    axion.add_src(tmp_dir)
    axion.exclude("error_cases")
    
    # Analyze should succeed because bad.vhd is excluded
    assert axion.analyze() is True
    
    # Verify bad.vhd was NOT parsed
    for module in axion.analyzed_modules:
        assert os.path.basename(module['file']) != "bad.vhd"
