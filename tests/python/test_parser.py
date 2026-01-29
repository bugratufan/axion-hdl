import pytest
import os
import shutil
import tempfile
from axion_hdl.parser import VHDLParser
from axion_hdl.annotation_parser import AnnotationParser
from axion_hdl import AxionHDL

@pytest.fixture
def parser_env():
    tmp_dir = tempfile.mkdtemp()
    parser = VHDLParser()
    annot_parser = AnnotationParser()
    yield tmp_dir, parser, annot_parser
    shutil.rmtree(tmp_dir, ignore_errors=True)

def write_vhd(tmp_dir, name, content):
    f = os.path.join(tmp_dir, name)
    with open(f, 'w') as f_out: f_out.write(content)
    return f

def test_parser_001_entity_extraction(parser_env):
    """PARSER-001: Extract entity name correctly (requires at least one annotation)."""
    tmp_dir, parser, _ = parser_env
    vhdl = """
entity my_mod is end entity;
architecture rtl of my_mod is
    signal dummy : std_logic; -- @axion RO ADDR=0x0
begin end;
"""
    f = write_vhd(tmp_dir, "test.vhd", vhdl)
    result = parser.parse_file(f)
    assert result is not None
    assert result['entity_name'] == 'my_mod'

def test_parser_002_signal_types(parser_env):
    """PARSER-002: Parse signal widths."""
    tmp_dir, parser, _ = parser_env
    vhdl = """
entity t is end;
architecture rtl of t is
    signal s1 : std_logic; -- @axion RO ADDR=0x00
    signal s2 : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x04
begin end;
"""
    f = write_vhd(tmp_dir, "types.vhd", vhdl)
    result = parser.parse_file(f)
    widths = {s['name']: s['width'] for s in result['signals']}
    assert widths['s1'] == 1
    assert widths['s2'] == 32

def test_parser_003_strobe_parsing(parser_env):
    """PARSER-003: Parse strobe flags."""
    tmp_dir, parser, _ = parser_env
    vhdl = """
entity t is end;
architecture rtl of t is
    signal s : std_logic; -- @axion RO R_STROBE W_STROBE ADDR=0x00
begin end;
"""
    f = write_vhd(tmp_dir, "strobe.vhd", vhdl)
    result = parser.parse_file(f)
    sig = result['signals'][0]
    assert sig['r_strobe'] is True
    assert sig['w_strobe'] is True

def test_parser_004_def_parsing(parser_env):
    """PARSER-004: Parse @axion_def attributes (requires at least one signal annotation)."""
    tmp_dir, parser, _ = parser_env
    vhdl = """
-- @axion_def BASE_ADDR=0x1234 CDC_EN CDC_STAGE=4
entity t is end;
architecture rtl of t is
    signal s : std_logic; -- @axion RO ADDR=0x0
begin end;
"""
    f = write_vhd(tmp_dir, "def.vhd", vhdl)
    result = parser.parse_file(f)
    assert result is not None
    assert result['base_addr'] == 0x1234
    assert result['cdc_en'] is True
    assert result['cdc_stage'] == 4

def test_parser_006_description_parsing(parser_env):
    """PARSER-006: Parse quoted descriptions."""
    tmp_dir, parser, _ = parser_env
    vhdl = """
entity t is end;
architecture rtl of t is
    signal s : std_logic; -- @axion RO DESC="A test signal"
begin end;
"""
    f = write_vhd(tmp_dir, "desc.vhd", vhdl)
    result = parser.parse_file(f)
    assert "test signal" in result['signals'][0]['description']

def test_parser_007_exclude_directory(parser_env):
    """PARSER-007: Exclude directory pattern."""
    tmp_dir, _, _ = parser_env
    os.makedirs(os.path.join(tmp_dir, "excl"))
    write_vhd(tmp_dir, "keep.vhd", "entity keep is end;\narchitecture rtl of keep is\nsignal s : std_logic; -- @axion RO\nbegin end;")
    write_vhd(os.path.join(tmp_dir, "excl"), "skip.vhd", "entity skip is end;\narchitecture rtl of skip is\nsignal s : std_logic; -- @axion RO\nbegin end;")
    
    axion = AxionHDL(output_dir=os.path.join(tmp_dir, "out"))
    axion.add_src(tmp_dir)
    axion.exclude("excl")
    axion.analyze()
    
    # analyzed_modules uses 'name' key
    names = [m['name'] for m in axion.analyzed_modules]
    assert 'keep' in names
    assert 'skip' not in names

def test_parser_009_case_insensitivity(parser_env):
    """PARSER-009: Parse attributes case-insensitively."""
    tmp_dir, parser, _ = parser_env
    vhdl = """
-- @axion_def base_addr=0x1000
entity t is end;
architecture rtl of t is
    signal s : std_logic; -- @axion rw addr=0x04 desc="Low"
begin end;
"""
    f = write_vhd(tmp_dir, "case.vhd", vhdl)
    result = parser.parse_file(f)
    assert result['base_addr'] == 0x1000
    sig = result['signals'][0]
    assert sig['access'] == 'RW'
    assert sig['address'] == 4 
