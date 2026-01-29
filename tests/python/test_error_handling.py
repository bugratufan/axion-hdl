import pytest
import os
import shutil
import tempfile
from axion_hdl.parser import VHDLParser
from axion_hdl.address_manager import AddressConflictError
from axion_hdl.axion import AxionHDL

@pytest.fixture
def err_env():
    tmp_dir = tempfile.mkdtemp()
    parser = VHDLParser()
    yield tmp_dir, parser
    shutil.rmtree(tmp_dir, ignore_errors=True)

def test_err_001_address_conflict_error_message():
    """ERR-001: AddressConflictError string representation is clean."""
    err = AddressConflictError(0x1000, "reg_a", "reg_b", "mod_x")
    msg = str(err)
    assert "Address Conflict" in msg
    assert "0x1000" in msg
    assert "reg_a" in msg
    assert "reg_b" in msg
    # Clean message should not have ASCII art
    assert "╔" not in msg
    assert "VIOLATED REQUIREMENTS" not in msg
    # Formatted message should have ASCII art
    assert "╔" in err.formatted_message

def test_err_002_parser_partial_loading_on_conflict(err_env):
    """ERR-002: Parser returns module with errors on conflict."""
    tmp_dir, parser = err_env
    content = """
entity conflict_test is end;
architecture rtl of conflict_test is
    signal reg_a : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
    signal reg_b : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x00
begin end;
"""
    f = os.path.join(tmp_dir, "conflict.vhd")
    with open(f, 'w') as f_out: f_out.write(content)
    
    data = parser._parse_vhdl_file(f)
    assert data is not None
    assert data['name'] == 'conflict_test'
    
    # Check that both registers exist in data
    regs = [r['signal_name'] for r in data['registers']]
    assert 'reg_a' in regs
    assert 'reg_b' in regs
    
    # Check for recorded error
    errors = data.get('parsing_errors', [])
    assert any("Address Conflict" in e['msg'] and "0x0000" in e['msg'] for e in errors)

def test_err_003_skipped_files(err_env):
    """ERR-003: Skips files missing @axion or valid entities."""
    tmp_dir, parser = err_env
    f = os.path.join(tmp_dir, "no_axion.vhd")
    with open(f, 'w') as f_out: f_out.write("entity e is end;")
    
    data = parser._parse_vhdl_file(f)
    assert data is None

def test_err_004_invalid_hex_address(err_env):
    """ERR-004: Reports error for malformed hex strings."""
    tmp_dir, parser = err_env
    content = """
entity bad_hex is end;
architecture rtl of bad_hex is
    signal r : std_logic; -- @axion ADDR=0xGG
begin end;
"""
    f = os.path.join(tmp_dir, "bad_hex.vhd")
    with open(f, 'w') as f_out: f_out.write(content)
    
    with pytest.raises(ValueError):
        parser._parse_vhdl_file(f)

def test_err_006_duplicate_signal_detection(err_env):
    """ERR-006: Detects and reports duplicate signal names."""
    tmp_dir, parser = err_env
    content = """
entity dup is end;
architecture rtl of dup is
    signal a : std_logic; -- @axion ADDR=0x0
    signal a : std_logic; -- @axion ADDR=0x4
begin end;
"""
    f = os.path.join(tmp_dir, "dup.vhd")
    with open(f, 'w') as f_out: f_out.write(content)
    
    data = parser._parse_vhdl_file(f)
    assert data is not None
    regs = [r['signal_name'] for r in data['registers']]
    assert regs.count('a') == 2

def test_err_007_address_overlap_detection():
    """ERR-007: Raises AddressConflictError when modules overlap."""
    mod1 = {
        'name': 'm1', 
        'base_address': 0x1000, 
        'registers': [
            {'name': 'r1', 'offset': 0x0, 'width': 32},
            # r1 ends at 0x1004
            {'name': 'r2', 'offset': 0x4, 'width': 32}
            # r2 ends at 0x1008
        ]
    }
    mod2 = {
        'name': 'm2', 
        'base_address': 0x1004, 
        'registers': [
            {'name': 'r3', 'offset': 0x0, 'width': 32}
        ]
    }
    # m2 starts at 0x1004, which is where r1 ends and r2 starts. 
    # Since r2 starts at 0x1004, there's an overlap.
    
    axion = AxionHDL()
    axion.analyzed_modules = [mod1, mod2]
    axion.is_analyzed = True
    
    with pytest.raises(AddressConflictError) as exc:
        axion.check_address_overlaps()
    
    assert "Module m1" in str(exc.value)
    assert "Module m2" in str(exc.value)
