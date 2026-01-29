import pytest
import os
import shutil
import tempfile
from axion_hdl import AxionHDL
from axion_hdl.parser import VHDLParser

@pytest.fixture
def test_env():
    """Set up temporary directory and parser."""
    tmp_dir = tempfile.mkdtemp()
    parser = VHDLParser()
    yield tmp_dir, parser
    shutil.rmtree(tmp_dir, ignore_errors=True)

def write_vhdl(tmp_dir, filename, content):
    filepath = os.path.join(tmp_dir, filename)
    with open(filepath, 'w') as f:
        f.write(content)
    return filepath

def test_addr_001_auto_assign_sequential(test_env):
    """ADDR-001: Auto-assigned addresses are sequential."""
    tmp_dir, parser = test_env
    vhdl = """
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity auto_addr is
    port (clk : in std_logic);
end entity;
architecture rtl of auto_addr is
    signal reg_a : std_logic_vector(31 downto 0); -- @axion RO
    signal reg_b : std_logic_vector(31 downto 0); -- @axion RW
    signal reg_c : std_logic_vector(31 downto 0); -- @axion WO
begin
end architecture;
"""
    filepath = write_vhdl(tmp_dir, "auto_addr.vhd", vhdl)
    result = parser.parse_file(filepath)
    
    signals = result.get('signals', [])
    assert len(signals) == 3
    addresses = [s['address'] for s in signals]
    assert addresses == [0, 4, 8]

def test_addr_001_first_addr_zero(test_env):
    """ADDR-001: First auto-assigned address is 0x00."""
    tmp_dir, parser = test_env
    vhdl = """
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity first_zero is
    port (clk : in std_logic);
end entity;
architecture rtl of first_zero is
    signal first_reg : std_logic_vector(31 downto 0); -- @axion RO
begin
end architecture;
"""
    filepath = write_vhdl(tmp_dir, "first_zero.vhd", vhdl)
    result = parser.parse_file(filepath)
    assert result['signals'][0]['address'] == 0

def test_addr_002_manual_address(test_env):
    """ADDR-002: ADDR attribute sets specific address."""
    tmp_dir, parser = test_env
    vhdl = """
-- @axion_def BASE_ADDR=0x0000
entity manual_addr is
    port (clk : in std_logic);
end entity;
architecture rtl of manual_addr is
    signal reg_a : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x100
begin
end architecture;
"""
    filepath = write_vhdl(tmp_dir, "manual_addr.vhd", vhdl)
    result = parser.parse_file(filepath)
    assert result['signals'][0]['address'] == 0x100

def test_addr_003_mixed_assignment(test_env):
    """ADDR-003: Mixed auto and manual addresses work correctly."""
    tmp_dir, parser = test_env
    vhdl = """
-- @axion_def BASE_ADDR=0x0000
entity mixed_addr is
    port (clk : in std_logic);
end entity;
architecture rtl of mixed_addr is
    signal reg_a : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x10
    signal reg_b : std_logic_vector(31 downto 0); -- @axion RW
    signal reg_c : std_logic_vector(31 downto 0); -- @axion WO ADDR=0x20
begin
end architecture;
"""
    filepath = write_vhdl(tmp_dir, "mixed_addr.vhd", vhdl)
    result = parser.parse_file(filepath)
    addr_dict = {s['name']: s['address'] for s in result['signals']}
    assert addr_dict['reg_a'] == 0x10
    assert addr_dict['reg_b'] == 0x14
    assert addr_dict['reg_c'] == 0x20

def test_addr_004_alignment(test_env):
    """ADDR-004: Addresses are 4-byte aligned."""
    tmp_dir, parser = test_env
    vhdl = """
-- @axion_def BASE_ADDR=0x0000
entity align_test is
    port (clk : in std_logic);
end entity;
architecture rtl of align_test is
    signal reg_a : std_logic_vector(31 downto 0); -- @axion RO
    signal reg_b : std_logic_vector(31 downto 0); -- @axion RW
begin
end architecture;
"""
    filepath = write_vhdl(tmp_dir, "align_test.vhd", vhdl)
    result = parser.parse_file(filepath)
    for sig in result['signals']:
        assert sig['address'] % 4 == 0

def test_addr_005_conflict_detection(test_env):
    """ADDR-005: Duplicate addresses reported in parsing_errors."""
    tmp_dir, parser = test_env
    vhdl = """
-- @axion_def BASE_ADDR=0x0000
entity conflict is
    port (clk : in std_logic);
end entity;
architecture rtl of conflict is
    signal reg_a : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x10
    signal reg_b : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x10
begin
end architecture;
"""
    write_vhdl(tmp_dir, "conflict.vhd", vhdl)
    axion = AxionHDL(output_dir=os.path.join(tmp_dir, "out"))
    axion.add_src(tmp_dir)
    axion.analyze()
    
    found_conflict = any(
        "Address Conflict" in err.get('msg', '')
        for module in axion.analyzed_modules
        for err in module.get('parsing_errors', [])
    )
    assert found_conflict is True

def test_addr_006_wide_signal_space(test_env):
    """ADDR-006: Wide signals reserve multiple address slots."""
    tmp_dir, parser = test_env
    vhdl = """
-- @axion_def BASE_ADDR=0x0000
entity wide_space is
    port (clk : in std_logic);
end entity;
architecture rtl of wide_space is
    signal wide_reg : std_logic_vector(63 downto 0); -- @axion RO ADDR=0x00
    signal next_reg : std_logic_vector(31 downto 0); -- @axion RW
begin
end architecture;
"""
    filepath = write_vhdl(tmp_dir, "wide_space.vhd", vhdl)
    result = parser.parse_file(filepath)
    addr_dict = {s['name']: s['address'] for s in result['signals']}
    assert addr_dict['wide_reg'] == 0x00
    assert addr_dict['next_reg'] == 0x08

def test_addr_007_gaps_preserved(test_env):
    """ADDR-007: Gaps between manual addresses preserved."""
    tmp_dir, parser = test_env
    vhdl = """
-- @axion_def BASE_ADDR=0x0000
entity gaps is
    port (clk : in std_logic);
end entity;
architecture rtl of gaps is
    signal reg_a : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
    signal reg_b : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x100
begin
end architecture;
"""
    filepath = write_vhdl(tmp_dir, "gaps.vhd", vhdl)
    result = parser.parse_file(filepath)
    addr_dict = {s['name']: s['address'] for s in result['signals']}
    assert addr_dict['reg_a'] == 0x00
    assert addr_dict['reg_b'] == 0x100

def test_addr_008_base_address_addition(test_env):
    """ADDR-008: BASE_ADDR added to relative addresses."""
    tmp_dir, parser = test_env
    vhdl = """
-- @axion_def BASE_ADDR=0x1000
entity base_add is
    port (clk : in std_logic);
end entity;
architecture rtl of base_add is
    signal reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x04
begin
end architecture;
"""
    filepath = write_vhdl(tmp_dir, "base_add.vhd", vhdl)
    result = parser.parse_file(filepath)
    assert result['signals'][0]['address'] == 0x04
    assert result['base_addr'] == 0x1000
