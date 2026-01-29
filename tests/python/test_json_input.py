#!/usr/bin/env python3
"""
test_json_input.py - JSON Input Parser Requirements Tests

Tests for JSON-INPUT-001 through JSON-INPUT-015 requirements.
Verifies the JSON input parser functionality for register definition parsing.
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from axion_hdl.json_input_parser import JSONInputParser
from axion_hdl import AxionHDL


class TestJSONInputRequirements(unittest.TestCase):
    """Test cases for JSON-INPUT-xxx requirements"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.parser = JSONInputParser()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up temp files"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def _write_temp_json(self, filename: str, content: str) -> str:
        """Write JSON content to temp file and return path"""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath
    
    # JSON-INPUT-001: JSON file detection
    def test_json_input_001_file_detection(self):
        """JSON-INPUT-001: Parser detects and loads .json files"""
        json_content = '''
{
  "module": "test_module",
  "base_addr": "0x0000",
  "registers": [
    {"name": "test_reg", "access": "RW", "width": 32}
  ]
}
'''
        json_file = self._write_temp_json("test.json", json_content)
        result = self.parser.parse_file(json_file)
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'test_module')
    
    # JSON-INPUT-002: Module name extraction
    def test_json_input_002_module_name(self):
        """JSON-INPUT-002: Correctly extracts module field"""
        json_content = '''
{
  "module": "my_custom_module",
  "registers": [{"name": "reg1", "access": "RW"}]
}
'''
        filepath = self._write_temp_json("test.json", json_content)
        result = self.parser.parse_file(filepath)
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'my_custom_module')
        self.assertEqual(result['entity_name'], 'my_custom_module')
    
    # JSON-INPUT-003: Hex base address parsing
    def test_json_input_003_hex_address(self):
        """JSON-INPUT-003: Parses hex string base address"""
        json_content = '''
{
  "module": "test",
  "base_addr": "0x1000",
  "registers": [{"name": "reg1", "access": "RW"}]
}
'''
        filepath = self._write_temp_json("test.json", json_content)
        result = self.parser.parse_file(filepath)
        self.assertEqual(result['base_address'], 0x1000)
    
    # JSON-INPUT-004: Numeric base address parsing
    def test_json_input_004_numeric_address(self):
        """JSON-INPUT-004: Parses numeric base address"""
        json_content = '''
{
  "module": "test",
  "base_addr": 4096,
  "registers": [{"name": "reg1", "access": "RW"}]
}
'''
        filepath = self._write_temp_json("test.json", json_content)
        result = self.parser.parse_file(filepath)
        self.assertEqual(result['base_address'], 4096)
    
    # JSON-INPUT-005: Register array parsing
    def test_json_input_005_register_parsing(self):
        """JSON-INPUT-005: Parses registers array with all attributes"""
        json_content = '''
{
  "module": "test",
  "registers": [
    {"name": "status_reg", "addr": "0x00", "access": "RO", "width": 32},
    {"name": "control_reg", "addr": "0x04", "access": "RW", "width": 32}
  ]
}
'''
        filepath = self._write_temp_json("test.json", json_content)
        result = self.parser.parse_file(filepath)
        self.assertEqual(len(result['registers']), 2)
        self.assertEqual(result['registers'][0]['signal_name'], 'status_reg')
        self.assertEqual(result['registers'][1]['signal_name'], 'control_reg')
    
    # JSON-INPUT-006: Access mode support
    def test_json_input_006_access_modes(self):
        """JSON-INPUT-006: Handles RO, RW, WO (case-insensitive)"""
        json_content = '''
{
  "module": "test",
  "registers": [
    {"name": "ro_reg", "access": "ro"},
    {"name": "rw_reg", "access": "RW"},
    {"name": "wo_reg", "access": "Wo"}
  ]
}
'''
        filepath = self._write_temp_json("test.json", json_content)
        result = self.parser.parse_file(filepath)
        self.assertEqual(result['registers'][0]['access_mode'], 'RO')
        self.assertEqual(result['registers'][1]['access_mode'], 'RW')
        self.assertEqual(result['registers'][2]['access_mode'], 'WO')
    
    # JSON-INPUT-007: Strobe signal parsing
    def test_json_input_007_strobe_signals(self):
        """JSON-INPUT-007: Parses r_strobe and w_strobe boolean fields"""
        json_content = '''
{
  "module": "test",
  "registers": [
    {"name": "test_reg", "access": "RW", "r_strobe": true, "w_strobe": true}
  ]
}
'''
        filepath = self._write_temp_json("test.json", json_content)
        result = self.parser.parse_file(filepath)
        self.assertTrue(result['registers'][0]['r_strobe'])
        self.assertTrue(result['registers'][0]['w_strobe'])
    
    # JSON-INPUT-008: CDC configuration
    def test_json_input_008_cdc_config(self):
        """JSON-INPUT-008: Parses CDC configuration"""
        json_content = '''
{
  "module": "test",
  "config": {"cdc_en": true, "cdc_stage": 4},
  "registers": [{"name": "reg1", "access": "RW"}]
}
'''
        filepath = self._write_temp_json("test.json", json_content)
        result = self.parser.parse_file(filepath)
        self.assertTrue(result['cdc_enabled'])
        self.assertEqual(result['cdc_stages'], 4)
    
    # JSON-INPUT-009: Description field
    def test_json_input_009_description(self):
        """JSON-INPUT-009: Parses register description"""
        json_content = '''
{
  "module": "test",
  "registers": [
    {"name": "status_reg", "access": "RO", "description": "Status register for system state"}
  ]
}
'''
        filepath = self._write_temp_json("test.json", json_content)
        result = self.parser.parse_file(filepath)
        self.assertEqual(result['registers'][0]['description'], 'Status register for system state')
    
    # JSON-INPUT-010: Auto address assignment
    def test_json_input_010_auto_address(self):
        """JSON-INPUT-010: Assigns sequential addresses if addr omitted"""
        json_content = '''
{
  "module": "test",
  "registers": [
    {"name": "reg1", "access": "RW"},
    {"name": "reg2", "access": "RW"},
    {"name": "reg3", "access": "RW"}
  ]
}
'''
        filepath = self._write_temp_json("test.json", json_content)
        result = self.parser.parse_file(filepath)
        self.assertEqual(result['registers'][0]['relative_address_int'], 0)
        self.assertEqual(result['registers'][1]['relative_address_int'], 4)
        self.assertEqual(result['registers'][2]['relative_address_int'], 8)
    
    # JSON-INPUT-011: Invalid JSON handling
    def test_json_input_011_invalid_json(self):
        """JSON-INPUT-011: Returns None for malformed JSON"""
        json_content = '''
{
  "module": "test",
  "registers": [
    {"name": "invalid"
  ]
}
'''
        filepath = self._write_temp_json("test.json", json_content)
        result = self.parser.parse_file(filepath)
        self.assertIsNone(result)
    
    # JSON-INPUT-012: Missing module name
    def test_json_input_012_missing_module(self):
        """JSON-INPUT-012: Returns None when module field missing"""
        json_content = '''
{
  "registers": [{"name": "reg1", "access": "RW"}]
}
'''
        filepath = self._write_temp_json("test.json", json_content)
        result = self.parser.parse_file(filepath)
        self.assertIsNone(result)
    
    # JSON-INPUT-013: Packed register parsing
    def test_json_input_013_packed_registers(self):
        """JSON-INPUT-013: Parses reg_name and bit_offset for subregisters"""
        json_content = '''
{
  "module": "test",
  "registers": [
    {"name": "field1", "reg_name": "control", "bit_offset": 0, "width": 8, "access": "RW"},
    {"name": "field2", "reg_name": "control", "bit_offset": 8, "width": 8, "access": "RW"}
  ]
}
'''
        filepath = self._write_temp_json("test.json", json_content)
        result = self.parser.parse_file(filepath)
        packed = [r for r in result['registers'] if r.get('is_packed')]
        self.assertEqual(len(packed), 1)
        self.assertEqual(len(packed[0]['fields']), 2)
    
    # JSON-INPUT-014: Default value parsing
    def test_json_input_014_default_values(self):
        """JSON-INPUT-014: Parses default field (hex string and number)"""
        json_content = '''
{
  "module": "test",
  "registers": [
    {"name": "reg1", "access": "RW", "default": "0xFF"},
    {"name": "reg2", "access": "RW", "default": 100}
  ]
}
'''
        filepath = self._write_temp_json("test.json", json_content)
        result = self.parser.parse_file(filepath)
        self.assertEqual(result['registers'][0]['default_value'], 0xFF)
        self.assertEqual(result['registers'][1]['default_value'], 100)
    
    # JSON-INPUT-015: Wide signal support
    def test_json_input_015_wide_signals(self):
        """JSON-INPUT-015: Handles width > 32"""
        json_content = '''
{
  "module": "test",
  "registers": [{"name": "wide_reg", "access": "RW", "width": 64}]
}
'''
        filepath = self._write_temp_json("test.json", json_content)
        result = self.parser.parse_file(filepath)
        self.assertEqual(result['registers'][0]['width'], 64)


def run_json_input_tests():
    """Run all JSON input parser tests and return results"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestJSONInputRequirements)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_json_input_tests()
    sys.exit(0 if success else 1)
