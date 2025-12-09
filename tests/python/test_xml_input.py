#!/usr/bin/env python3
"""
test_xml_input.py - XML Input Parser Requirements Tests

Tests for AXION-XML-001 through AXION-XML-015 requirements.
Verifies the XML input parser functionality for register definition parsing,
format compatibility, and round-trip testing.
"""

import os
import sys
import tempfile
import unittest
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from axion_hdl.xml_input_parser import XMLInputParser
from axion_hdl import AxionHDL


class TestXMLInputRequirements(unittest.TestCase):
    """Test cases for AXION-XML-xxx requirements"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.parser = XMLInputParser()
        self.temp_dir = tempfile.mkdtemp()
        self.xml_test_dir = project_root / "tests" / "xml"
    
    def tearDown(self):
        """Clean up temp files"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _write_temp_xml(self, filename: str, content: str) -> str:
        """Write XML content to temp file and return path"""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath
    
    # =========================================================================
    # AXION-XML-001: XML File Detection and Loading
    # =========================================================================
    def test_axion_xml_001_file_detection(self):
        """AXION-XML-001: XML file detection and loading"""
        # Create test XML files
        xml1 = '''<?xml version="1.0"?>
<register_map module="test1" base_addr="0x0000">
    <register name="reg1" access="RO" addr="0x00"/>
</register_map>'''
        xml2 = '''<?xml version="1.0"?>
<register_map module="test2" base_addr="0x1000">
    <register name="reg2" access="RW" addr="0x00"/>
</register_map>'''
        
        # Create subdirectory
        subdir = os.path.join(self.temp_dir, "subdir")
        os.makedirs(subdir)
        
        self._write_temp_xml("module1.xml", xml1)
        with open(os.path.join(subdir, "module2.xml"), 'w') as f:
            f.write(xml2)
        
        # Also create a non-XML file that should be ignored
        with open(os.path.join(self.temp_dir, "readme.txt"), 'w') as f:
            f.write("This should be ignored")
        
        modules = self.parser.parse_xml_files([self.temp_dir])
        self.assertEqual(len(modules), 2)
        module_names = [m['name'] for m in modules]
        self.assertIn('test1', module_names)
        self.assertIn('test2', module_names)
    
    # =========================================================================
    # AXION-XML-002: Module Name Extraction
    # =========================================================================
    def test_axion_xml_002_module_name(self):
        """AXION-XML-002: Module name extraction"""
        xml = '''<?xml version="1.0"?>
<register_map module="my_test_module_123" base_addr="0x0000">
    <register name="reg" access="RO" addr="0x00"/>
</register_map>'''
        filepath = self._write_temp_xml("module_name_test.xml", xml)
        result = self.parser.parse_file(filepath)
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'my_test_module_123')
        self.assertEqual(result['entity_name'], 'my_test_module_123')
    
    def test_axion_xml_002_missing_module_name(self):
        """AXION-XML-002: Missing module name should return None"""
        xml = '''<?xml version="1.0"?>
<register_map base_addr="0x0000">
    <register name="reg" access="RO" addr="0x00"/>
</register_map>'''
        filepath = self._write_temp_xml("no_module.xml", xml)
        result = self.parser.parse_file(filepath)
        self.assertIsNone(result)
    
    # =========================================================================
    # AXION-XML-003: Base Address Parsing
    # =========================================================================
    def test_axion_xml_003_hex_address(self):
        """AXION-XML-003: Parse hex base address"""
        xml = '''<?xml version="1.0"?>
<register_map module="test" base_addr="0x1000">
    <register name="reg" access="RO" addr="0x00"/>
</register_map>'''
        filepath = self._write_temp_xml("hex_addr.xml", xml)
        result = self.parser.parse_file(filepath)
        self.assertEqual(result['base_address'], 0x1000)
    
    def test_axion_xml_003_decimal_address(self):
        """AXION-XML-003: Parse decimal base address"""
        xml = '''<?xml version="1.0"?>
<register_map module="test" base_addr="4096">
    <register name="reg" access="RO" addr="0x00"/>
</register_map>'''
        filepath = self._write_temp_xml("dec_addr.xml", xml)
        result = self.parser.parse_file(filepath)
        self.assertEqual(result['base_address'], 4096)
    
    def test_axion_xml_003_default_address(self):
        """AXION-XML-003: Default base address when omitted"""
        xml = '''<?xml version="1.0"?>
<register_map module="test">
    <register name="reg" access="RO" addr="0x00"/>
</register_map>'''
        filepath = self._write_temp_xml("no_addr.xml", xml)
        result = self.parser.parse_file(filepath)
        self.assertEqual(result['base_address'], 0)
    
    # =========================================================================
    # AXION-XML-004: Register Definition Parsing
    # =========================================================================
    def test_axion_xml_004_register_parsing(self):
        """AXION-XML-004: Parse register definitions"""
        xml = '''<?xml version="1.0"?>
<register_map module="test">
    <register name="reg_a" access="RO" addr="0x00" width="32"/>
    <register name="reg_b" access="RW" addr="0x04" width="32"/>
    <register name="reg_c" access="WO" addr="0x08" width="32"/>
</register_map>'''
        filepath = self._write_temp_xml("multi_reg.xml", xml)
        result = self.parser.parse_file(filepath)
        self.assertEqual(len(result['registers']), 3)
        
        # Check order is preserved
        self.assertEqual(result['registers'][0]['name'], 'reg_a')
        self.assertEqual(result['registers'][1]['name'], 'reg_b')
        self.assertEqual(result['registers'][2]['name'], 'reg_c')
    
    # =========================================================================
    # AXION-XML-005: Access Mode Support
    # =========================================================================
    def test_axion_xml_005_access_modes(self):
        """AXION-XML-005: Access mode support (RO, RW, WO)"""
        xml = '''<?xml version="1.0"?>
<register_map module="test">
    <register name="ro_reg" access="RO" addr="0x00"/>
    <register name="rw_reg" access="RW" addr="0x04"/>
    <register name="wo_reg" access="WO" addr="0x08"/>
</register_map>'''
        filepath = self._write_temp_xml("access_modes.xml", xml)
        result = self.parser.parse_file(filepath)
        
        access_map = {r['name']: r['access_mode'] for r in result['registers']}
        self.assertEqual(access_map['ro_reg'], 'RO')
        self.assertEqual(access_map['rw_reg'], 'RW')
        self.assertEqual(access_map['wo_reg'], 'WO')
    
    def test_axion_xml_005_case_insensitive(self):
        """AXION-XML-005: Case-insensitive access mode parsing"""
        xml = '''<?xml version="1.0"?>
<register_map module="test">
    <register name="reg" access="ro" addr="0x00"/>
</register_map>'''
        filepath = self._write_temp_xml("lowercase.xml", xml)
        result = self.parser.parse_file(filepath)
        self.assertEqual(result['registers'][0]['access_mode'], 'RO')
    
    # =========================================================================
    # AXION-XML-006: Strobe Signal Support
    # =========================================================================
    def test_axion_xml_006_strobe_signals(self):
        """AXION-XML-006: Strobe signal support"""
        xml = '''<?xml version="1.0"?>
<register_map module="test">
    <register name="r_strobe_reg" access="RO" addr="0x00" r_strobe="true"/>
    <register name="w_strobe_reg" access="WO" addr="0x04" w_strobe="true"/>
    <register name="both_strobe" access="RW" addr="0x08" r_strobe="true" w_strobe="true"/>
    <register name="no_strobe" access="RW" addr="0x0C"/>
</register_map>'''
        filepath = self._write_temp_xml("strobes.xml", xml)
        result = self.parser.parse_file(filepath)
        
        strobe_map = {r['name']: (r['r_strobe'], r['w_strobe']) for r in result['registers']}
        self.assertEqual(strobe_map['r_strobe_reg'], (True, False))
        self.assertEqual(strobe_map['w_strobe_reg'], (False, True))
        self.assertEqual(strobe_map['both_strobe'], (True, True))
        self.assertEqual(strobe_map['no_strobe'], (False, False))
    
    # =========================================================================
    # AXION-XML-007: CDC Configuration Parsing
    # =========================================================================
    def test_axion_xml_007_cdc_config(self):
        """AXION-XML-007: CDC configuration parsing"""
        xml = '''<?xml version="1.0"?>
<register_map module="test">
    <config cdc_en="true" cdc_stage="3"/>
    <register name="reg" access="RO" addr="0x00"/>
</register_map>'''
        filepath = self._write_temp_xml("cdc_config.xml", xml)
        result = self.parser.parse_file(filepath)
        self.assertTrue(result['cdc_enabled'])
        self.assertEqual(result['cdc_stages'], 3)
    
    def test_axion_xml_007_cdc_default(self):
        """AXION-XML-007: CDC default when omitted"""
        xml = '''<?xml version="1.0"?>
<register_map module="test">
    <register name="reg" access="RO" addr="0x00"/>
</register_map>'''
        filepath = self._write_temp_xml("no_cdc.xml", xml)
        result = self.parser.parse_file(filepath)
        self.assertFalse(result['cdc_enabled'])
    
    # =========================================================================
    # AXION-XML-008: Register Description Support
    # =========================================================================
    def test_axion_xml_008_descriptions(self):
        """AXION-XML-008: Register description support"""
        xml = '''<?xml version="1.0"?>
<register_map module="test">
    <register name="reg" access="RO" addr="0x00" description="Test register description"/>
</register_map>'''
        filepath = self._write_temp_xml("description.xml", xml)
        result = self.parser.parse_file(filepath)
        self.assertEqual(result['registers'][0]['description'], 'Test register description')
    
    # =========================================================================
    # AXION-XML-009: Address Auto-Assignment
    # =========================================================================
    def test_axion_xml_009_auto_address(self):
        """AXION-XML-009: Address auto-assignment"""
        xml = '''<?xml version="1.0"?>
<register_map module="test">
    <register name="reg_a" access="RO"/>
    <register name="reg_b" access="RW"/>
    <register name="reg_c" access="WO"/>
</register_map>'''
        filepath = self._write_temp_xml("auto_addr.xml", xml)
        result = self.parser.parse_file(filepath)
        
        # Should auto-assign sequential addresses
        addresses = [r['relative_address_int'] for r in result['registers']]
        self.assertEqual(addresses, [0, 4, 8])
    
    # =========================================================================
    # AXION-XML-010: Error Handling
    # =========================================================================
    def test_axion_xml_010_invalid_xml(self):
        """AXION-XML-010: Invalid XML syntax handling"""
        invalid_xml = '''<?xml version="1.0"?>
<register_map module="test">
    <register name="reg" access="RO" addr="0x00"
</register_map>'''  # Missing closing >
        filepath = self._write_temp_xml("invalid.xml", invalid_xml)
        result = self.parser.parse_file(filepath)
        self.assertIsNone(result)
    
    def test_axion_xml_010_file_not_found(self):
        """AXION-XML-010: File not found handling"""
        result = self.parser.parse_file("/nonexistent/file.xml")
        self.assertIsNone(result)
    
    # =========================================================================
    # AXION-XML-011: CLI Integration
    # =========================================================================
    def test_axion_xml_011_cli_integration(self):
        """AXION-XML-011: CLI integration with AxionHDL"""
        xml = '''<?xml version="1.0"?>
<register_map module="cli_test" base_addr="0x0000">
    <register name="reg" access="RO" addr="0x00"/>
</register_map>'''
        self._write_temp_xml("cli_test.xml", xml)
        
        output_dir = os.path.join(self.temp_dir, "output")
        axion = AxionHDL(output_dir=output_dir)
        axion.add_xml_src(self.temp_dir)
        success = axion.analyze()
        
        self.assertTrue(success)
        self.assertEqual(len(axion.analyzed_modules), 1)
        self.assertEqual(axion.analyzed_modules[0]['name'], 'cli_test')
    
    # =========================================================================
    # AXION-XML-012: Output Equivalence
    # =========================================================================
    def test_axion_xml_012_output_equivalence(self):
        """AXION-XML-012: Output equivalence test"""
        xml = '''<?xml version="1.0"?>
<register_map module="equiv_test" base_addr="0x0000">
    <register name="status" access="RO" addr="0x00" description="Status"/>
    <register name="control" access="WO" addr="0x04" w_strobe="true"/>
    <register name="config" access="RW" addr="0x08"/>
</register_map>'''
        self._write_temp_xml("equiv_test.xml", xml)
        
        output_dir = os.path.join(self.temp_dir, "output")
        axion = AxionHDL(output_dir=output_dir)
        axion.add_xml_src(self.temp_dir)
        axion.analyze()
        
        # Generate all outputs
        axion.generate_all()
        
        # Check outputs exist
        self.assertTrue(os.path.exists(os.path.join(output_dir, "equiv_test_axion_reg.vhd")))
        self.assertTrue(os.path.exists(os.path.join(output_dir, "equiv_test_regs.h")))
        self.assertTrue(os.path.exists(os.path.join(output_dir, "equiv_test_regs.xml")))
        self.assertTrue(os.path.exists(os.path.join(output_dir, "register_map.md")))
    
    # =========================================================================
    # AXION-XML-013: XML Generator Compatibility
    # =========================================================================
    def test_axion_xml_013_generator_compatibility(self):
        """AXION-XML-013: Parse XML generated by XMLGenerator (SPIRIT format)"""
        # This is a simplified version of what XMLGenerator produces
        spirit_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<spirit:component xmlns:spirit="http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5">
    <spirit:vendor>axion</spirit:vendor>
    <spirit:library>user</spirit:library>
    <spirit:name>generated_module</spirit:name>
    <spirit:version>1.0</spirit:version>
    <spirit:memoryMaps>
        <spirit:memoryMap>
            <spirit:name>register_map</spirit:name>
            <spirit:addressBlock>
                <spirit:name>registers</spirit:name>
                <spirit:baseAddress>0x0</spirit:baseAddress>
                <spirit:range>8</spirit:range>
                <spirit:width>32</spirit:width>
                <spirit:register r_strobe="true">
                    <spirit:name>status_reg</spirit:name>
                    <spirit:addressOffset>0x00</spirit:addressOffset>
                    <spirit:size>32</spirit:size>
                    <spirit:access>read-only</spirit:access>
                </spirit:register>
            </spirit:addressBlock>
        </spirit:memoryMap>
    </spirit:memoryMaps>
