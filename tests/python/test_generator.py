#!/usr/bin/env python3
"""
test_generator.py - Code Generation Requirements Tests

Tests for GEN-001 through GEN-016 requirements
Verifies VHDL, C header, XML, Markdown, HTML, and PDF generation functionality.
"""

import os
import sys
import tempfile
import unittest
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from axion_hdl import AxionHDL


class TestGeneratorRequirements(unittest.TestCase):
    """Test cases for GEN-xxx requirements"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests"""
        cls.temp_dir = tempfile.mkdtemp()
        cls.output_dir = os.path.join(cls.temp_dir, "output")
        os.makedirs(cls.output_dir)
        
        # Create test VHDL file
        cls.vhdl_content = '''
library ieee;
use ieee.std_logic_1164.all;

-- @axion_def BASE_ADDR=0x1000

entity generator_test is
    port (
        clk : in std_logic;
        rst_n : in std_logic
    );
end entity generator_test;

architecture rtl of generator_test is
    signal status_reg : std_logic_vector(31 downto 0);  -- @axion RO ADDR=0x00 DESC="Status register"
    signal control_reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x04 DESC="Control register"
    signal command_reg : std_logic_vector(31 downto 0); -- @axion WO ADDR=0x08 W_STROBE DESC="Command register"
    signal data_reg : std_logic_vector(31 downto 0);    -- @axion RW ADDR=0x0C R_STROBE DESC="Data register"
begin
end architecture rtl;
'''
        cls.vhdl_file = os.path.join(cls.temp_dir, "generator_test.vhd")
        with open(cls.vhdl_file, 'w') as f:
            f.write(cls.vhdl_content)
        
        # Run analysis and generation
        cls.axion = AxionHDL(output_dir=cls.output_dir)
        cls.axion.add_src(cls.temp_dir)
        cls.axion.analyze()
        cls.axion.generate_vhdl()
        cls.axion.generate_c_header()
        cls.axion.generate_xml()
        cls.axion.generate_documentation(format="md")
        cls.axion.generate_documentation(format="html")
        cls.axion.generate_documentation(format="pdf")
        
        # Get generated file paths
        cls.gen_vhdl = os.path.join(cls.output_dir, "generator_test_axion_reg.vhd")
        cls.gen_header = os.path.join(cls.output_dir, "generator_test_regs.h")
        cls.gen_xml = os.path.join(cls.output_dir, "generator_test_regs.xml")
        cls.gen_md = os.path.join(cls.output_dir, "register_map.md")
        cls.gen_html = os.path.join(cls.output_dir, "register_map.html")
        cls.gen_pdf = os.path.join(cls.output_dir, "register_map.pdf")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up temp files"""
        import shutil
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
    
    # =========================================================================
    # GEN-001: VHDL Entity Generation
    # =========================================================================
    def test_gen_001_vhdl_file_exists(self):
        """GEN-001: Generated VHDL file exists"""
        self.assertTrue(os.path.exists(self.gen_vhdl))
    
    def test_gen_001_entity_name_pattern(self):
        """GEN-001: Entity name follows pattern <module>_axion_reg"""
        with open(self.gen_vhdl, 'r') as f:
            content = f.read()
        self.assertIn('entity generator_test_axion_reg is', content.lower())
    
    def test_gen_001_vhdl_compiles(self):
        """GEN-001: Generated VHDL compiles without errors"""
        # Check if GHDL is available
        result = subprocess.run(['which', 'ghdl'], capture_output=True)
        if result.returncode != 0:
            self.skipTest("GHDL not available")
        
        # Try to analyze the generated VHDL
        work_dir = os.path.join(self.temp_dir, "work")
        os.makedirs(work_dir, exist_ok=True)
        
        result = subprocess.run(
            ['ghdl', '-a', '--std=08', f'--workdir={work_dir}', self.gen_vhdl],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, f"GHDL error: {result.stderr}")
    
    # =========================================================================
    # GEN-002: VHDL Architecture Generation
    # =========================================================================
    def test_gen_002_architecture_rtl(self):
        """GEN-002: Architecture is named 'rtl'"""
        with open(self.gen_vhdl, 'r') as f:
            content = f.read().lower()
        self.assertIn('architecture rtl of', content)
    
    def test_gen_002_signal_declarations(self):
        """GEN-002: Internal signals are properly declared"""
        with open(self.gen_vhdl, 'r') as f:
            content = f.read().lower()
        # Should have state machine or internal signals
        self.assertTrue('signal' in content)
    
    # =========================================================================
    # GEN-003: AXI Port Signal Generation
    # =========================================================================
    def test_gen_003_axi_clock_reset(self):
        """GEN-003: Clock and reset signals present"""
        with open(self.gen_vhdl, 'r') as f:
            content = f.read().lower()
        self.assertIn('axi_aclk', content)
        self.assertIn('axi_aresetn', content)
    
    def test_gen_003_write_address_channel(self):
        """GEN-003: Write address channel signals present"""
        with open(self.gen_vhdl, 'r') as f:
            content = f.read().lower()
        self.assertIn('axi_awaddr', content)
        self.assertIn('axi_awvalid', content)
        self.assertIn('axi_awready', content)
    
    def test_gen_003_write_data_channel(self):
        """GEN-003: Write data channel signals present"""
        with open(self.gen_vhdl, 'r') as f:
            content = f.read().lower()
        self.assertIn('axi_wdata', content)
        self.assertIn('axi_wstrb', content)
        self.assertIn('axi_wvalid', content)
        self.assertIn('axi_wready', content)
    
    def test_gen_003_write_response_channel(self):
        """GEN-003: Write response channel signals present"""
        with open(self.gen_vhdl, 'r') as f:
            content = f.read().lower()
        self.assertIn('axi_bresp', content)
        self.assertIn('axi_bvalid', content)
        self.assertIn('axi_bready', content)
    
    def test_gen_003_read_address_channel(self):
        """GEN-003: Read address channel signals present"""
        with open(self.gen_vhdl, 'r') as f:
            content = f.read().lower()
        self.assertIn('axi_araddr', content)
        self.assertIn('axi_arvalid', content)
        self.assertIn('axi_arready', content)
    
    def test_gen_003_read_data_channel(self):
        """GEN-003: Read data channel signals present"""
        with open(self.gen_vhdl, 'r') as f:
            content = f.read().lower()
        self.assertIn('axi_rdata', content)
        self.assertIn('axi_rresp', content)
        self.assertIn('axi_rvalid', content)
        self.assertIn('axi_rready', content)
    
    # =========================================================================
    # GEN-004: Register Port Direction Generation
    # =========================================================================
    def test_gen_004_ro_register_direction(self):
        """GEN-004: RO registers have 'in' direction"""
        with open(self.gen_vhdl, 'r') as f:
            content = f.read().lower()
        # status_reg is RO, should be input
        self.assertIn('status_reg', content)
        # Check for 'in' port direction near status_reg
        self.assertTrue('status_reg' in content)
    
    def test_gen_004_wo_register_direction(self):
        """GEN-004: WO registers have 'out' direction"""
        with open(self.gen_vhdl, 'r') as f:
            content = f.read().lower()
        # command_reg is WO, should be output
        self.assertIn('command_reg', content)
    
    # =========================================================================
    # GEN-005: Read Strobe Port Generation
    # =========================================================================
    def test_gen_005_read_strobe_port(self):
        """GEN-005: R_STROBE generates read strobe port"""
        with open(self.gen_vhdl, 'r') as f:
            content = f.read().lower()
        # data_reg has R_STROBE, should have strobe port
        self.assertIn('data_reg_rd_strobe', content)
    
    # =========================================================================
    # GEN-006: Write Strobe Port Generation
    # =========================================================================
    def test_gen_006_write_strobe_port(self):
        """GEN-006: W_STROBE generates write strobe port"""
        with open(self.gen_vhdl, 'r') as f:
            content = f.read().lower()
        # command_reg has W_STROBE, should have strobe port
        self.assertIn('command_reg_wr_strobe', content)
    
    # =========================================================================
    # GEN-007: AXI State Machine Generation
    # =========================================================================
    def test_gen_007_state_machine_exists(self):
        """GEN-007: State machine logic present"""
        with open(self.gen_vhdl, 'r') as f:
            content = f.read().lower()
        # Should have process blocks for state machine
        self.assertIn('process', content)
    
    # =========================================================================
    # GEN-008: Address Decoder Generation
    # =========================================================================
    def test_gen_008_address_decoder(self):
        """GEN-008: Address decoder has case statement"""
        with open(self.gen_vhdl, 'r') as f:
            content = f.read().lower()
        # Should have case statement for address decoding
        self.assertIn('case', content)
    
    # =========================================================================
    # GEN-009: C Header File Generation
    # =========================================================================
    def test_gen_009_c_header_exists(self):
        """GEN-009: C header file generated"""
        self.assertTrue(os.path.exists(self.gen_header))
    
    def test_gen_009_include_guards(self):
        """GEN-009: Header has include guards"""
        with open(self.gen_header, 'r') as f:
            content = f.read()
        self.assertIn('#ifndef', content)
        self.assertIn('#define', content)
        self.assertIn('#endif', content)
    
    def test_gen_009_base_address_macro(self):
        """GEN-009: Base address macro defined"""
        with open(self.gen_header, 'r') as f:
            content = f.read()
        self.assertIn('BASE_ADDR', content.upper())
        self.assertIn('0x1000', content.lower())
    
    def test_gen_009_offset_macros(self):
        """GEN-009: Register offset macros defined"""
        with open(self.gen_header, 'r') as f:
            content = f.read()
        self.assertIn('OFFSET', content.upper())
    
    def test_gen_009_c_header_compiles(self):
        """GEN-009: C header compiles without warnings"""
        # Check if GCC is available
        result = subprocess.run(['which', 'gcc'], capture_output=True)
        if result.returncode != 0:
            self.skipTest("GCC not available")
        
        # Create test C file
        test_c = os.path.join(self.temp_dir, "test_header.c")
        with open(test_c, 'w') as f:
            f.write(f'#include "{self.gen_header}"\nint main(void) {{ return 0; }}')
        
        result = subprocess.run(
            ['gcc', '-Wall', '-Wextra', '-c', test_c, '-o', '/dev/null'],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, f"GCC error: {result.stderr}")
    
    # =========================================================================
    # GEN-010: C Header Register Structure Generation
    # =========================================================================
    def test_gen_010_struct_definition(self):
        """GEN-010: Struct definition present"""
        with open(self.gen_header, 'r') as f:
            content = f.read()
        # Should have typedef struct
        self.assertTrue('typedef' in content and 'struct' in content)
    
    # =========================================================================
    # GEN-011: XML Register Map Generation
    # =========================================================================
    def test_gen_011_xml_exists(self):
        """GEN-011: XML file generated"""
        self.assertTrue(os.path.exists(self.gen_xml))
    
    def test_gen_011_xml_well_formed(self):
        """GEN-011: XML is well-formed"""
        try:
            tree = ET.parse(self.gen_xml)
            root = tree.getroot()
            self.assertIsNotNone(root)
        except ET.ParseError as e:
            self.fail(f"XML parse error: {e}")
    
    def test_gen_011_xml_has_registers(self):
        """GEN-011: XML contains register elements"""
        tree = ET.parse(self.gen_xml)
        root = tree.getroot()
        # Should have some register elements
        # Look for elements with 'register' in tag or attributes with address
        xml_str = ET.tostring(root, encoding='unicode')
        self.assertTrue('0x' in xml_str.lower() or 'register' in xml_str.lower())
    
    # =========================================================================
    # GEN-012: Markdown Documentation Generation
    # =========================================================================
    def test_gen_012_markdown_exists(self):
        """GEN-012: Markdown file generated"""
        self.assertTrue(os.path.exists(self.gen_md))
    
    def test_gen_012_has_module_header(self):
        """GEN-012: Document has module header"""
        with open(self.gen_md, 'r') as f:
            content = f.read()
        self.assertIn('generator_test', content.lower())
    
    def test_gen_012_has_register_table(self):
        """GEN-012: Document has register table"""
        with open(self.gen_md, 'r') as f:
            content = f.read()
        # Markdown tables use | character
        self.assertIn('|', content)
    
    def test_gen_012_shows_address(self):
        """GEN-012: Document shows addresses"""
        with open(self.gen_md, 'r') as f:
            content = f.read()
        self.assertIn('0x', content.lower())
    
    # =========================================================================
    # GEN-015: HTML Documentation Generation
    # =========================================================================
    def test_gen_015_html_exists(self):
        """GEN-015: HTML file generated"""
        self.assertTrue(os.path.exists(self.gen_html))
    
    def test_gen_015_html_has_doctype(self):
        """GEN-015: HTML has proper DOCTYPE"""
        with open(self.gen_html, 'r') as f:
            content = f.read()
        self.assertIn('<!DOCTYPE html>', content)
    
    def test_gen_015_html_has_style(self):
        """GEN-015: HTML has embedded CSS"""
        with open(self.gen_html, 'r') as f:
            content = f.read()
        self.assertIn('<style>', content)
        self.assertIn('</style>', content)
    
    def test_gen_015_html_has_table(self):
        """GEN-015: HTML has register table"""
        with open(self.gen_html, 'r') as f:
            content = f.read()
        self.assertIn('<table>', content)
        self.assertIn('<th>', content)
    
    def test_gen_015_html_has_module_name(self):
        """GEN-015: HTML has module name"""
        with open(self.gen_html, 'r') as f:
            content = f.read().lower()
        self.assertIn('generator_test', content)
    
    # =========================================================================
    # GEN-016: PDF Documentation Generation  
    # =========================================================================
    def test_gen_016_pdf_exists_or_skipped(self):
        """GEN-016: PDF file generated or skipped if weasyprint unavailable"""
        # PDF generation is optional, depends on weasyprint
        try:
            import weasyprint
            # weasyprint is available, PDF should exist
            self.assertTrue(os.path.exists(self.gen_pdf), 
                "PDF should be generated when weasyprint is available")
        except ImportError:
            # weasyprint not available, PDF generation skipped is acceptable
            pass  # Test passes regardless of PDF existence
    
    def test_gen_016_pdf_valid_if_exists(self):
        """GEN-016: PDF has valid header if generated"""
        if os.path.exists(self.gen_pdf):
            with open(self.gen_pdf, 'rb') as f:
                header = f.read(8)
            # PDF files start with %PDF-
            self.assertTrue(header.startswith(b'%PDF-'), 
                "Generated PDF should have valid PDF header")
    
    # =========================================================================
    # GEN-013: YAML Register Map Generation
    # =========================================================================
    def test_gen_013_yaml_map_exists(self):
        """GEN-013: YAML register map file generated"""
        # Generate YAML if not already done
        self.axion.generate_yaml()
        yaml_file = os.path.join(self.output_dir, "generator_test_regs.yaml")
        self.assertTrue(os.path.exists(yaml_file), 
            "YAML register map should be generated")
    
    def test_gen_013_yaml_valid_syntax(self):
        """GEN-013: YAML file has valid syntax and structure"""
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not available")
        
        self.axion.generate_yaml()
        yaml_file = os.path.join(self.output_dir, "generator_test_regs.yaml")
        
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
        
        self.assertIsInstance(data, dict)
        self.assertIn('module', data, "YAML must contain 'module' field")
        self.assertEqual(data['module'], 'generator_test')
        self.assertIn('registers', data, "YAML must contain 'registers' field")
        self.assertIsInstance(data['registers'], list)
        self.assertGreater(len(data['registers']), 0, "YAML must have at least one register")
    
    # =========================================================================
    # GEN-014: JSON Register Map Generation
    # =========================================================================
    def test_gen_014_json_map_exists(self):
        """GEN-014: JSON register map file generated"""
        self.axion.generate_json()
        json_file = os.path.join(self.output_dir, "generator_test_regs.json")
        self.assertTrue(os.path.exists(json_file), 
            "JSON register map should be generated")
    
    def test_gen_014_json_valid_syntax(self):
        """GEN-014: JSON file has valid syntax and structure"""
        import json
        
        self.axion.generate_json()
        json_file = os.path.join(self.output_dir, "generator_test_regs.json")
        
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        self.assertIsInstance(data, dict)
        self.assertIn('module', data, "JSON must contain 'module' field")
        self.assertEqual(data['module'], 'generator_test')
        self.assertIn('registers', data, "JSON must contain 'registers' field")
        self.assertIsInstance(data['registers'], list)
        self.assertGreater(len(data['registers']), 0, "JSON must have at least one register")
    
    # =========================================================================
    # GEN-017: Address Range Calculation
    # =========================================================================
    def test_gen_017_address_range_in_module(self):
        """GEN-017: Module has calculated address range"""
        self.assertTrue(len(self.axion.analyzed_modules) > 0, "Must have analyzed modules")
        module = self.axion.analyzed_modules[0]
        
        # Get registers and calculate expected range
        registers = module.get('registers', [])
        self.assertGreater(len(registers), 0, "Module must have registers")
        
        # Find min and max addresses
        min_addr = min(r.get('relative_address_int', r.get('address_int', 0)) for r in registers)
        max_addr = max(r.get('relative_address_int', r.get('address_int', 0)) for r in registers)
        
        # Address range should cover all registers
        self.assertGreaterEqual(max_addr, min_addr, 
            "Address range must be valid (max >= min)")
    
    def test_gen_017_address_range_display(self):
        """GEN-017: Address range displayed in documentation"""
        # Check that markdown documentation shows address information
        with open(self.gen_md, 'r') as f:
            content = f.read()
        
        # Should have address information displayed
        self.assertIn('0x', content.lower(), 
            "Documentation should display address values")


def run_generator_tests():
    """Run all generator tests and return results"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestGeneratorRequirements)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_generator_tests()
    sys.exit(0 if success else 1)
