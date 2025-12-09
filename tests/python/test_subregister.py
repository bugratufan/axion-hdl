#!/usr/bin/env python3
"""
test_subregister.py - Subregister Support Tests

Tests for Issue #2: REG_NAME and BIT_OFFSET attributes for bit field packing.
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
from axion_hdl.bit_field_manager import BitFieldManager, BitOverlapError, BitField


class TestSubregisterRequirements(unittest.TestCase):
    """Test cases for SUB-xxx requirements"""
    
    def setUp(self):
        self.parser = VHDLParser()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _write_temp_vhdl(self, filename: str, content: str) -> str:
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath
    
    # =========================================================================
    # SUB-001: Parse REG_NAME attribute
    # =========================================================================
    def test_sub_001_parse_reg_name(self):
        """SUB-001: Parse REG_NAME attribute"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;

entity test_module is
end entity;

architecture rtl of test_module is
    signal enable : std_logic;  -- @axion RW ADDR=0x00 REG_NAME=control BIT_OFFSET=0
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("test.vhd", vhdl)
        result = self.parser._parse_vhdl_file(filepath)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result['packed_registers']), 1)
        self.assertEqual(result['packed_registers'][0]['reg_name'], 'control')
    
    # =========================================================================
    # SUB-002: Parse BIT_OFFSET attribute
    # =========================================================================
    def test_sub_002_parse_bit_offset(self):
        """SUB-002: Parse BIT_OFFSET attribute"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;

entity test_module is
end entity;

architecture rtl of test_module is
    signal enable : std_logic;  -- @axion RW ADDR=0x00 REG_NAME=control BIT_OFFSET=0
    signal mode : std_logic_vector(1 downto 0);  -- @axion RW ADDR=0x00 REG_NAME=control BIT_OFFSET=1
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("test.vhd", vhdl)
        result = self.parser._parse_vhdl_file(filepath)
        
        fields = result['packed_registers'][0]['fields']
        self.assertEqual(len(fields), 2)
        self.assertEqual(fields[0]['bit_low'], 0)  # enable at bit 0
        self.assertEqual(fields[1]['bit_low'], 1)  # mode at bit 1
        self.assertEqual(fields[1]['bit_high'], 2)  # mode is 2 bits
    
    # =========================================================================
    # SUB-003: Group signals by REG_NAME
    # =========================================================================
    def test_sub_003_group_by_reg_name(self):
        """SUB-003: Group signals by REG_NAME"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;

entity test_module is
end entity;

