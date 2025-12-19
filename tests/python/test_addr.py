#!/usr/bin/env python3
"""
test_addr.py - Address Management Requirements Tests

Tests for ADDR-001 through ADDR-008 requirements
Verifies automatic and manual address assignment.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from axion_hdl import AxionHDL, AddressConflictError
from axion_hdl.parser import VHDLParser


class TestAddressManagementRequirements(unittest.TestCase):
    """Test cases for ADDR-xxx requirements"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, "output")
        self.parser = VHDLParser()
    
    def tearDown(self):
        """Clean up temp files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _write_temp_vhdl(self, filename: str, content: str) -> str:
        """Write VHDL content to temp file and return path"""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath
    
    # =========================================================================
    # ADDR-001: Automatic Address Assignment
    # =========================================================================
    def test_addr_001_auto_assign_sequential(self):
        """ADDR-001: Auto-assigned addresses are sequential"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity auto_addr is
    port (clk : in std_logic);
end entity;
architecture rtl of auto_addr is
    signal reg_a : std_logic_vector(31 downto 0); -- @axion RO
    signal reg_b : std_logic_vector(31 downto 0); -- @axion RW
    signal reg_c : std_logic_vector(31 downto 0); -- @axion WO
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("auto_addr.vhd", vhdl)
        result = self.parser.parse_file(filepath)
        
        self.assertIsNotNone(result)
        signals = result.get('signals', [])
        self.assertEqual(len(signals), 3)
        
        # Addresses should be 0x00, 0x04, 0x08
        addresses = [s['address'] for s in signals]
        self.assertEqual(addresses, [0, 4, 8])
    
    def test_addr_001_first_addr_zero(self):
        """ADDR-001: First auto-assigned address is 0x00"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity first_zero is
    port (clk : in std_logic);
end entity;
architecture rtl of first_zero is
    signal first_reg : std_logic_vector(31 downto 0); -- @axion RO
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("first_zero.vhd", vhdl)
        result = self.parser.parse_file(filepath)
        
        signals = result.get('signals', [])
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0]['address'], 0)
    
    # =========================================================================
    # ADDR-002: Manual Address Assignment
    # =========================================================================
    def test_addr_002_manual_address(self):
        """ADDR-002: ADDR attribute sets specific address"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity manual_addr is
    port (clk : in std_logic);
end entity;
architecture rtl of manual_addr is
    signal reg_a : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x100
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("manual_addr.vhd", vhdl)
        result = self.parser.parse_file(filepath)
        
        signals = result.get('signals', [])
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0]['address'], 0x100)
    
    # =========================================================================
    # ADDR-003: Mixed Auto/Manual Address Assignment
    # =========================================================================
    def test_addr_003_mixed_assignment(self):
        """ADDR-003: Mixed auto and manual addresses work correctly"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity mixed_addr is
    port (clk : in std_logic);
end entity;
architecture rtl of mixed_addr is
    signal reg_a : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x10
    signal reg_b : std_logic_vector(31 downto 0); -- @axion RW
    signal reg_c : std_logic_vector(31 downto 0); -- @axion WO ADDR=0x20
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("mixed_addr.vhd", vhdl)
        result = self.parser.parse_file(filepath)
        
        signals = result.get('signals', [])
        self.assertEqual(len(signals), 3)
        
        # reg_a at 0x10, reg_b auto at 0x14, reg_c at 0x20
        addr_dict = {s['name']: s['address'] for s in signals}
        self.assertEqual(addr_dict['reg_a'], 0x10)
        # Auto-assigned should continue from 0x10
        self.assertEqual(addr_dict['reg_b'], 0x14)
        self.assertEqual(addr_dict['reg_c'], 0x20)
    
    # =========================================================================
    # ADDR-004: Address Alignment Enforcement
    # =========================================================================
    def test_addr_004_alignment(self):
        """ADDR-004: Addresses are 4-byte aligned"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity align_test is
    port (clk : in std_logic);
