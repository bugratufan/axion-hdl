import pytest
import os
import shutil
import tempfile
import re
from pathlib import Path
from axion_hdl.xml_input_parser import XMLInputParser
from axion_hdl.yaml_input_parser import YAMLInputParser
from axion_hdl.json_input_parser import JSONInputParser
from axion_hdl.generator import VHDLGenerator
from axion_hdl.doc_generators import YAMLGenerator, JSONGenerator

@pytest.fixture(scope="module")
def paths():
    project_root = Path(__file__).resolve().parent.parent.parent
    return {
        'xml': project_root / "tests" / "xml" / "sensor_controller.xml",
        'yaml': project_root / "tests" / "yaml" / "sensor_controller.yaml",
        'json': project_root / "tests" / "json" / "sensor_controller.json"
    }

@pytest.fixture
def temp_dir():
    tmp = tempfile.mkdtemp()
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)

def compare_modules(mod1, mod2, desc=""):
    assert mod1['name'] == mod2['name'], f"Names differ {desc}"
    assert mod1['base_address'] == mod2['base_address'], f"Base addrs differ {desc}"
    assert mod1['cdc_enabled'] == mod2['cdc_enabled'], f"CDC en differs {desc}"
    
    assert len(mod1['registers']) == len(mod2['registers']), f"Reg count differs {desc}"
    
    for i, (r1, r2) in enumerate(zip(mod1['registers'], mod2['registers'])):
        assert r1['signal_name'] == r2['signal_name'], f"Reg {i} name differs {desc}"
        assert r1['access_mode'] == r2['access_mode'], f"Reg {i} access differs {desc}"
        assert r1['relative_address_int'] == r2['relative_address_int'], f"Reg {i} addr differs {desc}"

def test_equiv_001_xml_yaml(paths):
    xml_mod = XMLInputParser().parse_file(str(paths['xml']))
    yaml_mod = YAMLInputParser().parse_file(str(paths['yaml']))
    compare_modules(xml_mod, yaml_mod, "(XML vs YAML)")

def test_equiv_002_xml_json(paths):
    xml_mod = XMLInputParser().parse_file(str(paths['xml']))
    json_mod = JSONInputParser().parse_file(str(paths['json']))
    compare_modules(xml_mod, json_mod, "(XML vs JSON)")

def test_equiv_004_yaml_roundtrip(paths, temp_dir):
    parser = YAMLInputParser()
    original = parser.parse_file(str(paths['yaml']))
    
    gen = YAMLGenerator(temp_dir)
    out = gen.generate_yaml(original)
    
    roundtrip = parser.parse_file(out)
    compare_modules(original, roundtrip, "(YAML roundtrip)")

def test_equiv_005_json_roundtrip(paths, temp_dir):
    parser = JSONInputParser()
    original = parser.parse_file(str(paths['json']))
    
    gen = JSONGenerator(temp_dir)
    out = gen.generate_json(original)
    
    roundtrip = parser.parse_file(out)
    compare_modules(original, roundtrip, "(JSON roundtrip)")

def test_equiv_006_cross_format_vhdl(paths, temp_dir):
    xml_mod = XMLInputParser().parse_file(str(paths['xml']))
    yaml_mod = YAMLInputParser().parse_file(str(paths['yaml']))
    json_mod = JSONInputParser().parse_file(str(paths['json']))
    
    def get_vhdl(mod, sub):
        d = os.path.join(temp_dir, sub)
        os.makedirs(d, exist_ok=True)
        path = VHDLGenerator(d).generate_module(mod)
        with open(path, 'r') as f:
            content = f.read()
            # Normalize: remove source comments
            content = re.sub(r'--\s*Source:.*\n', '', content)
            content = re.sub(r'sensor_controller\.(xml|yaml|json)', 'sensor.src', content)
            return content

    v_xml = get_vhdl(xml_mod, "xml")
    v_yaml = get_vhdl(yaml_mod, "yaml")
    v_json = get_vhdl(json_mod, "json")
    
    assert v_xml == v_yaml
    assert v_xml == v_json
