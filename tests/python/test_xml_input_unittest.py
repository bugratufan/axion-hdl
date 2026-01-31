"""
test_xml_input_unittest.py - XML Input Parser Requirements Tests

Tests for XML-INPUT-001 through XML-INPUT-015 requirements.
Verifies the XML input parser functionality for register definition parsing.
"""

import unittest
import os
import tempfile
import shutil
from pathlib import Path

# Import the XML parser
from axion_hdl.xml_input_parser import XMLInputParser


class TestXMLInputRequirements(unittest.TestCase):
    """Test cases for XML-INPUT-xxx requirements"""

    def setUp(self):
        """Set up test fixtures"""
        self.parser = XMLInputParser()
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(__file__).parent.parent.parent

    def tearDown(self):
        """Clean up temp files"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def write_xml(self, content):
        """Write XML content to temp file and return path"""
        xml_file = os.path.join(self.temp_dir, "test.xml")
        with open(xml_file, 'w') as f:
            f.write(content)
        return xml_file

    # XML-INPUT-001: XML file detection
    def test_xml_input_001_file_detection(self):
        """XML-INPUT-001: Parser detects and loads .xml files"""
        content = '<register_map module="test_module"><register name="reg1" access="RW"/></register_map>'
        xml_file = self.write_xml(content)

        result = self.parser.parse_file(xml_file)
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'test_module')

    # XML-INPUT-002: Module name extraction
    def test_xml_input_002_module_name(self):
        """XML-INPUT-002: Correctly extracts module attribute"""
        content = '<register_map module="my_module"></register_map>'
        xml_file = self.write_xml(content)

        result = self.parser.parse_file(xml_file)
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'my_module')

    # XML-INPUT-003: Hex base address parsing
    def test_xml_input_003_hex_address(self):
        """XML-INPUT-003: Parses hex string base address"""
        content = '<register_map module="test" base_addr="0x1000"></register_map>'
        xml_file = self.write_xml(content)

        result = self.parser.parse_file(xml_file)
        self.assertEqual(result['base_address'], 0x1000)

    # XML-INPUT-004: Decimal base address parsing
    def test_xml_input_004_decimal_address(self):
        """XML-INPUT-004: Parses decimal base address"""
        content = '<register_map module="test" base_addr="4096"></register_map>'
        xml_file = self.write_xml(content)

        result = self.parser.parse_file(xml_file)
        self.assertEqual(result['base_address'], 4096)

    # XML-INPUT-005: Register element parsing
    def test_xml_input_005_register_parsing(self):
        """XML-INPUT-005: Parses register elements with all attributes"""
        content = '''<register_map module="test">
            <register name="ctrl" addr="0x00" access="RW" width="32" description="Control register"/>
        </register_map>'''
        xml_file = self.write_xml(content)

        result = self.parser.parse_file(xml_file)
        self.assertEqual(len(result['registers']), 1)
        reg = result['registers'][0]
        self.assertEqual(reg['signal_name'], 'ctrl')
        self.assertEqual(reg['relative_address_int'], 0)
        self.assertEqual(reg['access_mode'], 'RW')
        self.assertEqual(reg['width'], 32)
        self.assertEqual(reg['description'], 'Control register')

    # XML-INPUT-006: Access mode parsing
    def test_xml_input_006_access_modes(self):
        """XML-INPUT-006: Handles RO, RW, WO (case-insensitive)"""
        content = '''<register_map module="test">
            <register name="r1" access="ro"/>
            <register name="r2" access="RW"/>
            <register name="r3" access="Wo"/>
        </register_map>'''
        xml_file = self.write_xml(content)

        result = self.parser.parse_file(xml_file)
        self.assertEqual(result['registers'][0]['access_mode'], 'RO')
        self.assertEqual(result['registers'][1]['access_mode'], 'RW')
        self.assertEqual(result['registers'][2]['access_mode'], 'WO')

    # XML-INPUT-007: Strobe signal attributes
    def test_xml_input_007_strobe_signals(self):
        """XML-INPUT-007: Parses r_strobe and w_strobe attributes"""
        content = '''<register_map module="test">
            <register name="r1" access="RW" r_strobe="true"/>
            <register name="r2" access="RW" w_strobe="true"/>
        </register_map>'''
        xml_file = self.write_xml(content)

        result = self.parser.parse_file(xml_file)
        self.assertTrue(result['registers'][0].get('read_strobe', False))
        self.assertTrue(result['registers'][1].get('write_strobe', False))

    # XML-INPUT-008: CDC configuration
    @unittest.skip("XML parser CDC parsing not yet implemented - existing issue")
    def test_xml_input_008_cdc_config(self):
        """XML-INPUT-008: Parses CDC configuration attributes"""
        content = '<register_map module="test" cdc_en="true" cdc_stages="3"><register name="r1" access="RW"/></register_map>'
        xml_file = self.write_xml(content)

        result = self.parser.parse_file(xml_file)
        self.assertTrue(result.get('cdc_enabled', False))
        self.assertEqual(result.get('cdc_stages', 2), 3)

    # XML-INPUT-009: Description parsing
    def test_xml_input_009_description(self):
        """XML-INPUT-009: Parses register description attribute"""
        content = '<register_map module="test"><register name="r1" access="RW" description="Test description"/></register_map>'
        xml_file = self.write_xml(content)

        result = self.parser.parse_file(xml_file)
        self.assertEqual(result['registers'][0]['description'], 'Test description')

    # XML-INPUT-010: Auto address assignment
    def test_xml_input_010_auto_address(self):
        """XML-INPUT-010: Assigns sequential addresses if addr omitted"""
        content = '''<register_map module="test">
            <register name="r1" access="RW"/>
            <register name="r2" access="RW"/>
            <register name="r3" access="RW"/>
        </register_map>'''
        xml_file = self.write_xml(content)

        result = self.parser.parse_file(xml_file)
        # Addresses should be sequential (0x00, 0x04, 0x08)
        self.assertEqual(result['registers'][0]['relative_address_int'], 0x00)
        self.assertEqual(result['registers'][1]['relative_address_int'], 0x04)
        self.assertEqual(result['registers'][2]['relative_address_int'], 0x08)

    # XML-INPUT-011: Invalid XML handling
    def test_xml_input_011_invalid_xml(self):
        """XML-INPUT-011: Returns None for malformed XML"""
        content = '<register_map module="test"><register name="r1" access="RW"'  # Missing closing tag
        xml_file = self.write_xml(content)

        result = self.parser.parse_file(xml_file)
        self.assertIsNone(result)

    # XML-INPUT-012: Missing module attribute
    def test_xml_input_012_missing_module(self):
        """XML-INPUT-012: Returns None when module attribute missing"""
        content = '<register_map><register name="r1" access="RW"/></register_map>'
        xml_file = self.write_xml(content)

        result = self.parser.parse_file(xml_file)
        self.assertIsNone(result)

    # XML-INPUT-013: Packed registers (subregisters)
    def test_xml_input_013_packed_registers(self):
        """XML-INPUT-013: Parses reg_name and bit_offset for subregisters"""
        content = '''<register_map module="test">
            <register name="flag_a" reg_name="ctrl" bit_offset="0" width="1"/>
            <register name="flag_b" reg_name="ctrl" bit_offset="1" width="1"/>
        </register_map>'''
        xml_file = self.write_xml(content)

        result = self.parser.parse_file(xml_file)
        # Should create one packed register with two fields
        packed_regs = [r for r in result['registers'] if r.get('is_packed')]
        self.assertEqual(len(packed_regs), 1)
        self.assertEqual(len(packed_regs[0]['fields']), 2)

    # XML-INPUT-014: Default values
    def test_xml_input_014_default_values(self):
        """XML-INPUT-014: Parses default attribute (hex and decimal)"""
        content = '''<register_map module="test">
            <register name="r1" access="RW" default="0x1234"/>
            <register name="r2" access="RW" default="42"/>
        </register_map>'''
        xml_file = self.write_xml(content)

        result = self.parser.parse_file(xml_file)
        self.assertEqual(result['registers'][0].get('default_value', 0), 0x1234)
        self.assertEqual(result['registers'][1].get('default_value', 0), 42)

    # XML-INPUT-015: Wide signals
    def test_xml_input_015_wide_signals(self):
        """XML-INPUT-015: Handles width > 32"""
        content = '<register_map module="test"><register name="wide_reg" access="RW" width="64"/></register_map>'
        xml_file = self.write_xml(content)

        result = self.parser.parse_file(xml_file)
        self.assertEqual(result['registers'][0]['width'], 64)


if __name__ == '__main__':
    unittest.main()
