import os
from axion_hdl import AxionHDL
from axion_hdl.yaml_input_parser import YAMLInputParser
from axion_hdl.xml_input_parser import XMLInputParser

def test_val_006_yaml_numeric_validation(tmp_path):
    """VAL-006: Invalid numeric values in YAML must be reported as Parsing Errors."""
    p = tmp_path / "invalid.yaml"
    p.write_text("""
module: invalid_module
base_addr: "not_a_base_addr"
config:
  cdc_en: true
  cdc_stage: "invalid_stage"
registers:
  - name: reg1
    addr: "invalid_addr"
    width: "invalid_width"
    default: "invalid_default"
""")
    
    parser = YAMLInputParser()
    module = parser.parse_file(str(p))
    
    assert module is not None
    assert 'parsing_errors' in module
    errors = [e['msg'] for e in module['parsing_errors']]
    
    assert any("not_a_base_addr" in e for e in errors)
    assert any("invalid_stage" in e for e in errors)
    assert any("invalid_addr" in e for e in errors)
    assert any("invalid_width" in e for e in errors)
    assert any("invalid_default" in e for e in errors)

def test_val_006_xml_numeric_validation(tmp_path):
    """VAL-006: Invalid numeric values in XML must be reported as Parsing Errors."""
    p = tmp_path / "invalid.xml"
    p.write_text("""
<register_map module="invalid_xml" base_addr="invalid_base">
    <config cdc_stage="invalid_stage"/>
    <register name="reg1" addr="invalid_addr" width="invalid_width" default="invalid_default"/>
</register_map>
""")
    
    parser = XMLInputParser()
    module = parser.parse_file(str(p))
    
    assert module is not None
    assert 'parsing_errors' in module
    errors = [e['msg'] for e in module['parsing_errors']]
    
    assert any("invalid_base" in e for e in errors)
    assert any("invalid_stage" in e for e in errors)
    assert any("invalid_addr" in e for e in errors)
    assert any("invalid_width" in e for e in errors)
    assert any("invalid_default" in e for e in errors)

def test_val_007_generation_safety_lock(tmp_path):
    """VAL-007: Tool must block generation if any module has parsing errors."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    
    p = src_dir / "invalid.yaml"
    p.write_text("""
module: invalid_module
base_addr: "broken"
registers:
  - name: reg1
    access: RW
""")
    
    axion = AxionHDL(output_dir=str(out_dir))
    axion.add_source(str(src_dir))
    axion.analyze()
    
    # Verify parsing error is caught
    assert any(m.get('parsing_errors') for m in axion.analyzed_modules)
    
    # Try to generate - should return False
    assert axion.generate_vhdl() is False
    assert axion.generate_xml() is False
    assert axion.generate_yaml() is False
    assert axion.generate_json() is False
    assert axion.generate_toml() is False
    assert axion.generate_c_header() is False
    assert axion.generate_documentation() is False
    
    # Ensure no files were generated
    assert len(os.listdir(str(out_dir))) == 0
