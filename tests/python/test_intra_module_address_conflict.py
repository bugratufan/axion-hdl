#!/usr/bin/env python3
"""
test_intra_module_address_conflict.py - Intra-Module Address Conflict Tests

Tests for detecting address conflicts within a single module, including:
1. Exact duplicate addresses (two registers at same address)
2. Wide register overlap (64-bit register at 0x00 + 32-bit at 0x04)

Tests all input formats: YAML, JSON, XML, and VHDL.
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from axion_hdl import AxionHDL
from axion_hdl.rule_checker import RuleChecker


class TestIntraModuleAddressConflict(unittest.TestCase):
    """Test cases for intra-module address conflict detection"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def tearDown(self):
        """Clean up temp files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _run_rule_checker(self, modules):
        """Run rule checker and return results"""
        checker = RuleChecker()
        return checker.run_all_checks(modules)
    
    # =========================================================================
    # TEST: Exact Duplicate Address Detection
    # =========================================================================
    
    def test_yaml_duplicate_address(self):
        """YAML: Detect two registers at same address"""
        yaml_content = """
module: spi_master
base_addr: "0x1000"
config:
  cdc_en: true
registers:
  - name: control
    addr: "0x04"
    access: RW
    description: SPI control register
  - name: status
    addr: "0x04"
    access: RO
    description: SPI status register
"""
        # Write YAML file
        yaml_path = os.path.join(self.temp_dir, "spi.yaml")
        with open(yaml_path, 'w') as f:
            f.write(yaml_content)
        
        # Parse and check
        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_source(self.temp_dir)
        axion.analyze()
        
        # Run rule checker
        results = self._run_rule_checker(axion.analyzed_modules)
        
        # Should have errors
        self.assertTrue(len(results['errors']) > 0, 
            "Should detect duplicate address conflict")
        
        # Check for specific error message
        error_msgs = [e['msg'] for e in results['errors']]
        has_conflict = any('0x1004' in msg or 'control' in msg or 'status' in msg 
                          for msg in error_msgs)
        self.assertTrue(has_conflict, 
            f"Should mention conflicting registers. Errors: {error_msgs}")
    
    def test_json_duplicate_address(self):
        """JSON: Detect two registers at same address"""
        json_content = {
            "module": "uart_controller",
            "base_addr": "0x2000",
            "registers": [
                {
                    "name": "tx_data",
                    "addr": "0x00",
                    "access": "WO"
                },
                {
                    "name": "rx_data",
                    "addr": "0x00",
                    "access": "RO"
                }
            ]
        }
        
        # Write JSON file
        json_path = os.path.join(self.temp_dir, "uart.json")
        with open(json_path, 'w') as f:
            json.dump(json_content, f)
        
        # Parse and check
        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_source(self.temp_dir)
        axion.analyze()
        
        results = self._run_rule_checker(axion.analyzed_modules)
        
        self.assertTrue(len(results['errors']) > 0,
            "Should detect duplicate address conflict in JSON")
        
        error_msgs = [e['msg'] for e in results['errors']]
        has_conflict = any('tx_data' in msg or 'rx_data' in msg for msg in error_msgs)
        self.assertTrue(has_conflict,
            f"Should mention conflicting registers. Errors: {error_msgs}")
    
    def test_xml_duplicate_address(self):
        """XML: Detect two registers at same address"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<register_map module="gpio_controller" base_addr="0x3000">
    <register name="direction" addr="0x08" access="RW">
        <description>GPIO direction register</description>
    </register>
    <register name="output" addr="0x08" access="RW">
        <description>GPIO output register</description>
    </register>
</register_map>
"""
        # Write XML file
        xml_path = os.path.join(self.temp_dir, "gpio.xml")
        with open(xml_path, 'w') as f:
            f.write(xml_content)
        
        # Parse and check
        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_source(self.temp_dir)
        axion.analyze()
        
        results = self._run_rule_checker(axion.analyzed_modules)
        
        self.assertTrue(len(results['errors']) > 0,
            "Should detect duplicate address conflict in XML")
    
    def test_vhdl_duplicate_address(self):
        """VHDL: Detect two registers at same address"""
        vhdl_content = """
library ieee;
use ieee.std_logic_1164.all;

-- @axion_def BASE_ADDR=0x4000

entity timer_module is
    port (clk : in std_logic);
end entity;

architecture rtl of timer_module is
    signal counter : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
    signal reload : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x00
begin
end architecture;
"""
        # Write VHDL file
        vhdl_path = os.path.join(self.temp_dir, "timer.vhd")
        with open(vhdl_path, 'w') as f:
            f.write(vhdl_content)
        
        # Parse - VHDL parser should catch this
        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_source(self.temp_dir)
        axion.analyze()
        
        # First check parsing errors
        parsing_errors = []
        for module in axion.analyzed_modules:
            parsing_errors.extend(module.get('parsing_errors', []))
        
        # Run rule checker  
        results = self._run_rule_checker(axion.analyzed_modules)
        
        # Should have errors from either parsing or rule checker
        total_errors = len(results['errors']) + len(parsing_errors)
        self.assertTrue(total_errors > 0,
            "Should detect duplicate address in VHDL")
    
    # =========================================================================
    # TEST: Wide Register Overlap Detection
    # =========================================================================
    
    def test_yaml_wide_register_overlap(self):
        """YAML: Detect overlap when wide register spans multiple addresses"""
        yaml_content = """
