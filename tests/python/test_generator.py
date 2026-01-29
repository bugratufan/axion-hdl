import pytest
import os
import shutil
import tempfile
import subprocess
import xml.etree.ElementTree as ET
from axion_hdl import AxionHDL

@pytest.fixture(scope="module")
def gen_env():
    tmp_dir = tempfile.mkdtemp()
    output_dir = os.path.join(tmp_dir, "output")
    os.makedirs(output_dir)
    
    vhdl_content = """
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x1000
entity generator_test is
    port (clk, rst_n : in std_logic);
end entity;
architecture rtl of generator_test is
    signal s_reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00 DESC="Status"
    signal c_reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x04 DESC="Control"
    signal w_reg : std_logic_vector(31 downto 0); -- @axion WO ADDR=0x08 W_STROBE DESC="Command"
    signal d_reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x0C R_STROBE DESC="Data"
begin end;
"""
    vhdl_file = os.path.join(tmp_dir, "generator_test.vhd")
    with open(vhdl_file, 'w') as f: f.write(vhdl_content)
    
    axion = AxionHDL(output_dir=output_dir)
    axion.add_src(tmp_dir)
    axion.analyze()
    axion.generate_vhdl()
    axion.generate_c_header()
    axion.generate_xml()
    axion.generate_documentation(format="md")
    axion.generate_documentation(format="html")
    
    paths = {
        'vhdl': os.path.join(output_dir, "generator_test_axion_reg.vhd"),
        'header': os.path.join(output_dir, "generator_test_regs.h"),
        'xml': os.path.join(output_dir, "generator_test_regs.xml"),
        'md': os.path.join(output_dir, "register_map.md"),
        'html': os.path.join(output_dir, "register_map.html")
    }
    
    yield tmp_dir, output_dir, paths
    shutil.rmtree(tmp_dir, ignore_errors=True)

def test_gen_001_vhdl_entity(gen_env):
    """GEN-001: Generated VHDL exists and has correct entity name."""
    _, _, paths = gen_env
    assert os.path.exists(paths['vhdl'])
    with open(paths['vhdl'], 'r') as f:
        content = f.read().lower()
    assert 'entity generator_test_axion_reg is' in content

def test_gen_001_vhdl_compiles(gen_env):
    """GEN-001: Generated VHDL compiles with GHDL."""
    tmp_dir, _, paths = gen_env
    if shutil.which('ghdl') is None:
        pytest.skip("GHDL not available")
    
    work_dir = os.path.join(tmp_dir, "work")
    os.makedirs(work_dir, exist_ok=True)
    res = subprocess.run(['ghdl', '-a', '--std=08', f'--workdir={work_dir}', paths['vhdl']], capture_output=True)
    assert res.returncode == 0

def test_gen_003_axi_ports(gen_env):
    """GEN-003: AXI port signals present."""
    _, _, paths = gen_env
    with open(paths['vhdl'], 'r') as f:
        content = f.read().lower()
    signals = ['axi_aclk', 'axi_aresetn', 'axi_awaddr', 'axi_wdata', 'axi_araddr', 'axi_rdata']
    for s in signals:
        assert s in content

def test_gen_009_c_header(gen_env):
    """GEN-009: C header exists and compiles."""
    tmp_dir, _, paths = gen_env
    assert os.path.exists(paths['header'])
    
    if shutil.which('gcc') is None:
        pytest.skip("GCC not available")
        
    test_c = os.path.join(tmp_dir, "test_h.c")
    with open(test_c, 'w') as f:
        f.write(f'#include "{paths["header"]}"\nint main() {{ return 0; }}')
    res = subprocess.run(['gcc', '-c', test_c, '-o', '/dev/null'], capture_output=True)
    assert res.returncode == 0

def test_gen_011_xml_well_formed(gen_env):
    """GEN-011: XML is well-formed."""
    _, _, paths = gen_env
    assert os.path.exists(paths['xml'])
    ET.parse(paths['xml'])

def test_gen_012_markdown(gen_env):
    """GEN-012: Markdown has table and addresses."""
    _, _, paths = gen_env
    assert os.path.exists(paths['md'])
    with open(paths['md'], 'r') as f:
        content = f.read()
    assert '|' in content
    assert '0x' in content.lower()
