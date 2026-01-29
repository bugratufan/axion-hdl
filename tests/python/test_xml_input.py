import pytest
import os
import shutil
import tempfile
from axion_hdl.xml_input_parser import XMLInputParser

@pytest.fixture
def xml_parser_env():
    tmp_dir = tempfile.mkdtemp()
    parser = XMLInputParser()
    yield tmp_dir, parser
    shutil.rmtree(tmp_dir, ignore_errors=True)

def write_xml(tmp_dir, name, content):
    f = os.path.join(tmp_dir, name)
    with open(f, 'w') as f_out:
        f_out.write(content)
    return f

def test_xml_input_001_file_detection(xml_parser_env):
    """XML-INPUT-001: Parser detects and loads .xml files."""
    tmp_dir, parser = xml_parser_env
    content = '<register_map module="m"><register name="r" access="RO"/></register_map>'
    f = write_xml(tmp_dir, "test.xml", content)
    result = parser.parse_file(f)
    assert result is not None
    assert result['name'] == 'm'

def test_xml_input_003_hex_address(xml_parser_env):
    """XML-INPUT-003: Parses hex string base address."""
    tmp_dir, parser = xml_parser_env
    content = '<register_map module="t" base_addr="0x1000"></register_map>'
    f = write_xml(tmp_dir, "t.xml", content)
    result = parser.parse_file(f)
    assert result['base_address'] == 0x1000

def test_xml_input_006_access_modes(xml_parser_env):
    """XML-INPUT-006: Handles RO, RW, WO (case-insensitive)."""
    tmp_dir, parser = xml_parser_env
    content = """
<register_map module="t">
  <register name="r1" access="ro"/>
  <register name="r2" access="RW"/>
  <register name="r3" access="Wo"/>
</register_map>
"""
    f = write_xml(tmp_dir, "t.xml", content)
    result = parser.parse_file(f)
    assert result['registers'][0]['access_mode'] == 'RO'
    assert result['registers'][1]['access_mode'] == 'RW'
    assert result['registers'][2]['access_mode'] == 'WO'

def test_xml_input_013_packed_registers(xml_parser_env):
    """XML-INPUT-013: Parses reg_name and bit_offset for subregisters."""
    tmp_dir, parser = xml_parser_env
    content = """
<register_map module="t">
  <register name="f1" reg_name="ctrl" bit_offset="0" width="1"/>
  <register name="f2" reg_name="ctrl" bit_offset="8" width="1"/>
</register_map>
"""
    f = write_xml(tmp_dir, "t.xml", content)
    result = parser.parse_file(f)
    packed = [r for r in result['registers'] if r.get('is_packed')]
    assert len(packed) == 1
    assert len(packed[0]['fields']) == 2
