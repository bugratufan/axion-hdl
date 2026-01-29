import pytest
import os
import shutil
import tempfile
from axion_hdl import AxionHDL

@pytest.fixture
def cdc_test_env():
    """Set up temporary directory and Axion instance."""
    tmp_dir = tempfile.mkdtemp()
    output_dir = os.path.join(tmp_dir, "output")
    yield tmp_dir, output_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)

def generate_vhdl(tmp_dir, output_dir, entity_name, vhdl_content):
    vhdl_file = os.path.join(tmp_dir, f"{entity_name}.vhd")
    with open(vhdl_file, 'w') as f:
        f.write(vhdl_content)
    
    axion = AxionHDL(output_dir=output_dir)
    axion.add_src(tmp_dir)
    axion.analyze()
    axion.generate_vhdl()
    
    gen_file = os.path.join(output_dir, f"{entity_name}_axion_reg.vhd")
    if os.path.exists(gen_file):
        with open(gen_file, 'r') as f:
            return f.read()
    return ""

def test_cdc_001_stage_count_2(cdc_test_env):
    """CDC-001: CDC_STAGE=2 generates 2-stage synchronizer."""
    tmp_dir, output_dir = cdc_test_env
    vhdl = """
-- @axion_def BASE_ADDR=0x0000 CDC_EN CDC_STAGE=2
entity cdc2 is
    port (clk : in std_logic);
end entity;
architecture rtl of cdc2 is
    signal status : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
"""
    content = generate_vhdl(tmp_dir, output_dir, "cdc2", vhdl)
    assert "module_clk" in content.lower()
    # Should have sync0 and sync1 (2 stages)
    assert "status_sync0" in content
    assert "status_sync1" in content
    assert "status_sync2" not in content

def test_cdc_001_stage_count_3(cdc_test_env):
    """CDC-001: CDC_STAGE=3 generates 3-stage synchronizer."""
    tmp_dir, output_dir = cdc_test_env
    vhdl = """
-- @axion_def BASE_ADDR=0x0000 CDC_EN CDC_STAGE=3
entity cdc3 is
    port (clk : in std_logic);
end entity;
architecture rtl of cdc3 is
    signal status : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
"""
    content = generate_vhdl(tmp_dir, output_dir, "cdc3", vhdl)
    assert "module_clk" in content.lower()
    # Should have sync0, sync1, and sync2 (3 stages)
    assert "status_sync0" in content
    assert "status_sync1" in content
    assert "status_sync2" in content
    assert "status_sync3" not in content

def test_cdc_002_default_stage_count(cdc_test_env):
    """CDC-002: CDC_EN without CDC_STAGE defaults to 2 stages."""
    tmp_dir, output_dir = cdc_test_env
    vhdl = """
-- @axion_def BASE_ADDR=0x0000 CDC_EN
entity cdc_def is
    port (clk : in std_logic);
end entity;
architecture rtl of cdc_def is
    signal status : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
"""
    content = generate_vhdl(tmp_dir, output_dir, "cdc_def", vhdl)
    assert "status_sync0" in content
    assert "status_sync1" in content
    assert "status_sync2" not in content

def test_cdc_005_cdc_disabled(cdc_test_env):
    """CDC-005: Without CDC_EN, no CDC signals generated."""
    tmp_dir, output_dir = cdc_test_env
    vhdl = """
-- @axion_def BASE_ADDR=0x0000
entity no_cdc is
    port (clk : in std_logic);
end entity;
architecture rtl of no_cdc is
    signal status : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
"""
    content = generate_vhdl(tmp_dir, output_dir, "no_cdc", vhdl)
    assert "module_clk" not in content.lower()
    assert "sync0" not in content.lower()

def test_cdc_006_ro_cdc_path(cdc_test_env):
    """CDC-006: RO registers synchronized from module to AXI domain."""
    tmp_dir, output_dir = cdc_test_env
    vhdl = """
-- @axion_def BASE_ADDR=0x0000 CDC_EN
entity ro_cdc is
    port (clk : in std_logic);
end entity;
architecture rtl of ro_cdc is
    signal status_ro : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
"""
    content = generate_vhdl(tmp_dir, output_dir, "ro_cdc", vhdl)
    # RO should be assigned from synchronizer stage 1 (last stage for default 2)
    assert "status_ro_reg <= status_ro_sync1;" in content

def test_cdc_007_rw_cdc_path(cdc_test_env):
    """CDC-007: Writable registers synchronized from AXI to module domain."""
    tmp_dir, output_dir = cdc_test_env
    vhdl = """
-- @axion_def BASE_ADDR=0x0000 CDC_EN
entity rw_cdc is
    port (clk : in std_logic);
end entity;
architecture rtl of rw_cdc is
    signal control_rw : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x00
begin
end architecture;
"""
    content = generate_vhdl(tmp_dir, output_dir, "rw_cdc", vhdl)
    # Output port should be assigned from synchronizer
    assert "control_rw <= control_rw_sync1;" in content
    # Synchronizer should take reg value
    assert "control_rw_sync0 <= control_rw_reg;" in content
