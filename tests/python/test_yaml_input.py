import pytest
import os
import shutil
import tempfile
import yaml
from axion_hdl.yaml_input_parser import YAMLInputParser

@pytest.fixture
def yaml_parser_env():
    tmp_dir = tempfile.mkdtemp()
    parser = YAMLInputParser()
    yield tmp_dir, parser
    shutil.rmtree(tmp_dir, ignore_errors=True)

def write_yaml(tmp_dir, name, content_dict):
    f = os.path.join(tmp_dir, name)
    with open(f, 'w') as f_out:
        yaml.dump(content_dict, f_out)
    return f

def test_yaml_input_001_file_detection(yaml_parser_env):
    """YAML-INPUT-001: Parser detects and loads .yaml files."""
    tmp_dir, parser = yaml_parser_env
    content = {"module": "m", "registers": [{"name": "r"}]}
    f = write_yaml(tmp_dir, "test.yaml", content)
    result = parser.parse_file(f)
    assert result is not None
    assert result['name'] == 'm'

def test_yaml_input_003_hex_address(yaml_parser_env):
    """YAML-INPUT-003: Parses hex string base address."""
    tmp_dir, parser = yaml_parser_env
    content = {"module": "t", "base_addr": "0x1000", "registers": []}
    f = write_yaml(tmp_dir, "t.yaml", content)
    result = parser.parse_file(f)
    assert result['base_address'] == 0x1000

def test_yaml_input_006_access_modes(yaml_parser_env):
    """YAML-INPUT-006: Handles RO, RW, WO (case-insensitive)."""
    tmp_dir, parser = yaml_parser_env
    content = {
        "module": "t",
        "registers": [
            {"name": "r1", "access": "ro"},
            {"name": "r2", "access": "RW"},
            {"name": "r3", "access": "Wo"}
        ]
    }
    f = write_yaml(tmp_dir, "t.yaml", content)
    result = parser.parse_file(f)
    assert result['registers'][0]['access_mode'] == 'RO'
    assert result['registers'][1]['access_mode'] == 'RW'
    assert result['registers'][2]['access_mode'] == 'WO'

def test_yaml_input_013_packed_registers(yaml_parser_env):
    """YAML-INPUT-013: Parses reg_name and bit_offset for subregisters."""
    tmp_dir, parser = yaml_parser_env
    content = {
        "module": "t",
        "registers": [
            {"name": "f1", "reg_name": "ctrl", "bit_offset": 0, "width": 1},
            {"name": "f2", "reg_name": "ctrl", "bit_offset": 8, "width": 1}
        ]
    }
    f = write_yaml(tmp_dir, "t.yaml", content)
    result = parser.parse_file(f)
    packed = [r for r in result['registers'] if r.get('is_packed')]
    assert len(packed) == 1
    assert len(packed[0]['fields']) == 2
