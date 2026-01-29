import pytest
import os
import shutil
import tempfile
import json
from axion_hdl.json_input_parser import JSONInputParser

@pytest.fixture
def json_parser_env():
    tmp_dir = tempfile.mkdtemp()
    parser = JSONInputParser()
    yield tmp_dir, parser
    shutil.rmtree(tmp_dir, ignore_errors=True)

def write_json(tmp_dir, name, content_dict):
    f = os.path.join(tmp_dir, name)
    with open(f, 'w') as f_out:
        json.dump(content_dict, f_out)
    return f

def test_json_input_001_file_detection(json_parser_env):
    """JSON-INPUT-001: Parser detects and loads .json files."""
    tmp_dir, parser = json_parser_env
    content = {"module": "m", "registers": [{"name": "r"}]}
    f = write_json(tmp_dir, "test.json", content)
    result = parser.parse_file(f)
    assert result is not None
    assert result['name'] == 'm'

def test_json_input_003_hex_address(json_parser_env):
    """JSON-INPUT-003: Parses hex string base address."""
    tmp_dir, parser = json_parser_env
    content = {"module": "t", "base_addr": "0x1000", "registers": []}
    f = write_json(tmp_dir, "t.json", content)
    result = parser.parse_file(f)
    assert result['base_address'] == 0x1000

def test_json_input_006_access_modes(json_parser_env):
    """JSON-INPUT-006: Handles RO, RW, WO (case-insensitive)."""
    tmp_dir, parser = json_parser_env
    content = {
        "module": "t",
        "registers": [
            {"name": "r1", "access": "ro"},
            {"name": "r2", "access": "RW"},
            {"name": "r3", "access": "Wo"}
        ]
    }
    f = write_json(tmp_dir, "t.json", content)
    result = parser.parse_file(f)
    assert result['registers'][0]['access_mode'] == 'RO'
    assert result['registers'][1]['access_mode'] == 'RW'
    assert result['registers'][2]['access_mode'] == 'WO'

def test_json_input_010_auto_address(json_parser_env):
    """JSON-INPUT-010: Assigns sequential addresses if addr omitted."""
    tmp_dir, parser = json_parser_env
    content = {
        "module": "t",
        "registers": [
            {"name": "r1"},
            {"name": "r2"}
        ]
    }
    f = write_json(tmp_dir, "t.json", content)
    result = parser.parse_file(f)
    assert result['registers'][0]['relative_address_int'] == 0
    assert result['registers'][1]['relative_address_int'] == 4

def test_json_input_011_invalid_json(json_parser_env):
    """JSON-INPUT-011: Returns None for malformed JSON."""
    tmp_dir, parser = json_parser_env
    f = os.path.join(tmp_dir, "bad.json")
    with open(f, 'w') as f_out: f_out.write("{ broken }")
    result = parser.parse_file(f)
    assert result is None

def test_json_input_013_packed_registers(json_parser_env):
    """JSON-INPUT-013: Parses reg_name and bit_offset for subregisters."""
    tmp_dir, parser = json_parser_env
    content = {
        "module": "t",
        "registers": [
            {"name": "f1", "reg_name": "ctrl", "bit_offset": 0, "width": 1},
            {"name": "f2", "reg_name": "ctrl", "bit_offset": 8, "width": 1}
        ]
    }
    f = write_json(tmp_dir, "t.json", content)
    result = parser.parse_file(f)
    packed = [r for r in result['registers'] if r.get('is_packed')]
    assert len(packed) == 1
    assert len(packed[0]['fields']) == 2
