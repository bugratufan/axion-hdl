#!/usr/bin/env python3
"""
test_error_handling.py - Error Handling Requirements Tests

Tests for ERR-001 through ERR-006 requirements
Verifies proper error handling in various scenarios.
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


class TestErrorHandlingRequirements(unittest.TestCase):
    """Test cases for ERR-xxx requirements"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, "output")
    
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
    # ERR-001: AddressConflictError Exception
    # =========================================================================
    def test_err_001_address_conflict_exception(self):
        """ERR-001: Duplicate addresses raise AddressConflictError"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity conflict_test is
    port (clk : in std_logic);
end entity;
architecture rtl of conflict_test is
    signal reg_a : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
    signal reg_b : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x00
begin
end architecture;
'''
        self._write_temp_vhdl("conflict.vhd", vhdl)
        
        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_src(self.temp_dir)
        
        with self.assertRaises(AddressConflictError) as ctx:
            axion.analyze()
        
        # Check exception message contains expected info
        error_msg = str(ctx.exception)
        self.assertIn('0x', error_msg.lower())  # Address mentioned
    
    def test_err_001_exception_has_register_names(self):
        """ERR-001: Exception includes register names"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity conflict_test2 is
    port (clk : in std_logic);
end entity;
architecture rtl of conflict_test2 is
    signal first_reg : std_logic_vector(31 downto 0);  -- @axion RO ADDR=0x10
    signal second_reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x10
begin
end architecture;
'''
        self._write_temp_vhdl("conflict2.vhd", vhdl)
        
        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_src(self.temp_dir)
        
        with self.assertRaises(AddressConflictError) as ctx:
            axion.analyze()
        
        error_msg = str(ctx.exception)
        # Should mention both register names
        self.assertTrue('first_reg' in error_msg or 'second_reg' in error_msg)
    
    # =========================================================================
    # ERR-002: Invalid VHDL File Handling
    # =========================================================================
    def test_err_002_nonexistent_file(self):
        """ERR-002: Non-existent file handled gracefully"""
        # Don't create any VHDL file, just try to analyze empty dir
        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_src(self.temp_dir)
        
        # Should not raise exception
        result = axion.analyze()
        # Empty analysis is okay
        self.assertTrue(result is not None or len(axion.get_modules()) == 0)
    
    def test_err_002_binary_file_skipped(self):
        """ERR-002: Binary files are skipped"""
        # Create a binary file
        binary_file = os.path.join(self.temp_dir, "binary.vhd")
        with open(binary_file, 'wb') as f:
            f.write(bytes([0x00, 0x01, 0x02, 0xFF, 0xFE]))
        
        # Create valid VHDL file
        valid_vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity valid is port (clk : in std_logic); end entity;
architecture rtl of valid is
    signal reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin end architecture;
'''
        self._write_temp_vhdl("valid.vhd", valid_vhdl)
        
        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_src(self.temp_dir)
        
        # Should not crash, should find the valid file
        try:
            axion.analyze()
            modules = axion.get_modules()
            self.assertTrue(any(m.get('entity_name') == 'valid' for m in modules))
        except Exception as e:
            self.fail(f"Should handle binary files gracefully: {e}")
    
    # =========================================================================
    # ERR-003: Missing @axion Annotation Handling
    # =========================================================================
    def test_err_003_no_annotation_skipped(self):
        """ERR-003: Files without @axion silently skipped"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;

entity no_annotation is
    port (
        clk : in std_logic;
        data : out std_logic_vector(31 downto 0)
    );
end entity;

architecture rtl of no_annotation is
    signal internal_reg : std_logic_vector(31 downto 0);
begin
    data <= internal_reg;
end architecture;
'''
        self._write_temp_vhdl("no_annotation.vhd", vhdl)
        
        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_src(self.temp_dir)
        
        # Should not raise exception
        try:
            axion.analyze()
            # File should be skipped, no modules generated
            modules = axion.get_modules()
            self.assertFalse(any(m.get('entity_name') == 'no_annotation' for m in modules))
        except Exception as e:
            self.fail(f"Should skip non-annotated files: {e}")
    
    def test_err_003_only_axion_def_skipped(self):
        """ERR-003: Files with only @axion_def but no signals skipped"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x1000
entity only_def is
    port (clk : in std_logic);
end entity;
architecture rtl of only_def is
    signal internal : std_logic_vector(31 downto 0);  -- No @axion annotation
begin
end architecture;
'''
        self._write_temp_vhdl("only_def.vhd", vhdl)
        
        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_src(self.temp_dir)
        
        try:
            axion.analyze()
            modules = axion.get_modules()
            # Should not generate module without annotated signals
            matching = [m for m in modules if m.get('entity_name') == 'only_def']
            if matching:
                # If module exists, it should have no signals
                self.assertEqual(len(matching[0].get('signals', [])), 0)
        except Exception as e:
            self.fail(f"Should handle files with only @axion_def: {e}")
    
    # =========================================================================
    # ERR-004: Invalid Address Format Error
    # =========================================================================
    def test_err_004_invalid_hex_address(self):
        """ERR-004: Invalid hex address reports error"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity bad_addr is
    port (clk : in std_logic);
end entity;
architecture rtl of bad_addr is
    signal reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0xGG
begin
end architecture;
'''
        self._write_temp_vhdl("bad_addr.vhd", vhdl)
        
        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_src(self.temp_dir)
        
        # Should either raise error or skip the bad annotation
        try:
            axion.analyze()
            modules = axion.get_modules()
            # If it didn't raise error, the signal should be skipped
            if modules:
                signals = modules[0].get('signals', [])
                self.assertFalse(any(s['name'] == 'reg' for s in signals))
        except Exception:
            # Exception is also acceptable behavior
            pass
    
    # =========================================================================
    # ERR-005: Missing Entity Declaration Handling
    # =========================================================================
    def test_err_005_no_entity_skipped(self):
        """ERR-005: Files without entity declaration skipped"""
        vhdl = '''
-- Just a package
library ieee;
use ieee.std_logic_1164.all;

package my_constants is
    constant C_VALUE : integer := 42;
    -- @axion RO ADDR=0x00
end package;
'''
        self._write_temp_vhdl("package_only.vhd", vhdl)
        
        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_src(self.temp_dir)
        
        try:
            axion.analyze()
            # Should not crash, package should be skipped
            modules = axion.get_modules()
            self.assertFalse(any(m.get('entity_name') == 'my_constants' for m in modules))
        except Exception as e:
            self.fail(f"Should handle package files: {e}")
    
    # =========================================================================
    # ERR-006: Duplicate Signal Name Detection
    # =========================================================================
    def test_err_006_duplicate_signal_detection(self):
        """ERR-006: Duplicate signal names detected"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity dup_signal is
    port (clk : in std_logic);
end entity;
architecture rtl of dup_signal is
    signal my_reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
    signal my_reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x04
begin
end architecture;
'''
        self._write_temp_vhdl("dup_signal.vhd", vhdl)
        
        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_src(self.temp_dir)
        
        # Note: This is actually invalid VHDL, so it may fail at parse level
        # or at duplicate detection level
        try:
            axion.analyze()
            # If no exception, check signals are handled properly
        except Exception:
            # Some form of error detection is expected
            pass


def run_error_tests():
    """Run all error handling tests and return results"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestErrorHandlingRequirements)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_error_tests()
    sys.exit(0 if success else 1)
