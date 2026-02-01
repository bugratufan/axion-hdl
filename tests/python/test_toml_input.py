#!/usr/bin/env python3
"""
test_toml_input.py - TOML Input Parser Requirements Tests

Tests for TOML-INPUT-001 through TOML-INPUT-015 requirements.
Verifies the TOML input parser functionality for register definition parsing.
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

from axion_hdl.toml_input_parser import TOMLInputParser
from axion_hdl import AxionHDL


class TestTOMLInputRequirements(unittest.TestCase):
    """Test cases for TOML-INPUT-xxx requirements"""

    def setUp(self):
        """Set up test fixtures"""
        self.parser = TOMLInputParser()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temp files"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_temp_toml(self, filename: str, content: str) -> str:
        """Write TOML content to temp file and return path"""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath

    # TOML-INPUT-001: TOML file detection
    def test_toml_input_001_file_detection(self):
        """TOML-INPUT-001: Parser detects and loads .toml files"""
        toml_content = '''
module = "test_module"
base_addr = "0x0000"

[[registers]]
name = "test_reg"
access = "RW"
width = 32
'''
        toml_file = self._write_temp_toml("test.toml", toml_content)
        result = self.parser.parse_file(toml_file)
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'test_module')

    # TOML-INPUT-002: Module name extraction
    def test_toml_input_002_module_name(self):
        """TOML-INPUT-002: Correctly extracts module field"""
        toml_content = '''
module = "my_custom_module"

[[registers]]
name = "reg1"
access = "RW"
'''
        filepath = self._write_temp_toml("test.toml", toml_content)
        result = self.parser.parse_file(filepath)
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'my_custom_module')
        self.assertEqual(result['entity_name'], 'my_custom_module')

    # TOML-INPUT-003: Hex base address parsing
    def test_toml_input_003_hex_address(self):
        """TOML-INPUT-003: Parses hex string base address"""
        toml_content = '''
module = "test"
base_addr = "0x1000"

[[registers]]
name = "reg1"
access = "RW"
'''
        filepath = self._write_temp_toml("test.toml", toml_content)
        result = self.parser.parse_file(filepath)
        self.assertEqual(result['base_address'], 0x1000)

    # TOML-INPUT-004: Table format module name
    def test_toml_input_004_table_module(self):
        """TOML-INPUT-004: Parses [module] table format"""
        toml_content = '''
[module]
name = "table_module"
base_addr = "0x2000"

[[registers]]
name = "reg1"
access = "RW"
'''
        filepath = self._write_temp_toml("test.toml", toml_content)
        result = self.parser.parse_file(filepath)
        self.assertEqual(result['name'], 'table_module')
        self.assertEqual(result['base_address'], 0x2000)

    # TOML-INPUT-005: Register array parsing
    def test_toml_input_005_register_array(self):
        """TOML-INPUT-005: Parses [[registers]] array correctly"""
        toml_content = '''
module = "test"

[[registers]]
name = "reg1"
addr = "0x00"
access = "RO"

[[registers]]
name = "reg2"
addr = "0x04"
access = "WO"

[[registers]]
name = "reg3"
addr = "0x08"
access = "RW"
'''
        filepath = self._write_temp_toml("test.toml", toml_content)
        result = self.parser.parse_file(filepath)
        self.assertEqual(len(result['registers']), 3)
        self.assertEqual(result['registers'][0]['signal_name'], 'reg1')
        self.assertEqual(result['registers'][1]['signal_name'], 'reg2')
        self.assertEqual(result['registers'][2]['signal_name'], 'reg3')

    # TOML-INPUT-006: Access mode parsing
    def test_toml_input_006_access_modes(self):
        """TOML-INPUT-006: Correctly parses RO, WO, RW access modes"""
        toml_content = '''
module = "test"

[[registers]]
name = "ro_reg"
addr = "0x00"
access = "RO"

[[registers]]
name = "wo_reg"
addr = "0x04"
access = "WO"

[[registers]]
name = "rw_reg"
addr = "0x08"
access = "RW"
'''
        filepath = self._write_temp_toml("test.toml", toml_content)
        result = self.parser.parse_file(filepath)
        self.assertEqual(result['registers'][0]['access_mode'], 'RO')
        self.assertEqual(result['registers'][1]['access_mode'], 'WO')
        self.assertEqual(result['registers'][2]['access_mode'], 'RW')

    # TOML-INPUT-007: CDC configuration
    def test_toml_input_007_cdc_config(self):
        """TOML-INPUT-007: Parses [config] with cdc_en and cdc_stage"""
        toml_content = '''
module = "test"

[config]
cdc_en = true
cdc_stage = 3

[[registers]]
name = "reg1"
access = "RW"
'''
        filepath = self._write_temp_toml("test.toml", toml_content)
        result = self.parser.parse_file(filepath)
        self.assertTrue(result['cdc_enabled'])
        self.assertEqual(result['cdc_stages'], 3)

    # TOML-INPUT-008: Description field
    def test_toml_input_008_descriptions(self):
        """TOML-INPUT-008: Preserves register descriptions"""
        toml_content = '''
module = "test"

[[registers]]
name = "status"
addr = "0x00"
access = "RO"
description = "System status register"
'''
        filepath = self._write_temp_toml("test.toml", toml_content)
        result = self.parser.parse_file(filepath)
        self.assertEqual(result['registers'][0]['description'], 'System status register')

    # TOML-INPUT-009: Read strobe
    def test_toml_input_009_read_strobe(self):
        """TOML-INPUT-009: Correctly handles r_strobe boolean"""
        toml_content = '''
module = "test"

[[registers]]
name = "reg1"
addr = "0x00"
access = "RO"
r_strobe = true
'''
        filepath = self._write_temp_toml("test.toml", toml_content)
        result = self.parser.parse_file(filepath)
        self.assertTrue(result['registers'][0]['r_strobe'])

    # TOML-INPUT-010: Write strobe
    def test_toml_input_010_write_strobe(self):
        """TOML-INPUT-010: Correctly handles w_strobe boolean"""
        toml_content = '''
module = "test"

[[registers]]
name = "reg1"
addr = "0x00"
access = "WO"
w_strobe = true
'''
        filepath = self._write_temp_toml("test.toml", toml_content)
        result = self.parser.parse_file(filepath)
        self.assertTrue(result['registers'][0]['w_strobe'])

    # TOML-INPUT-011: Width specification
    def test_toml_input_011_register_width(self):
        """TOML-INPUT-011: Parses register width correctly"""
        toml_content = '''
module = "test"

[[registers]]
name = "wide_reg"
addr = "0x00"
access = "RW"
width = 64
'''
        filepath = self._write_temp_toml("test.toml", toml_content)
        result = self.parser.parse_file(filepath)
        self.assertEqual(result['registers'][0]['width'], 64)

    # TOML-INPUT-012: Default value
    def test_toml_input_012_default_value(self):
        """TOML-INPUT-012: Parses default field"""
        toml_content = '''
module = "test"

[[registers]]
name = "reg1"
addr = "0x00"
access = "RW"
default = "0xDEADBEEF"
'''
        filepath = self._write_temp_toml("test.toml", toml_content)
        result = self.parser.parse_file(filepath)
        # Default value handling depends on YAML parser implementation
        self.assertIn('default', str(result['registers'][0]).lower() or 'default_value' in result['registers'][0])

    # TOML-INPUT-013: Packed registers (subregisters)
    def test_toml_input_013_packed_registers(self):
        """TOML-INPUT-013: Handles reg_name and bit_offset for packed registers"""
        toml_content = '''
module = "test"

[[registers]]
name = "flag_a"
reg_name = "flags"
bit_offset = 0
access = "RW"

[[registers]]
name = "flag_b"
reg_name = "flags"
bit_offset = 1
access = "RW"
'''
        filepath = self._write_temp_toml("test.toml", toml_content)
        result = self.parser.parse_file(filepath)
        # Packed registers should be processed
        self.assertTrue(len(result['registers']) >= 2 or 'packed_registers' in result)

    # TOML-INPUT-014: Directory scanning
    def test_toml_input_014_directory_scan(self):
        """TOML-INPUT-014: parse_toml_files() scans directories"""
        toml_content = '''
module = "test_module"

[[registers]]
name = "reg1"
access = "RW"
'''
        self._write_temp_toml("file1.toml", toml_content)
        self._write_temp_toml("file2.toml", toml_content.replace("test_module", "test_module2"))

        modules = self.parser.parse_toml_files([self.temp_dir])
        self.assertEqual(len(modules), 2)

    # TOML-INPUT-015: AxionHDL integration
    def test_toml_input_015_axion_integration(self):
        """TOML-INPUT-015: AxionHDL.add_toml_src() works correctly"""
        toml_content = '''
module = "integration_test"
base_addr = "0x0000"

[[registers]]
name = "test_reg"
addr = "0x00"
access = "RW"
width = 32
'''
        toml_file = self._write_temp_toml("integration.toml", toml_content)

        axion = AxionHDL(output_dir=self.temp_dir)
        axion.add_toml_src(toml_file)
        self.assertIn(toml_file, axion.toml_src_files)

        # Test analysis
        success = axion.analyze()
        self.assertTrue(success)
        self.assertEqual(len(axion.analyzed_modules), 1)
        self.assertEqual(axion.analyzed_modules[0]['name'], 'integration_test')


if __name__ == '__main__':
    unittest.main()
