import pytest
import os
import shutil
import tempfile
from axion_hdl.parser import VHDLParser
from axion_hdl.annotation_parser import AnnotationParser

@pytest.fixture
def def_env():
    tmp_dir = tempfile.mkdtemp()
    parser = VHDLParser()
    annotation_parser = AnnotationParser()
    yield tmp_dir, parser, annotation_parser
    shutil.rmtree(tmp_dir, ignore_errors=True)

def test_def_001_parse_hex_default(def_env):
    """DEF-001: Parse DEFAULT hex value."""
    tmp_dir, parser, annot_parser = def_env
    attrs = annot_parser.parse_attributes("RW DEFAULT=0xDEADBEEF")
    assert attrs.get('default_value') == 0xDEADBEEF

def test_def_002_parse_decimal_default(def_env):
    """DEF-002: Parse DEFAULT decimal value."""
    tmp_dir, parser, annot_parser = def_env
    attrs = annot_parser.parse_attributes("RW DEFAULT=100")
    assert attrs.get('default_value') == 100

def test_def_003_register_has_default(def_env):
    """DEF-003: Register data includes default_value."""
    tmp_dir, parser, annot_parser = def_env
    vhdl = """
-- @axion_def BASE_ADDR=0x0000
entity t is end entity;
architecture rtl of t is
    signal config : std_logic_vector(31 downto 0);  -- @axion RW DEFAULT=0xDEADBEEF
begin end architecture;
"""
    f = os.path.join(tmp_dir, "t.vhd")
    with open(f, 'w') as f_out: f_out.write(vhdl)
    
    result = parser._parse_vhdl_file(f)
    assert result['registers'][0]['default_value'] == 0xDEADBEEF

def test_def_004_default_zero_when_missing(def_env):
    """DEF-004: Default to 0 if not specified."""
    tmp_dir, parser, annot_parser = def_env
    vhdl = """
-- @axion_def BASE_ADDR=0x0000
entity t is end entity;
architecture rtl of t is
    signal status : std_logic_vector(31 downto 0);  -- @axion RO
begin end architecture;
"""
    f = os.path.join(tmp_dir, "t.vhd")
    with open(f, 'w') as f_out: f_out.write(vhdl)
    result = parser._parse_vhdl_file(f)
    assert result['registers'][0]['default_value'] == 0

def test_def_009_combine_subregister_defaults(def_env):
    """DEF-009: Combine subregister defaults into register default."""
    tmp_dir, parser, annot_parser = def_env
    vhdl = """
-- @axion_def BASE_ADDR=0x0000
entity t is end entity;
architecture rtl of t is
    signal enable : std_logic;  -- @axion RW ADDR=0x00 REG_NAME=control BIT_OFFSET=0 DEFAULT=1
    signal mode : std_logic_vector(1 downto 0);  -- @axion RW ADDR=0x00 REG_NAME=control BIT_OFFSET=1 DEFAULT=2
    signal prescaler : std_logic_vector(7 downto 0);  -- @axion RW ADDR=0x00 REG_NAME=control BIT_OFFSET=3 DEFAULT=10
begin end architecture;
"""
    f = os.path.join(tmp_dir, "t.vhd")
    with open(f, 'w') as f_out: f_out.write(vhdl)
    result = parser._parse_vhdl_file(f)
    
    packed_reg = result['packed_registers'][0]
    # 1 | (2 << 1) | (10 << 3) = 1 + 4 + 80 = 85
    expected = 1 | (2 << 1) | (10 << 3)
    assert packed_reg['default_value'] == expected

def test_single_bit_default(def_env):
    """Single bit std_logic with DEFAULT=1."""
    tmp_dir, parser, annot_parser = def_env
    vhdl = """
-- @axion_def BASE_ADDR=0x0000
entity t is end entity;
architecture rtl of t is
    signal enable : std_logic;  -- @axion RW DEFAULT=1
begin end architecture;
"""
    f = os.path.join(tmp_dir, "t.vhd")
    with open(f, 'w') as f_out: f_out.write(vhdl)
    result = parser._parse_vhdl_file(f)
    assert result['registers'][0]['default_value'] == 1