</spirit:component>'''
        filepath = self._write_temp_xml("spirit_format.xml", spirit_xml)
        result = self.parser.parse_file(filepath)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'generated_module')
        self.assertEqual(len(result['registers']), 1)
        self.assertEqual(result['registers'][0]['access_mode'], 'RO')
    
    # =========================================================================
    # AXION-XML-014: Round-trip Integrity
    # =========================================================================
    def test_axion_xml_014_roundtrip_integrity(self):
        """AXION-XML-014: Round-trip test (parse -> generate -> parse)"""
        # Start with simple XML
        xml = '''<?xml version="1.0"?>
<register_map module="roundtrip_test" base_addr="0x0000">
    <register name="reg_a" access="RO" addr="0x00" description="Test A"/>
    <register name="reg_b" access="RW" addr="0x04" r_strobe="true"/>
</register_map>'''
        self._write_temp_xml("roundtrip.xml", xml)
        
        output_dir = os.path.join(self.temp_dir, "output")
        
        # First pass: parse XML and generate
        axion1 = AxionHDL(output_dir=output_dir)
        axion1.add_xml_src(self.temp_dir)
        axion1.analyze()
        axion1.generate_xml()
        
        original_modules = axion1.analyzed_modules.copy()
        
        # Second pass: parse the generated XML
        parser2 = XMLInputParser()
        generated_file = os.path.join(output_dir, "roundtrip_test_regs.xml")
        result = parser2.parse_file(generated_file)
        
        # Compare key data
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], original_modules[0]['name'])
        self.assertEqual(len(result['registers']), len(original_modules[0]['registers']))
    
    # =========================================================================
    # AXION-XML-015: Unified Attribute Naming
    # =========================================================================
    def test_axion_xml_015_unified_naming(self):
        """AXION-XML-015: Unified attribute naming between parser and generator"""
        xml = '''<?xml version="1.0"?>
<register_map module="naming_test" base_addr="0x0000">
    <config cdc_en="true" cdc_stage="2"/>
    <register name="strobe_reg" access="RW" addr="0x00" r_strobe="true" w_strobe="true"/>
</register_map>'''
        self._write_temp_xml("naming.xml", xml)
        
        output_dir = os.path.join(self.temp_dir, "output")
        axion = AxionHDL(output_dir=output_dir)
        axion.add_xml_src(self.temp_dir)
        axion.analyze()
        axion.generate_xml()
        
        # Read generated XML and check attributes are present
        generated_file = os.path.join(output_dir, "naming_test_regs.xml")
        with open(generated_file, 'r') as f:
            content = f.read()
        
        # Check strobe attributes are in generated XML
        self.assertIn('r_strobe="true"', content)
        self.assertIn('w_strobe="true"', content)


def run_xml_input_tests():
    """Run all XML input parser tests and return results"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestXMLInputRequirements)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_xml_input_tests()
    sys.exit(0 if success else 1)