end entity;
architecture rtl of align_test is
    signal reg_a : std_logic_vector(31 downto 0); -- @axion RO
    signal reg_b : std_logic_vector(31 downto 0); -- @axion RW
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("align_test.vhd", vhdl)
        result = self.parser.parse_file(filepath)
        
        signals = result.get('signals', [])
        for sig in signals:
            self.assertEqual(sig['address'] % 4, 0, f"Address {sig['address']} not 4-byte aligned")
    
    # =========================================================================
    # ADDR-005: Address Conflict Detection
    # =========================================================================
    def test_addr_005_conflict_detection(self):
        """ADDR-005: Duplicate addresses raise AddressConflictError"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity conflict is
    port (clk : in std_logic);
end entity;
architecture rtl of conflict is
    signal reg_a : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x10
    signal reg_b : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x10
begin
end architecture;
'''
        self._write_temp_vhdl("conflict.vhd", vhdl)
        
        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_src(self.temp_dir)
        axion.analyze()
        
        # Check for address conflict in parsing_errors
        found_conflict = False
        for module in axion.analyzed_modules:
            errors = module.get('parsing_errors', [])
            for err in errors:
                if 'Address Conflict' in err.get('msg', ''):
                    found_conflict = True
                    break
        
        self.assertTrue(found_conflict, "Address conflict should be detected in parsing_errors")
    
    # =========================================================================
    # ADDR-006: Wide Signal Address Space Allocation
    # =========================================================================
    def test_addr_006_wide_signal_space(self):
        """ADDR-006: Wide signals reserve multiple address slots"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity wide_space is
    port (clk : in std_logic);
end entity;
architecture rtl of wide_space is
    signal wide_reg : std_logic_vector(63 downto 0); -- @axion RO ADDR=0x00
    signal next_reg : std_logic_vector(31 downto 0); -- @axion RW
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("wide_space.vhd", vhdl)
        result = self.parser.parse_file(filepath)
        
        signals = result.get('signals', [])
        addr_dict = {s['name']: s['address'] for s in signals}
        
        # wide_reg uses 0x00 and 0x04, next_reg should be at 0x08
        self.assertEqual(addr_dict['wide_reg'], 0x00)
        self.assertEqual(addr_dict['next_reg'], 0x08)
    
    # =========================================================================
    # ADDR-007: Address Gap Handling
    # =========================================================================
    def test_addr_007_gaps_preserved(self):
        """ADDR-007: Gaps between manual addresses preserved"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity gaps is
    port (clk : in std_logic);
end entity;
architecture rtl of gaps is
    signal reg_a : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
    signal reg_b : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x100
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("gaps.vhd", vhdl)
        result = self.parser.parse_file(filepath)
        
        signals = result.get('signals', [])
        addr_dict = {s['name']: s['address'] for s in signals}
        
        # Gap between 0x00 and 0x100 should be preserved
        self.assertEqual(addr_dict['reg_a'], 0x00)
        self.assertEqual(addr_dict['reg_b'], 0x100)
    
    # =========================================================================
    # ADDR-008: Base Address Addition
    # =========================================================================
    def test_addr_008_base_address_addition(self):
        """ADDR-008: BASE_ADDR added to relative addresses"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x1000
entity base_add is
    port (clk : in std_logic);
end entity;
architecture rtl of base_add is
    signal reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x04
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("base_add.vhd", vhdl)
        result = self.parser.parse_file(filepath)
        
        # Relative address should be 0x04
        signals = result.get('signals', [])
        self.assertEqual(signals[0]['address'], 0x04)
        
        # Base address should be stored
        self.assertEqual(result['base_addr'], 0x1000)


def run_addr_tests():
    """Run all address management tests and return results"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestAddressManagementRequirements)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_addr_tests()
    sys.exit(0 if success else 1)
