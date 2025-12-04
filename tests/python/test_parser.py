#!/usr/bin/env python3
"""
test_parser.py - Parser Requirements Tests

Tests for PARSER-001 through PARSER-008 requirements
Verifies the VHDL parser functionality for annotation parsing,
entity extraction, and signal type handling.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from axion_hdl.parser import VHDLParser
from axion_hdl.annotation_parser import AnnotationParser


class TestParserRequirements(unittest.TestCase):
    """Test cases for PARSER-xxx requirements"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.parser = VHDLParser()
        self.annotation_parser = AnnotationParser()
        self.temp_dir = tempfile.mkdtemp()
    
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
    
    def _get_signal_by_name(self, signals, name):
        """Helper to find signal by name in list"""
        for s in signals:
            if s.get('name') == name:
                return s
        return None
    
    # =========================================================================
    # PARSER-001: Entity Name Extraction
    # =========================================================================
    def test_parser_001_basic_entity_extraction(self):
        """PARSER-001: Basic entity name extraction"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;

-- @axion_def BASE_ADDR=0x0000
entity my_test_module is
    port (
        clk : in std_logic
    );
end entity my_test_module;

architecture rtl of my_test_module is
    signal test_reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("test_entity.vhd", vhdl)
        result = self.parser.parse_file(filepath)
        self.assertIsNotNone(result)
        self.assertEqual(result.get('entity_name'), 'my_test_module')
    
    def test_parser_001_entity_with_whitespace(self):
        """PARSER-001: Entity extraction with varying whitespace"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;

-- @axion_def BASE_ADDR=0x0000
entity    whitespace_test    is
    port (clk : in std_logic);
end entity;

architecture rtl of whitespace_test is
    signal test_reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("whitespace_entity.vhd", vhdl)
        result = self.parser.parse_file(filepath)
        self.assertIsNotNone(result)
        self.assertEqual(result.get('entity_name'), 'whitespace_test')
    
    def test_parser_001_no_entity(self):
        """PARSER-001: File without entity declaration"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;

-- Just a package, no entity
package my_package is
    constant C_VALUE : integer := 42;
end package;
'''
        filepath = self._write_temp_vhdl("no_entity.vhd", vhdl)
        result = self.parser.parse_file(filepath)
        # Should return None or empty entity_name
        self.assertTrue(result is None or result.get('entity_name') is None)
    
    # =========================================================================
    # PARSER-002: Signal Type Parsing
    # =========================================================================
    def test_parser_002_std_logic(self):
        """PARSER-002: Parse std_logic as 1-bit"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity signal_test is
    port (clk : in std_logic);
end entity;
architecture rtl of signal_test is
    signal single_bit : std_logic; -- @axion RW ADDR=0x00
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("std_logic_test.vhd", vhdl)
        result = self.parser.parse_file(filepath)
        signals = result.get('signals', [])
        self.assertTrue(any(s['width'] == 1 for s in signals))
    
    def test_parser_002_std_logic_vector_downto(self):
        """PARSER-002: Parse std_logic_vector(N downto M)"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity vector_test is
    port (clk : in std_logic);
end entity;
architecture rtl of vector_test is
    signal my_vector : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
    signal small_vec : std_logic_vector(7 downto 0);  -- @axion RW ADDR=0x04
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("vector_test.vhd", vhdl)
        result = self.parser.parse_file(filepath)
        signals = result.get('signals', [])
        widths = {s['name']: s['width'] for s in signals}
        self.assertEqual(widths.get('my_vector'), 32)
        self.assertEqual(widths.get('small_vec'), 8)
    
    def test_parser_002_std_logic_vector_with_spaces(self):
        """PARSER-002: Parse std_logic_vector with extra spaces"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity spaced_vector is
    port (clk : in std_logic);
end entity;
architecture rtl of spaced_vector is
    signal spaced : std_logic_vector( 15 downto 0 ); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("spaced_vector.vhd", vhdl)
        result = self.parser.parse_file(filepath)
        signals = result.get('signals', [])
        self.assertTrue(any(s['width'] == 16 for s in signals))
    
    # =========================================================================
    # PARSER-003: @axion Annotation Parsing
    # =========================================================================
    def test_parser_003_access_modes(self):
        """PARSER-003: Parse RO, RW, WO access modes"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity access_test is
    port (clk : in std_logic);
end entity;
architecture rtl of access_test is
    signal read_only_reg : std_logic_vector(31 downto 0);  -- @axion RO ADDR=0x00
    signal read_write_reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x04
    signal write_only_reg : std_logic_vector(31 downto 0); -- @axion WO ADDR=0x08
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("access_test.vhd", vhdl)
        result = self.parser.parse_file(filepath)
        signals = result.get('signals', [])
        access_modes = {s['name']: s['access'] for s in signals}
        self.assertEqual(access_modes.get('read_only_reg'), 'RO')
        self.assertEqual(access_modes.get('read_write_reg'), 'RW')
        self.assertEqual(access_modes.get('write_only_reg'), 'WO')
    
    def test_parser_003_strobe_flags(self):
        """PARSER-003: Parse R_STROBE and W_STROBE flags"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity strobe_test is
    port (clk : in std_logic);
