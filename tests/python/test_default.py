#!/usr/bin/env python3
"""
test_default.py - DEFAULT Attribute Tests

Tests for Issue #3: DEFAULT attribute for register reset values.
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

from axion_hdl.parser import VHDLParser
from axion_hdl.annotation_parser import AnnotationParser


class TestDefaultRequirements(unittest.TestCase):
    """Test cases for DEF-xxx requirements"""
    
    def setUp(self):
        self.parser = VHDLParser()
        self.annotation_parser = AnnotationParser()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _write_temp_vhdl(self, filename: str, content: str) -> str:
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath
    
    # =========================================================================
    # DEF-001: Parse DEFAULT hex value
    # =========================================================================
    def test_def_001_parse_hex_default(self):
        """DEF-001: Parse DEFAULT hex value"""
        attrs = self.annotation_parser.parse_attributes("RW DEFAULT=0xDEADBEEF")
        self.assertEqual(attrs.get('default_value'), 0xDEADBEEF)
    
    def test_def_001_parse_hex_lower(self):
        """DEF-001: Parse DEFAULT hex lowercase"""
        attrs = self.annotation_parser.parse_attributes("RW DEFAULT=0xdeadbeef")
        self.assertEqual(attrs.get('default_value'), 0xDEADBEEF)
    
    # =========================================================================
    # DEF-002: Parse DEFAULT decimal value  
    # =========================================================================
    def test_def_002_parse_decimal_default(self):
        """DEF-002: Parse DEFAULT decimal value"""
        attrs = self.annotation_parser.parse_attributes("RW DEFAULT=100")
        self.assertEqual(attrs.get('default_value'), 100)
    
    def test_def_002_parse_zero(self):
        """DEF-002: Parse DEFAULT=0"""
        attrs = self.annotation_parser.parse_attributes("RW DEFAULT=0")
        self.assertEqual(attrs.get('default_value'), 0)
    
    # =========================================================================
    # DEF-003: Validate default fits width
    # =========================================================================
    def test_def_003_register_has_default(self):
        """DEF-003: Register data includes default_value"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;

entity test_module is
end entity;

architecture rtl of test_module is
    signal config : std_logic_vector(31 downto 0);  -- @axion RW DEFAULT=0xDEADBEEF
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("test.vhd", vhdl)
        result = self.parser._parse_vhdl_file(filepath)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result['registers']), 1)
        self.assertEqual(result['registers'][0]['default_value'], 0xDEADBEEF)
    
    # =========================================================================
    # DEF-004: Default to 0 if not specified
    # =========================================================================
    def test_def_004_default_zero_when_missing(self):
        """DEF-004: Default to 0 if not specified"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;

entity test_module is
end entity;

architecture rtl of test_module is
    signal status : std_logic_vector(31 downto 0);  -- @axion RO
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("test.vhd", vhdl)
        result = self.parser._parse_vhdl_file(filepath)
        
        self.assertEqual(result['registers'][0]['default_value'], 0)
    
    # =========================================================================
    # DEF-009: Combine subregister defaults
    # =========================================================================
    def test_def_009_combine_subregister_defaults(self):
        """DEF-009: Combine subregister defaults into register default"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;

entity test_module is
end entity;

architecture rtl of test_module is
    signal enable : std_logic;  -- @axion RW ADDR=0x00 REG_NAME=control BIT_OFFSET=0 DEFAULT=1
    signal mode : std_logic_vector(1 downto 0);  -- @axion RW ADDR=0x00 REG_NAME=control BIT_OFFSET=1 DEFAULT=2
    signal prescaler : std_logic_vector(7 downto 0);  -- @axion RW ADDR=0x00 REG_NAME=control BIT_OFFSET=3 DEFAULT=10
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("test.vhd", vhdl)
        result = self.parser._parse_vhdl_file(filepath)
        
        self.assertEqual(len(result['packed_registers']), 1)
        packed_reg = result['packed_registers'][0]
        
        # Calculate expected: enable[0]=1, mode[2:1]=2, prescaler[10:3]=10
        # 1 | (2 << 1) | (10 << 3) = 1 + 4 + 80 = 85 = 0x55
        expected = 1 | (2 << 1) | (10 << 3)
        self.assertEqual(packed_reg['default_value'], expected)
    
    def test_def_009_field_defaults_stored(self):
        """DEF-009: Each field stores its own default"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;

entity test_module is
end entity;

architecture rtl of test_module is
    signal flag_a : std_logic;  -- @axion RW ADDR=0x00 REG_NAME=status BIT_OFFSET=0 DEFAULT=1
    signal flag_b : std_logic;  -- @axion RW ADDR=0x00 REG_NAME=status BIT_OFFSET=1 DEFAULT=0
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("test.vhd", vhdl)
        result = self.parser._parse_vhdl_file(filepath)
        
        fields = result['packed_registers'][0]['fields']
        self.assertEqual(len(fields), 2)
        self.assertEqual(fields[0]['default_value'], 1)
        self.assertEqual(fields[1]['default_value'], 0)
    
    # =========================================================================
    # DEF-010: Backward compatibility
    # =========================================================================
    def test_def_010_backward_compatibility(self):
        """DEF-010: Existing annotations without DEFAULT still work"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;

entity test_module is
end entity;

architecture rtl of test_module is
    signal old_reg : std_logic_vector(31 downto 0);  -- @axion RW ADDR=0x00
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("test.vhd", vhdl)
        result = self.parser._parse_vhdl_file(filepath)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result['registers']), 1)
        self.assertEqual(result['registers'][0]['default_value'], 0)
    
    # =========================================================================
    # Additional tests
    # =========================================================================
    def test_single_bit_default(self):
        """Single bit std_logic with DEFAULT=1"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;

entity test_module is
end entity;

architecture rtl of test_module is
    signal enable : std_logic;  -- @axion RW DEFAULT=1
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("test.vhd", vhdl)
        result = self.parser._parse_vhdl_file(filepath)
        
        self.assertEqual(result['registers'][0]['default_value'], 1)
        self.assertEqual(result['registers'][0]['signal_width'], 1)


def run_default_tests():
    """Run all default attribute tests and return results"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestDefaultRequirements)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_default_tests()
    sys.exit(0 if success else 1)
