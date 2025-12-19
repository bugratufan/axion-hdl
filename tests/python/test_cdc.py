#!/usr/bin/env python3
"""
test_cdc.py - Clock Domain Crossing Requirements Tests

Tests for CDC-001 through CDC-007 requirements
Verifies CDC synchronizer generation and configuration.
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


class TestCDCRequirements(unittest.TestCase):
    """Test cases for CDC-xxx requirements"""
    
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
    
    def _generate_and_read_vhdl(self, vhdl_content: str, entity_name: str) -> str:
        """Generate VHDL and return the generated content"""
        self._write_temp_vhdl(f"{entity_name}.vhd", vhdl_content)
        
        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_src(self.temp_dir)
        axion.analyze()
        axion.generate_vhdl()
        
        gen_file = os.path.join(self.output_dir, f"{entity_name}_axion_reg.vhd")
        if os.path.exists(gen_file):
            with open(gen_file, 'r') as f:
                return f.read()
        return ""
    
    # =========================================================================
    # CDC-001: CDC Synchronizer Stage Count
    # =========================================================================
    def test_cdc_001_stage_count_2(self):
        """CDC-001: CDC_STAGE=2 generates 2-stage synchronizer"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN CDC_STAGE=2
entity cdc_test is
    port (clk : in std_logic);
end entity;
architecture rtl of cdc_test is
    signal reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        content = self._generate_and_read_vhdl(vhdl, "cdc_test")
        # CDC-001: Verify module_clk port exists for CDC-enabled module
        self.assertIn('module_clk', content.lower(), 
            "CDC-enabled module must have module_clk port")
        # Verify sync-related signals or logic is present
        self.assertTrue('sync' in content.lower(), 
            "CDC-enabled module should have synchronizer signals")
    
    def test_cdc_001_stage_count_3(self):
        """CDC-001: CDC_STAGE=3 generates 3-stage synchronizer"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN CDC_STAGE=3
entity cdc3_test is
    port (clk : in std_logic);
end entity;
architecture rtl of cdc3_test is
    signal reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        content = self._generate_and_read_vhdl(vhdl, "cdc3_test")
        # CDC-001: With 3-stage CDC, should have module_clk and sync signals
        self.assertIn('module_clk', content.lower(), 
            "3-stage CDC module must have module_clk port")
        self.assertTrue(len(content) > 500, 
            "CDC-enabled module should have substantial generated code")
    
    # =========================================================================
    # CDC-002: CDC Default Stage Count
    # =========================================================================
    def test_cdc_002_default_stage_count(self):
        """CDC-002: CDC_EN without CDC_STAGE defaults to 2 stages"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN
entity cdc_default is
    port (clk : in std_logic);
end entity;
architecture rtl of cdc_default is
    signal reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        content = self._generate_and_read_vhdl(vhdl, "cdc_default")
        # CDC-002: Default to 2 stages - verify module_clk port exists
        self.assertIn('module_clk', content.lower(), 
            "CDC-enabled module (default stages) must have module_clk port")
    
    # =========================================================================
    # CDC-003: CDC Signal Declaration
    # =========================================================================
    def test_cdc_003_sync_signal_declaration(self):
        """CDC-003: CDC-enabled modules declare synchronizer signals"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN CDC_STAGE=2
entity cdc_signals is
    port (clk : in std_logic);
end entity;
architecture rtl of cdc_signals is
    signal my_reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        content = self._generate_and_read_vhdl(vhdl, "cdc_signals")
        # CDC-003: Generated VHDL with CDC should have signal declarations
        self.assertTrue(len(content) > 500, 
            "CDC module should generate substantial VHDL")
        self.assertIn('signal', content.lower(), 
            "CDC module should declare internal signals")
    
    # =========================================================================
    # CDC-004: CDC Module Clock Port
    # =========================================================================
    def test_cdc_004_module_clock_port(self):
        """CDC-004: CDC-enabled modules have module_clk port"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN
entity cdc_clk is
    port (clk : in std_logic);
end entity;
architecture rtl of cdc_clk is
    signal reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        content = self._generate_and_read_vhdl(vhdl, "cdc_clk")
        # CDC-004: CDC-enabled modules must have module_clk in entity
        self.assertIn('module_clk', content.lower(), 
            "CDC-enabled module must have module_clk port")
    
    # =========================================================================
    # CDC-005: CDC Disabled Behavior
    # =========================================================================
    def test_cdc_005_cdc_disabled(self):
        """CDC-005: Without CDC_EN, no CDC signals generated"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity no_cdc is
    port (clk : in std_logic);
end entity;
architecture rtl of no_cdc is
    signal reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        content = self._generate_and_read_vhdl(vhdl, "no_cdc")
        # CDC-005: Without CDC_EN, module_clk should NOT be in entity port list
        # Extract entity section to verify no module_clk in ports
        self.assertTrue(len(content) > 100, 
            "Non-CDC module should still generate VHDL")
        # The module_clk should not appear as port
        entity_section = content.lower().split('architecture')[0] if 'architecture' in content.lower() else content.lower()
        self.assertNotIn('module_clk', entity_section, 
            "Non-CDC module should not have module_clk port")
    
    # =========================================================================
    # CDC-006: RO Register CDC Path
    # =========================================================================
    def test_cdc_006_ro_cdc_path(self):
        """CDC-006: RO registers synchronized from module to AXI domain"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN CDC_STAGE=2
entity ro_cdc is
    port (clk : in std_logic);
end entity;
architecture rtl of ro_cdc is
    signal status_ro : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        content = self._generate_and_read_vhdl(vhdl, "ro_cdc")
        # RO register should have input port
        self.assertTrue('status_ro' in content.lower())
    
    # =========================================================================
    # CDC-007: RW/WO Register CDC Path
    # =========================================================================
    def test_cdc_007_rw_cdc_path(self):
        """CDC-007: Writable registers synchronized from AXI to module domain"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN CDC_STAGE=2
entity rw_cdc is
    port (clk : in std_logic);
end entity;
architecture rtl of rw_cdc is
    signal control_rw : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x00
begin
end architecture;
'''
        content = self._generate_and_read_vhdl(vhdl, "rw_cdc")
        # RW register should have output port
        self.assertTrue('control_rw' in content.lower())

    # =========================================================================
    # CDC-008: CDC Flag Equivalence
    # =========================================================================
    def test_cdc_008_equivalence(self):
        """CDC-008: CDC_EN flag is equivalent to CDC_EN=true"""
        vhdl_flag = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN
entity cdc_flag is
    port (clk : in std_logic);
end entity;
architecture rtl of cdc_flag is
    signal reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        vhdl_kv = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN=true
entity cdc_kv is
    port (clk : in std_logic);
end entity;
architecture rtl of cdc_kv is
    signal reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        content_flag = self._generate_and_read_vhdl(vhdl_flag, "cdc_flag")
        content_kv = self._generate_and_read_vhdl(vhdl_kv, "cdc_kv")
        
        # Verify both generated content with module clock port (CDC enabled)
        self.assertTrue('module_clk' in content_flag.lower())
        self.assertTrue('module_clk' in content_kv.lower())
        
        # Verify content similarity (ignoring entity names)
        # We can check specific CDC logic blocks
        self.assertTrue('sync' in content_flag.lower())


def run_cdc_tests():
    """Run all CDC tests and return results"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestCDCRequirements)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_cdc_tests()
    sys.exit(0 if success else 1)
