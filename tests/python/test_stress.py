#!/usr/bin/env python3
"""
test_stress.py - Stress and Robustness Requirements Tests

Tests for STRESS-001 through STRESS-006 requirements
Verifies system behavior under stress conditions.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from axion_hdl import AxionHDL
from axion_hdl.parser import VHDLParser


class TestStressRequirements(unittest.TestCase):
    """Test cases for STRESS-xxx requirements"""
    
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
    # STRESS-001: Maximum Register Count Support
    # =========================================================================
    def test_stress_001_many_registers(self):
        """STRESS-001: Support 100+ registers per module"""
        # Generate VHDL with 100 registers
        signals = []
        for i in range(100):
            signals.append(f"    signal reg_{i:03d} : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x{i*4:04X}")
        
        vhdl = f'''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity many_regs is
    port (clk : in std_logic);
end entity;
architecture rtl of many_regs is
{chr(10).join(signals)}
begin
end architecture;
'''
        self._write_temp_vhdl("many_regs.vhd", vhdl)
        
        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_src(self.temp_dir)
        
        # Should analyze without error
        result = axion.analyze()
        self.assertTrue(result)
        
        modules = axion.get_modules()
        self.assertEqual(len(modules), 1)
        self.assertEqual(len(modules[0]['registers']), 100)
    
    # =========================================================================
    # STRESS-002: Maximum Signal Width Support
    # =========================================================================
    def test_stress_002_very_wide_signal(self):
        """STRESS-002: Support 256-bit signals"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity wide_signal is
    port (clk : in std_logic);
end entity;
architecture rtl of wide_signal is
    signal huge_reg : std_logic_vector(255 downto 0); -- @axion RO ADDR=0x00
    signal normal_reg : std_logic_vector(31 downto 0); -- @axion RW
begin
end architecture;
'''
        self._write_temp_vhdl("wide_signal.vhd", vhdl)
        
        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_src(self.temp_dir)
        result = axion.analyze()
        
        self.assertTrue(result)
        
        # 256-bit signal should allocate 8 registers
        modules = axion.get_modules()
        self.assertEqual(len(modules), 1)
    
    # =========================================================================
    # STRESS-003: Long Running Stability (simulated with multiple operations)
    # =========================================================================
    def test_stress_003_repeated_analysis(self):
        """STRESS-003: Multiple analysis cycles without errors"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity stable is
    port (clk : in std_logic);
end entity;
architecture rtl of stable is
    signal reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x00
begin
end architecture;
'''
        self._write_temp_vhdl("stable.vhd", vhdl)
        
        # Run multiple analysis cycles
        for i in range(10):
            axion = AxionHDL(output_dir=os.path.join(self.output_dir, f"run_{i}"))
            axion.add_src(self.temp_dir)
            result = axion.analyze()
            self.assertTrue(result, f"Failed on iteration {i}")
    
    # =========================================================================
    # STRESS-004: Rapid Reset Cycling (simulated with repeated generation)
    # =========================================================================
    def test_stress_004_repeated_generation(self):
        """STRESS-004: Repeated generation cycles without errors"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity gen_test is
    port (clk : in std_logic);
end entity;
architecture rtl of gen_test is
    signal reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x00
begin
end architecture;
'''
        self._write_temp_vhdl("gen_test.vhd", vhdl)
        
        for i in range(5):
            output = os.path.join(self.output_dir, f"gen_{i}")
            axion = AxionHDL(output_dir=output)
            axion.add_src(self.temp_dir)
            axion.analyze()
            axion.generate_vhdl()
            axion.generate_c_header()
            
            # Verify output exists
            self.assertTrue(os.path.exists(os.path.join(output, "gen_test_axion_reg.vhd")))
    
    # =========================================================================
    # STRESS-005: Random Access Pattern (simulated with varied addresses)
    # =========================================================================
    def test_stress_005_random_addresses(self):
        """STRESS-005: Non-sequential address patterns work correctly"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity random_addr is
    port (clk : in std_logic);
end entity;
architecture rtl of random_addr is
    signal reg_a : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x100
    signal reg_b : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x04
    signal reg_c : std_logic_vector(31 downto 0); -- @axion WO ADDR=0x200
    signal reg_d : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x08
    signal reg_e : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x50
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("random_addr.vhd", vhdl)
        result = self.parser.parse_file(filepath)
        
        self.assertIsNotNone(result)
        signals = result.get('signals', [])
        self.assertEqual(len(signals), 5)
        
        # All addresses should be correctly assigned
        addr_set = {s['address'] for s in signals}
        expected = {0x100, 0x04, 0x200, 0x08, 0x50}
        self.assertEqual(addr_set, expected)
    
    # =========================================================================
    # STRESS-006: Boundary Data Values (generate and verify output)
    # =========================================================================
    def test_stress_006_boundary_values(self):
        """STRESS-006: Generation handles all register types"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity boundary is
    port (clk : in std_logic);
end entity;
architecture rtl of boundary is
    signal ro_reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
    signal wo_reg : std_logic_vector(31 downto 0); -- @axion WO ADDR=0x04
    signal rw_reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x08
    signal strobe_reg : std_logic_vector(31 downto 0); -- @axion RW R_STROBE W_STROBE ADDR=0x0C
begin
end architecture;
'''
        self._write_temp_vhdl("boundary.vhd", vhdl)
        
        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_src(self.temp_dir)
        axion.analyze()
        axion.generate_vhdl()
        axion.generate_c_header()
        
        # Read generated files and verify content
        vhdl_file = os.path.join(self.output_dir, "boundary_axion_reg.vhd")
        self.assertTrue(os.path.exists(vhdl_file))
        
        with open(vhdl_file, 'r') as f:
            content = f.read().lower()
        
        # Verify all register types are handled
        self.assertIn('ro_reg', content)
        self.assertIn('wo_reg', content)
        self.assertIn('rw_reg', content)
        self.assertIn('strobe_reg', content)


def run_stress_tests():
    """Run all stress tests and return results"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestStressRequirements)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_stress_tests()
    sys.exit(0 if success else 1)
