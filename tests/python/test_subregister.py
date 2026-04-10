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
        self.assertEqual(len(result['registers']), 2)  # 1 regular + 1 packed register merged

        # Verify both registers are present
        reg_names = [r['signal_name'] for r in result['registers']]
        self.assertIn('status', reg_names)
        self.assertIn('control', reg_names)

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

    # =========================================================================
    # SUB-012: REG_NAME without BIT_OFFSET — auto-pack kicks in
    # =========================================================================
    def test_sub_012_reg_name_without_bit_offset_uses_auto_pack(self):
        """SUB-012: Signals with REG_NAME but no BIT_OFFSET are packed sequentially.

        The BitFieldManager auto-assigns bit positions starting from 0 when
        bit_offset is omitted. The first field gets bit 0, the second starts
        immediately after the first field ends.
        """
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;

entity test_autopack is
end entity;

architecture rtl of test_autopack is
    -- No BIT_OFFSET on either signal -> auto-pack
    signal flag_a : std_logic;                       -- @axion RW ADDR=0x00 REG_NAME=cfg
    signal flag_b : std_logic;                       -- @axion RW ADDR=0x00 REG_NAME=cfg
    signal counter : std_logic_vector(3 downto 0);  -- @axion RW ADDR=0x00 REG_NAME=cfg
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("test_autopack.vhd", vhdl)
        result = self.parser._parse_vhdl_file(filepath)

        self.assertIsNotNone(result)
        packed = result['packed_registers']
        self.assertEqual(len(packed), 1)

        fields = packed[0]['fields']
        self.assertEqual(len(fields), 3)

        # Sort by bit_low to get deterministic order
        fields_sorted = sorted(fields, key=lambda f: f['bit_low'])

        # flag_a (1 bit) at 0
        self.assertEqual(fields_sorted[0]['bit_low'], 0)
        self.assertEqual(fields_sorted[0]['bit_high'], 0)

        # flag_b (1 bit) at 1
        self.assertEqual(fields_sorted[1]['bit_low'], 1)
        self.assertEqual(fields_sorted[1]['bit_high'], 1)

        # counter (4 bits) at [5:2]
        self.assertEqual(fields_sorted[2]['bit_low'], 2)
        self.assertEqual(fields_sorted[2]['bit_high'], 5)

    # =========================================================================
    # SUB-013: Same REG_NAME with different BIT_OFFSETs — correct packing
    # =========================================================================
    def test_sub_013_same_reg_name_different_bit_offsets_correct_packing(self):
        """SUB-013: Same REG_NAME with different BIT_OFFSETs packs fields at declared positions"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;

entity test_packing is
end entity;

architecture rtl of test_packing is
    signal field_a : std_logic_vector(3 downto 0); -- @axion RW ADDR=0x00 REG_NAME=pack BIT_OFFSET=0
    signal field_b : std_logic_vector(4 downto 0); -- @axion RW ADDR=0x00 REG_NAME=pack BIT_OFFSET=8
    signal field_c : std_logic_vector(7 downto 0); -- @axion RW ADDR=0x00 REG_NAME=pack BIT_OFFSET=16
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("test_packing.vhd", vhdl)
        result = self.parser._parse_vhdl_file(filepath)

        self.assertIsNotNone(result)
        packed = result['packed_registers']
        self.assertEqual(len(packed), 1)

        fields = {f['name']: f for f in packed[0]['fields']}

        self.assertIn('field_a', fields)
        self.assertIn('field_b', fields)
        self.assertIn('field_c', fields)

        # Verify bit positions match declared BIT_OFFSETs
        self.assertEqual(fields['field_a']['bit_low'], 0)
        self.assertEqual(fields['field_a']['bit_high'], 3)   # 4 bits wide

        self.assertEqual(fields['field_b']['bit_low'], 8)
        self.assertEqual(fields['field_b']['bit_high'], 12)  # 5 bits wide

        self.assertEqual(fields['field_c']['bit_low'], 16)
        self.assertEqual(fields['field_c']['bit_high'], 23)  # 8 bits wide

    # =========================================================================
    # SUB-014: Overlapping BIT_OFFSETs in packed register at parser level
    # =========================================================================
    def test_sub_014_overlapping_bit_offsets_recorded_not_raised(self):
        """SUB-014: Parser records overlap as parsing_error with has_error=True; does NOT raise.

        The parser passes allow_overlap=True to BitFieldManager so the GUI can still
        render the conflicting layout. The error is surfaced via parsing_errors and
        the field's has_error flag.
        """
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;

entity test_overlap is
end entity;

architecture rtl of test_overlap is
    -- field_a: bits [7:0]
    signal field_a : std_logic_vector(7 downto 0); -- @axion RW ADDR=0x00 REG_NAME=reg BIT_OFFSET=0
    -- field_b: bits [11:4] -> overlaps field_a at [7:4]
    signal field_b : std_logic_vector(7 downto 0); -- @axion RW ADDR=0x00 REG_NAME=reg BIT_OFFSET=4
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("test_overlap.vhd", vhdl)
        result = self.parser._parse_vhdl_file(filepath)

        # Must not raise
        self.assertIsNotNone(result)

        # parsing_errors should contain the overlap report
        errors = result.get('parsing_errors', [])
        overlap_errors = [
            e for e in errors
            if 'overlap' in e.get('msg', '').lower() or 'conflict' in e.get('msg', '').lower()
        ]
        self.assertGreater(
            len(overlap_errors), 0,
            "Expected an overlap/conflict entry in parsing_errors"
        )

        # Packed register must still be created with both fields present
        packed = result.get('packed_registers', [])
        self.assertEqual(len(packed), 1)
        self.assertEqual(len(packed[0]['fields']), 2)

        # The second (conflicting) field should carry has_error=True
        error_fields = [f for f in packed[0]['fields'] if f.get('has_error')]
        self.assertGreater(
            len(error_fields), 0,
            "Expected at least one field with has_error=True"
        )

    # =========================================================================
    # SUB-015: Packed field width is correctly calculated
    # =========================================================================
    def test_sub_015_packed_field_width_calculation(self):
        """SUB-015: BitField width matches the declared signal width"""
        mgr = BitFieldManager()

        # 1-bit std_logic
        f1 = mgr.add_field("r", 0x00, "flag", 1, "RW", "[0:0]", bit_offset=0)
        self.assertEqual(f1.width, 1)
        self.assertEqual(f1.bit_low, 0)
        self.assertEqual(f1.bit_high, 0)

        # 8-bit field starting at bit 4
        f2 = mgr.add_field("r", 0x00, "byte_field", 8, "RW", "[7:0]", bit_offset=8)
        self.assertEqual(f2.width, 8)
        self.assertEqual(f2.bit_low, 8)
        self.assertEqual(f2.bit_high, 15)

        # 16-bit field starting at bit 16
        f3 = mgr.add_field("r", 0x00, "word_field", 16, "RW", "[15:0]", bit_offset=16)
        self.assertEqual(f3.width, 16)
        self.assertEqual(f3.bit_low, 16)
        self.assertEqual(f3.bit_high, 31)

    # =========================================================================
    # SUB-016: PackedRegister.used_bits reflects highest occupied bit
    # =========================================================================
    def test_sub_016_packed_register_used_bits(self):
        """SUB-016: PackedRegister.used_bits returns the count of bits up to the highest used bit"""
        mgr = BitFieldManager()

        mgr.add_field("r", 0x00, "f1", 4, "RW", "[3:0]", bit_offset=0)   # bits [3:0]
        mgr.add_field("r", 0x00, "f2", 4, "RW", "[3:0]", bit_offset=8)   # bits [11:8]

        reg = mgr.get_register("r")
        # Highest bit is 11 (8 + 4 - 1), so used_bits = 12
        self.assertEqual(reg.used_bits, 12)


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