architecture rtl of test_module is
    signal enable : std_logic;  -- @axion RW ADDR=0x00 REG_NAME=control BIT_OFFSET=0
    signal mode : std_logic_vector(1 downto 0);  -- @axion RW ADDR=0x00 REG_NAME=control BIT_OFFSET=1
    signal channel : std_logic_vector(3 downto 0);  -- @axion RW ADDR=0x00 REG_NAME=control BIT_OFFSET=3
    signal status : std_logic_vector(7 downto 0);  -- @axion RO ADDR=0x04
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("test.vhd", vhdl)
        result = self.parser._parse_vhdl_file(filepath)
        
        # One packed register (control) and one regular register (status)
        self.assertEqual(len(result['packed_registers']), 1)
        self.assertEqual(len(result['registers']), 1)
        self.assertEqual(result['registers'][0]['signal_name'], 'status')
        
        # control should have 3 fields
        control = result['packed_registers'][0]
        self.assertEqual(control['reg_name'], 'control')
        self.assertEqual(len(control['fields']), 3)
    
    # =========================================================================
    # SUB-004: Auto-calculate register width
    # =========================================================================
    def test_sub_004_auto_calculate_width(self):
        """SUB-004: Auto-calculate register width from fields"""
        mgr = BitFieldManager()
        
        mgr.add_field("status", 0x00, "flag_a", 1, "RO", "[0:0]", bit_offset=0)
        mgr.add_field("status", 0x00, "flag_b", 1, "RO", "[0:0]", bit_offset=1)
        mgr.add_field("status", 0x00, "counter", 8, "RO", "[7:0]", bit_offset=16)
        
        reg = mgr.get_register("status")
        self.assertEqual(reg.used_bits, 24)  # highest bit is 23 (16+8-1)
    
    # =========================================================================
    # SUB-005: Detect bit overlaps (BitOverlapError)
    # =========================================================================
    def test_sub_005_detect_bit_overlap(self):
        """SUB-005: Detect and report bit overlaps"""
        mgr = BitFieldManager()
        
        # field_a: bits [7:0]
        mgr.add_field("config", 0x00, "field_a", 8, "RW", "[7:0]", bit_offset=0)
        
        # field_b: bits [11:4] - overlaps with field_a at [7:4]
        with self.assertRaises(BitOverlapError) as ctx:
            mgr.add_field("config", 0x00, "field_b", 8, "RW", "[7:0]", bit_offset=4)
        
        error = ctx.exception
        self.assertIn("config", str(error))
        self.assertIn("field_a", str(error))
        self.assertIn("field_b", str(error))
    
    # =========================================================================
    # SUB-006: Auto-pack when BIT_OFFSET omitted
    # =========================================================================
    def test_sub_006_auto_pack(self):
        """SUB-006: Auto-pack signals when BIT_OFFSET not specified"""
        mgr = BitFieldManager()
        
        # Add fields without explicit BIT_OFFSET
        field1 = mgr.add_field("status", 0x00, "flag_a", 1, "RO", "[0:0]")
        field2 = mgr.add_field("status", 0x00, "flag_b", 1, "RO", "[0:0]")
        field3 = mgr.add_field("status", 0x00, "counter", 8, "RO", "[7:0]")
        
        # Should be packed sequentially: flag_a[0], flag_b[1], counter[9:2]
        self.assertEqual(field1.bit_low, 0)
        self.assertEqual(field2.bit_low, 1)
        self.assertEqual(field3.bit_low, 2)
        self.assertEqual(field3.bit_high, 9)
    
    # =========================================================================
    # SUB-007: Backward compatibility
    # =========================================================================
    def test_sub_011_backward_compatibility(self):
        """SUB-011: Signals without REG_NAME work as before"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;

entity test_module is
end entity;

architecture rtl of test_module is
    signal status : std_logic_vector(31 downto 0);  -- @axion RO ADDR=0x00
    signal control : std_logic_vector(31 downto 0);  -- @axion RW ADDR=0x04
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("test.vhd", vhdl)
        result = self.parser._parse_vhdl_file(filepath)
        
        # Should have 2 regular registers, no packed registers
        self.assertEqual(len(result['registers']), 2)
        self.assertEqual(len(result['packed_registers']), 0)
    
    # =========================================================================
    # BitField mask generation
    # =========================================================================
    def test_bit_field_mask(self):
        """Test bit field mask generation"""
        field = BitField(
            name="mode",
            bit_low=1,
            bit_high=2,
            width=2,
            access_mode="RW",
            signal_type="[1:0]"
        )
        
        # bits [2:1] = 0b110 = 6
        self.assertEqual(field.mask, 0x00000006)
    
    def test_bit_field_overlap_detection(self):
        """Test BitField.overlaps_with method"""
        field_a = BitField("a", 0, 7, 8, "RW", "[7:0]")
        field_b = BitField("b", 4, 11, 8, "RW", "[7:0]")
        field_c = BitField("c", 16, 23, 8, "RW", "[7:0]")
        
        # a and b overlap at [7:4]
        overlap = field_a.overlaps_with(field_b)
        self.assertIsNotNone(overlap)
        self.assertEqual(overlap, (4, 7))
        
        # a and c don't overlap
        self.assertIsNone(field_a.overlaps_with(field_c))


def run_subregister_tests():
    """Run all subregister tests and return results"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSubregisterRequirements)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_subregister_tests()
    sys.exit(0 if success else 1)
