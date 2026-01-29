#!/usr/bin/env python3
"""
test_yaml_input.py - YAML Input Parser Requirements Tests

Tests for YAML-INPUT-001 through YAML-INPUT-015 requirements.
Verifies the YAML input parser functionality for register definition parsing.
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

from axion_hdl.yaml_input_parser import YAMLInputParser
from axion_hdl import AxionHDL


class TestYAMLInputRequirements(unittest.TestCase):
    """Test cases for YAML-INPUT-xxx requirements"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.parser = YAMLInputParser()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up temp files"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def _write_temp_yaml(self, filename: str, content: str) -> str:
        """Write YAML content to temp file and return path"""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath
    
    # YAML-INPUT-001: YAML file detection
    def test_yaml_input_001_file_detection(self):
        """YAML-INPUT-001: Parser detects and loads .yaml and .yml files"""
        yaml_content = """
module: test_module
base_addr: "0x0000"
registers:
  - name: test_reg
    access: RW
    width: 32
"""
        # Test .yaml extension
        yaml_file = self._write_temp_yaml("test.yaml", yaml_content)
        result = self.parser.parse_file(yaml_file)
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'test_module')
        
        # Test .yml extension
        yml_file = self._write_temp_yaml("test.yml", yaml_content)
        result = self.parser.parse_file(yml_file)
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'test_module')
    
    # YAML-INPUT-002: Module name extraction
    def test_yaml_input_002_module_name(self):
        """YAML-INPUT-002: Correctly extracts module field"""
        yaml_content = """
module: my_custom_module
registers:
  - name: reg1
    access: RW
"""
        filepath = self._write_temp_yaml("test.yaml", yaml_content)
        result = self.parser.parse_file(filepath)
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'my_custom_module')
        self.assertEqual(result['entity_name'], 'my_custom_module')
    
    # YAML-INPUT-003: Hex base address parsing
    def test_yaml_input_003_hex_address(self):
        """YAML-INPUT-003: Parses hex base address"""
        yaml_content = """
module: test
base_addr: "0x1000"
registers:
  - name: reg1
    access: RW
"""
        filepath = self._write_temp_yaml("test.yaml", yaml_content)
        result = self.parser.parse_file(filepath)
        self.assertEqual(result['base_address'], 0x1000)
    
    # YAML-INPUT-004: Decimal base address parsing
    def test_yaml_input_004_decimal_address(self):
        """YAML-INPUT-004: Parses decimal base address"""
        yaml_content = """
module: test
base_addr: 4096
registers:
  - name: reg1
    access: RW
"""
        filepath = self._write_temp_yaml("test.yaml", yaml_content)
        result = self.parser.parse_file(filepath)
        self.assertEqual(result['base_address'], 4096)
    
    # YAML-INPUT-005: Register list parsing
    def test_yaml_input_005_register_parsing(self):
        """YAML-INPUT-005: Parses registers array with all attributes"""
        yaml_content = """
module: test
registers:
  - name: status_reg
    addr: "0x00"
    access: RO
    width: 32
  - name: control_reg
    addr: "0x04"
    access: RW
    width: 32
"""
        filepath = self._write_temp_yaml("test.yaml", yaml_content)
        result = self.parser.parse_file(filepath)
        self.assertEqual(len(result['registers']), 2)
        self.assertEqual(result['registers'][0]['signal_name'], 'status_reg')
        self.assertEqual(result['registers'][1]['signal_name'], 'control_reg')
    
    # YAML-INPUT-006: Access mode support
    def test_yaml_input_006_access_modes(self):
        """YAML-INPUT-006: Handles RO, RW, WO (case-insensitive)"""
        yaml_content = """
module: test
registers:
  - name: ro_reg
    access: ro
  - name: rw_reg
    access: RW
  - name: wo_reg
    access: Wo
"""
        filepath = self._write_temp_yaml("test.yaml", yaml_content)
        result = self.parser.parse_file(filepath)
        self.assertEqual(result['registers'][0]['access_mode'], 'RO')
        self.assertEqual(result['registers'][1]['access_mode'], 'RW')
        self.assertEqual(result['registers'][2]['access_mode'], 'WO')
    
    # YAML-INPUT-007: Strobe signal parsing
    def test_yaml_input_007_strobe_signals(self):
        """YAML-INPUT-007: Parses r_strobe and w_strobe flags"""
        yaml_content = """
module: test
registers:
  - name: test_reg
    access: RW
    r_strobe: true
    w_strobe: true
"""
        filepath = self._write_temp_yaml("test.yaml", yaml_content)
        result = self.parser.parse_file(filepath)
        self.assertTrue(result['registers'][0]['r_strobe'])
        self.assertTrue(result['registers'][0]['w_strobe'])
    
    # YAML-INPUT-008: CDC configuration
    def test_yaml_input_008_cdc_config(self):
        """YAML-INPUT-008: Parses CDC configuration"""
        yaml_content = """
module: test
config:
  cdc_en: true
  cdc_stage: 4
registers:
  - name: reg1
    access: RW
"""
        filepath = self._write_temp_yaml("test.yaml", yaml_content)
        result = self.parser.parse_file(filepath)
        self.assertTrue(result['cdc_enabled'])
        self.assertEqual(result['cdc_stages'], 4)
    
    # YAML-INPUT-009: Description field
    def test_yaml_input_009_description(self):
        """YAML-INPUT-009: Parses register description"""
        yaml_content = """
module: test
registers:
  - name: status_reg
    access: RO
    description: Status register for system state
"""
        filepath = self._write_temp_yaml("test.yaml", yaml_content)
        result = self.parser.parse_file(filepath)
        self.assertEqual(result['registers'][0]['description'], 'Status register for system state')
    
    # YAML-INPUT-010: Auto address assignment
    def test_yaml_input_010_auto_address(self):
        """YAML-INPUT-010: Assigns sequential addresses if addr omitted"""
        yaml_content = """
module: test
registers:
  - name: reg1
    access: RW
  - name: reg2
    access: RW
  - name: reg3
    access: RW
"""
        filepath = self._write_temp_yaml("test.yaml", yaml_content)
        result = self.parser.parse_file(filepath)
        self.assertEqual(result['registers'][0]['relative_address_int'], 0)
        self.assertEqual(result['registers'][1]['relative_address_int'], 4)
        self.assertEqual(result['registers'][2]['relative_address_int'], 8)
    
    # YAML-INPUT-011: Invalid YAML handling
    def test_yaml_input_011_invalid_yaml(self):
        """YAML-INPUT-011: Returns None for malformed YAML"""
        yaml_content = """
module: test
registers
  - name: invalid
"""
        filepath = self._write_temp_yaml("test.yaml", yaml_content)
        result = self.parser.parse_file(filepath)
        self.assertIsNone(result)
    
    # YAML-INPUT-012: Missing module name
    def test_yaml_input_012_missing_module(self):
        """YAML-INPUT-012: Returns None when module field missing"""
        yaml_content = """
registers:
  - name: reg1
    access: RW
"""
        filepath = self._write_temp_yaml("test.yaml", yaml_content)
        result = self.parser.parse_file(filepath)
        self.assertIsNone(result)
    
    # YAML-INPUT-013: Packed register parsing
    def test_yaml_input_013_packed_registers(self):
        """YAML-INPUT-013: Parses reg_name and bit_offset for subregisters"""
        yaml_content = """
module: test
registers:
  - name: field1
    reg_name: control
    bit_offset: 0
    width: 8
    access: RW
  - name: field2
    reg_name: control
    bit_offset: 8
    width: 8
    access: RW
"""
        filepath = self._write_temp_yaml("test.yaml", yaml_content)
        result = self.parser.parse_file(filepath)
        # Should have one packed register
        packed = [r for r in result['registers'] if r.get('is_packed')]
        self.assertEqual(len(packed), 1)
        self.assertEqual(len(packed[0]['fields']), 2)
    
    # YAML-INPUT-014: Default value parsing
    def test_yaml_input_014_default_values(self):
        """YAML-INPUT-014: Parses default field (hex and decimal)"""
        yaml_content = """
module: test
registers:
  - name: reg1
    access: RW
    default: "0xFF"
  - name: reg2
    access: RW
    default: 100
"""
        filepath = self._write_temp_yaml("test.yaml", yaml_content)
        result = self.parser.parse_file(filepath)
        self.assertEqual(result['registers'][0]['default_value'], 0xFF)
        self.assertEqual(result['registers'][1]['default_value'], 100)
    
    # YAML-INPUT-015: Wide signal support
    def test_yaml_input_015_wide_signals(self):
        """YAML-INPUT-015: Handles width > 32"""
        yaml_content = """
module: test
registers:
  - name: wide_reg
    access: RW
    width: 64
"""
        filepath = self._write_temp_yaml("test.yaml", yaml_content)
        result = self.parser.parse_file(filepath)
        self.assertEqual(result['registers'][0]['width'], 64)


def run_yaml_input_tests():
    """Run all YAML input parser tests and return results"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestYAMLInputRequirements)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_yaml_input_tests()
    sys.exit(0 if success else 1)
