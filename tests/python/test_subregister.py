import pytest
import os
import shutil
import tempfile
from axion_hdl.parser import VHDLParser
from axion_hdl.bit_field_manager import BitFieldManager, BitOverlapError, BitField

@pytest.fixture
def sub_env():
    tmp_dir = tempfile.mkdtemp()
    parser = VHDLParser()
    yield tmp_dir, parser
    shutil.rmtree(tmp_dir, ignore_errors=True)

def test_sub_001_parse_reg_name(sub_env):
    """SUB-001: Parse REG_NAME attribute."""
    tmp_dir, parser = sub_env
    vhdl = """
architecture rtl of t is
    signal enable : std_logic;  -- @axion RW ADDR=0x00 REG_NAME=control BIT_OFFSET=0
begin end;
"""
    f = os.path.join(tmp_dir, "t.vhd")
    with open(f, 'w') as f_out: f_out.write("entity t is end;\n" + vhdl)
    result = parser._parse_vhdl_file(f)
    assert result is not None
    assert len(result['packed_registers']) == 1
    assert result['packed_registers'][0]['reg_name'] == 'control'

def test_sub_002_parse_bit_offset(sub_env):
    """SUB-002: Parse BIT_OFFSET and calculate widths."""
    tmp_dir, parser = sub_env
    vhdl = """
-- @axion_def BASE_ADDR=0x0
entity t is end;
architecture rtl of t is
    signal enable : std_logic;  -- @axion RW ADDR=0x00 REG_NAME=control BIT_OFFSET=0
    signal mode : std_logic_vector(1 downto 0);  -- @axion RW ADDR=0x00 REG_NAME=control BIT_OFFSET=1
begin end;
"""
    f = os.path.join(tmp_dir, "t.vhd")
    with open(f, 'w') as f_out: f_out.write(vhdl)
    result = parser._parse_vhdl_file(f)
    fields = result['packed_registers'][0]['fields']
    assert len(fields) == 2
    assert fields[0]['bit_low'] == 0
    assert fields[1]['bit_low'] == 1
    assert fields[1]['bit_high'] == 2

def test_sub_004_auto_calculate_width():
    """SUB-004: Auto-calculate register width from fields."""
    mgr = BitFieldManager()
    mgr.add_field("status", 0x00, "f1", 1, "RO", "[0:0]", bit_offset=0)
    mgr.add_field("status", 0x00, "f2", 8, "RO", "[7:0]", bit_offset=16)
    reg = mgr.get_register("status")
    # highest bit is 16+8-1 = 23. used_bits = 24
    assert reg.used_bits == 24

def test_sub_005_detect_bit_overlap():
    """SUB-005: Detect and report bit overlaps."""
    mgr = BitFieldManager()
    mgr.add_field("c", 0x0, "a", 8, "RW", "[7:0]", bit_offset=0)
    with pytest.raises(BitOverlapError) as exc:
        mgr.add_field("c", 0x0, "b", 8, "RW", "[7:0]", bit_offset=4)
    assert "overlap" in str(exc.value).lower()
    assert "a" in str(exc.value)
    assert "b" in str(exc.value)

def test_sub_006_auto_pack():
    """SUB-006: Auto-pack signals when BIT_OFFSET is omitted."""
    mgr = BitFieldManager()
    f1 = mgr.add_field("s", 0x0, "f1", 1, "RO", "[0:0]")
    f2 = mgr.add_field("s", 0x0, "f2", 8, "RO", "[7:0]")
    assert f1.bit_low == 0
    assert f2.bit_low == 1
    assert f2.bit_high == 8

def test_bit_field_mask():
    """Test bit field mask generation."""
    field = BitField("m", 1, 2, 2, "RW", "[1:0]")
    # bits [2:1] = 0b110 = 6
    assert field.mask == 0x06