end entity;
architecture rtl of strobe_test is
    signal with_rd_strobe : std_logic_vector(31 downto 0); -- @axion RO R_STROBE ADDR=0x00
    signal with_wr_strobe : std_logic_vector(31 downto 0); -- @axion WO W_STROBE ADDR=0x04
    signal with_both : std_logic_vector(31 downto 0);      -- @axion RW R_STROBE W_STROBE ADDR=0x08
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("strobe_test.vhd", vhdl)
        result = self.parser.parse_file(filepath)
        self.assertIsNotNone(result, "Parser should return result for strobe test file")
        signals = result.get('signals', [])
        
        for s in signals:
            if s['name'] == 'with_rd_strobe':
                self.assertTrue(s.get('r_strobe', False))
            elif s['name'] == 'with_wr_strobe':
                self.assertTrue(s.get('w_strobe', False))
            elif s['name'] == 'with_both':
                self.assertTrue(s.get('r_strobe', False))
                self.assertTrue(s.get('w_strobe', False))
    
    def test_parser_003_multiple_attributes_same_line(self):
        """PARSER-003: Multiple attributes on single line"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity multi_attr is
    port (clk : in std_logic);
end entity;
architecture rtl of multi_attr is
    signal multi : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x10 R_STROBE W_STROBE DESC="Multi-attribute register"
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("multi_attr.vhd", vhdl)
        result = self.parser.parse_file(filepath)
        self.assertIsNotNone(result, "Parser should return result for multi-attribute test")
        signals = result.get('signals', [])
        self.assertTrue(len(signals) > 0)
        multi_sig = self._get_signal_by_name(signals, 'multi')
        self.assertIsNotNone(multi_sig)
        self.assertEqual(multi_sig['access'], 'RW')
        self.assertEqual(multi_sig['address'], 0x10)
    
    # =========================================================================
    # PARSER-004: @axion_def Module Definition Parsing
    # =========================================================================
    def test_parser_004_base_addr_hex(self):
        """PARSER-004: Parse BASE_ADDR in hex format"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x1000
entity base_addr_test is
    port (clk : in std_logic);
end entity;
architecture rtl of base_addr_test is
    signal my_reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("base_addr_test.vhd", vhdl)
        result = self.parser.parse_file(filepath)
        self.assertEqual(result.get('base_addr'), 0x1000)
    
    def test_parser_004_cdc_enable(self):
        """PARSER-004: Parse CDC_EN flag"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN
entity cdc_test is
    port (clk : in std_logic);
end entity;
architecture rtl of cdc_test is
    signal my_reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("cdc_test.vhd", vhdl)
        result = self.parser.parse_file(filepath)
        self.assertTrue(result.get('cdc_en', False))
    
    def test_parser_004_cdc_stage(self):
        """PARSER-004: Parse CDC_STAGE attribute"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN CDC_STAGE=3
entity cdc_stage_test is
    port (clk : in std_logic);
end entity;
architecture rtl of cdc_stage_test is
    signal my_reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("cdc_stage_test.vhd", vhdl)
        result = self.parser.parse_file(filepath)
        self.assertEqual(result.get('cdc_stage', 2), 3)
    
    def test_parser_004_missing_axion_def_defaults(self):
        """PARSER-004: Default values when @axion_def missing"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
entity no_def_test is
    port (clk : in std_logic);
end entity;
architecture rtl of no_def_test is
    signal my_reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("no_def_test.vhd", vhdl)
        result = self.parser.parse_file(filepath)
        self.assertEqual(result.get('base_addr', 0), 0)
        self.assertFalse(result.get('cdc_en', False))
    
    # =========================================================================
    # PARSER-005: Decimal and Hexadecimal Address Parsing
    # =========================================================================
    def test_parser_005_hex_address(self):
        """PARSER-005: Parse hex address (0x10)"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity hex_addr is
    port (clk : in std_logic);
end entity;
architecture rtl of hex_addr is
    signal hex_reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x10
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("hex_addr.vhd", vhdl)
        result = self.parser.parse_file(filepath)
        signals = result.get('signals', [])
        self.assertTrue(any(s['address'] == 16 for s in signals))
    
    def test_parser_005_decimal_address(self):
        """PARSER-005: Parse decimal address (16)"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity dec_addr is
    port (clk : in std_logic);
end entity;
architecture rtl of dec_addr is
    signal dec_reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=16
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("dec_addr.vhd", vhdl)
        result = self.parser.parse_file(filepath)
        signals = result.get('signals', [])
        self.assertTrue(any(s['address'] == 16 for s in signals))
    
    def test_parser_005_upper_case_hex(self):
        """PARSER-005: Parse uppercase hex (0X10)"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0X0000