module: dma_controller
base_addr: "0x5000"
registers:
  - name: buffer_addr
    addr: "0x00"
    width: 64
    access: RW
    description: 64-bit buffer address (occupies 0x00-0x07)
  - name: control
    addr: "0x04"
    width: 32
    access: RW
    description: Control register - CONFLICTS with buffer_addr!
"""
        yaml_path = os.path.join(self.temp_dir, "dma.yaml")
        with open(yaml_path, 'w') as f:
            f.write(yaml_content)
        
        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_source(self.temp_dir)
        axion.analyze()
        
        results = self._run_rule_checker(axion.analyzed_modules)
        
        self.assertTrue(len(results['errors']) > 0,
            "Should detect wide register overlap")
        
        error_msgs = [e['msg'] for e in results['errors']]
        has_overlap = any('overlap' in msg.lower() or 'conflict' in msg.lower() 
                         for msg in error_msgs)
        self.assertTrue(has_overlap,
            f"Should mention overlap or conflict. Errors: {error_msgs}")
    
    def test_json_wide_register_overlap(self):
        """JSON: 96-bit register at 0x10 overlaps with 32-bit at 0x18"""
        json_content = {
            "module": "crypto_engine",
            "base_addr": "0x6000",
            "registers": [
                {
                    "name": "key_data",
                    "addr": "0x10",
                    "width": 96,
                    "access": "WO",
                    "description": "96-bit key (0x10-0x1B)"
                },
                {
                    "name": "status",
                    "addr": "0x18",
                    "width": 32,
                    "access": "RO",
                    "description": "Conflicts with key_data"
                }
            ]
        }
        
        json_path = os.path.join(self.temp_dir, "crypto.json")
        with open(json_path, 'w') as f:
            json.dump(json_content, f)
        
        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_source(self.temp_dir)
        axion.analyze()
        
        results = self._run_rule_checker(axion.analyzed_modules)
        
        self.assertTrue(len(results['errors']) > 0,
            "Should detect 96-bit register overlap")
    
    def test_vhdl_wide_signal_overlap(self):
        """VHDL: 64-bit signal at 0x00 overlaps with 32-bit at 0x04"""
        vhdl_content = """
library ieee;
use ieee.std_logic_1164.all;

-- @axion_def BASE_ADDR=0x7000

entity wide_test is
    port (clk : in std_logic);
end entity;

architecture rtl of wide_test is
    signal wide_data : std_logic_vector(63 downto 0); -- @axion RW ADDR=0x00
    signal overlap_reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x04
begin
end architecture;
"""
        vhdl_path = os.path.join(self.temp_dir, "wide_test.vhd")
        with open(vhdl_path, 'w') as f:
            f.write(vhdl_content)
        
        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_source(self.temp_dir)
        axion.analyze()
        
        # Check both parsing errors and rule checker
        parsing_errors = []
        for module in axion.analyzed_modules:
            parsing_errors.extend(module.get('parsing_errors', []))
        
        results = self._run_rule_checker(axion.analyzed_modules)
        
        total_errors = len(results['errors']) + len(parsing_errors)
        self.assertTrue(total_errors > 0,
            "Should detect wide signal overlap in VHDL")
    
    # =========================================================================
    # TEST: No False Positives
    # =========================================================================
    
    def test_no_conflict_valid_addresses(self):
        """Should not report errors for valid non-overlapping addresses"""
        yaml_content = """
module: valid_module
base_addr: "0x0000"
registers:
  - name: reg_a
    addr: "0x00"
    width: 32
    access: RW
  - name: reg_b
    addr: "0x04"
    width: 32
    access: RW
  - name: reg_c
    addr: "0x08"
    width: 32
    access: RO
"""
        yaml_path = os.path.join(self.temp_dir, "valid.yaml")
        with open(yaml_path, 'w') as f:
            f.write(yaml_content)
        
        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_source(self.temp_dir)
        axion.analyze()
        
        results = self._run_rule_checker(axion.analyzed_modules)
        
        # Filter for address-related errors only
        addr_errors = [e for e in results['errors'] 
                      if 'Address' in e['type'] or 'Duplicate' in e['type']]
        
        self.assertEqual(len(addr_errors), 0,
            f"Should not report address errors for valid config. Got: {addr_errors}")
    
    def test_no_conflict_wide_register_correct_spacing(self):
        """64-bit at 0x00 and 32-bit at 0x08 should NOT conflict"""
        yaml_content = """
module: proper_spacing
base_addr: "0x0000"
registers:
  - name: wide_reg
    addr: "0x00"
    width: 64
    access: RW
    description: 64-bit uses 0x00-0x07
  - name: next_reg
    addr: "0x08"
    width: 32
    access: RW
    description: Starts at 0x08, no conflict
"""
        yaml_path = os.path.join(self.temp_dir, "proper.yaml")
        with open(yaml_path, 'w') as f:
            f.write(yaml_content)
        
        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_source(self.temp_dir)
        axion.analyze()
        
        results = self._run_rule_checker(axion.analyzed_modules)
        
        addr_errors = [e for e in results['errors'] 
                      if 'Address' in e['type'] or 'Overlap' in e['type']]
        
        self.assertEqual(len(addr_errors), 0,
            f"64-bit at 0x00 and 32-bit at 0x08 should not conflict. Got: {addr_errors}")


def run_tests():
    """Run all intra-module address conflict tests"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestIntraModuleAddressConflict)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