entity upper_hex is
    port (clk : in std_logic);
end entity;
architecture rtl of upper_hex is
    signal upper_reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0X10
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("upper_hex.vhd", vhdl)
        result = self.parser.parse_file(filepath)
        signals = result.get('signals', [])
        self.assertTrue(any(s['address'] == 16 for s in signals))
    
    # =========================================================================
    # PARSER-006: Quoted Description Parsing
    # =========================================================================
    def test_parser_006_double_quoted_desc(self):
        """PARSER-006: Parse double-quoted description"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity desc_test is
    port (clk : in std_logic);
end entity;
architecture rtl of desc_test is
    signal my_reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00 DESC="This is a test register"
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("desc_test.vhd", vhdl)
        result = self.parser.parse_file(filepath)
        signals = result.get('signals', [])
        self.assertTrue(any('test register' in s.get('description', '') for s in signals))
    
    def test_parser_006_desc_with_special_chars(self):
        """PARSER-006: Parse description with special characters"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity special_desc is
    port (clk : in std_logic);
end entity;
architecture rtl of special_desc is
    signal special_reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00 DESC="Temperature: -40 to +125 deg C"
begin
end architecture;
'''
        filepath = self._write_temp_vhdl("special_desc.vhd", vhdl)
        result = self.parser.parse_file(filepath)
        signals = result.get('signals', [])
        # Just check that parsing doesn't fail
        self.assertTrue(len(signals) > 0)
    
    # =========================================================================
    # PARSER-007: File Exclusion Pattern Support
    # =========================================================================
    def test_parser_007_exclude_directory(self):
        """PARSER-007: Exclude directory by name"""
        # Create subdirectory with VHDL file
        exclude_dir = os.path.join(self.temp_dir, "error_cases")
        os.makedirs(exclude_dir)
        
        vhdl_main = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity main_module is
    port (clk : in std_logic);
end entity;
architecture rtl of main_module is
    signal reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        vhdl_exclude = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity exclude_module is
    port (clk : in std_logic);
end entity;
architecture rtl of exclude_module is
    signal reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        self._write_temp_vhdl("main_module.vhd", vhdl_main)
        with open(os.path.join(exclude_dir, "exclude_module.vhd"), 'w') as f:
            f.write(vhdl_exclude)
        
        from axion_hdl import AxionHDL
        axion = AxionHDL(output_dir=os.path.join(self.temp_dir, "output"))
        axion.add_src(self.temp_dir)
        axion.exclude("error_cases")
        axion.analyze()
        
        # Should only find main_module, not exclude_module
        modules = axion.get_modules()
        module_names = [m.get('entity_name') for m in modules]
        self.assertIn('main_module', module_names)
        self.assertNotIn('exclude_module', module_names)
    
    # =========================================================================
    # PARSER-008: Recursive Directory Scanning
    # =========================================================================
    def test_parser_008_recursive_scan(self):
        """PARSER-008: Recursively scan subdirectories"""
        # Create nested directory structure
        sub1 = os.path.join(self.temp_dir, "level1")
        sub2 = os.path.join(sub1, "level2")
        os.makedirs(sub2)
        
        vhdl_root = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity root_module is port (clk : in std_logic); end entity;
architecture rtl of root_module is
    signal reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin end architecture;
'''
        vhdl_level1 = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x1000
entity level1_module is port (clk : in std_logic); end entity;
architecture rtl of level1_module is
    signal reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin end architecture;
'''
        vhdl_level2 = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x2000
entity level2_module is port (clk : in std_logic); end entity;
architecture rtl of level2_module is
    signal reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin end architecture;
'''
        self._write_temp_vhdl("root_module.vhd", vhdl_root)
        with open(os.path.join(sub1, "level1_module.vhd"), 'w') as f:
            f.write(vhdl_level1)
        with open(os.path.join(sub2, "level2_module.vhd"), 'w') as f:
            f.write(vhdl_level2)
        
        from axion_hdl import AxionHDL
        axion = AxionHDL(output_dir=os.path.join(self.temp_dir, "output"))
        axion.add_src(self.temp_dir)
        axion.analyze()
        
        modules = axion.get_modules()
        module_names = [m.get('entity_name') for m in modules]
        self.assertIn('root_module', module_names)
        self.assertIn('level1_module', module_names)
        self.assertIn('level2_module', module_names)


def run_parser_tests():
    """Run all parser tests and return results"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestParserRequirements)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_parser_tests()
    sys.exit(0 if success else 1)
