#!/usr/bin/env python3
"""
test_xdc.py - XDC Constraint Generation Requirements Tests

Tests for XDC-001 through XDC-012 requirements
Verifies instance-independent Xilinx XDC false-path constraint generation.
"""

import os
import sys
import tempfile
import unittest
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from axion_hdl import AxionHDL


CDC_VHDL = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN CDC_STAGE=2
entity xdc_cdc_test is
    port (clk : in std_logic);
end entity;
architecture rtl of xdc_cdc_test is
    signal status_reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00 R_STROBE
    signal config_reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x04 W_STROBE
    signal tx_reg     : std_logic_vector(15 downto 0); -- @axion WO ADDR=0x08
    signal enable_bit : std_logic;                     -- @axion RW ADDR=0x0C
begin
end architecture;
'''

NOCDC_VHDL = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN=false
entity xdc_nocdc_test is
    port (clk : in std_logic);
end entity;
architecture rtl of xdc_nocdc_test is
    signal plain_reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x00
begin
end architecture;
'''

PACKED_VHDL = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN=false
entity xdc_packed_test is
    port (clk : in std_logic);
end entity;
architecture rtl of xdc_packed_test is
    signal ctrl_enable : std_logic;                    -- @axion RW ADDR=0x00 REG_NAME=control BIT_OFFSET=0
    signal ctrl_mode   : std_logic_vector(1 downto 0); -- @axion RW ADDR=0x00 REG_NAME=control BIT_OFFSET=1
    signal stat_busy   : std_logic;                    -- @axion RO ADDR=0x04 REG_NAME=status BIT_OFFSET=0
begin
end architecture;
'''

YAML_INPUT = '''
module: xdc_yaml_test
base_addr: "0x2000"

config:
  cdc_en: false

registers:
  - name: yaml_status
    addr: "0x00"
    access: RO
    width: 32
    description: "Status from YAML"
  - name: yaml_config
    addr: "0x04"
    access: RW
    width: 32
    description: "Config from YAML"
'''


class TestXDCRequirements(unittest.TestCase):
    """Test cases for XDC-xxx requirements"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, "output")

    def tearDown(self):
        """Clean up temp files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_source(self, filename: str, content: str) -> str:
        """Write source content to temp file and return path"""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath

    def _generate_xdc(self, content: str, module_name: str,
                      extension: str = "vhd") -> str:
        """Generate XDC from source content and return the generated text"""
        src = self._write_source(f"{module_name}.{extension}", content)

        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_source(src)
        axion.analyze()
        self.assertTrue(axion.generate_xdc())

        gen_file = os.path.join(self.output_dir, f"{module_name}_axion_reg.xdc")
        self.assertTrue(os.path.exists(gen_file),
                        f"Expected XDC file not generated: {gen_file}")
        with open(gen_file, 'r') as f:
            return f.read()

    @staticmethod
    def _active_lines(xdc_content: str):
        """Return non-comment, non-empty lines of an XDC file"""
        return [line.strip() for line in xdc_content.splitlines()
                if line.strip() and not line.strip().startswith('#')]

    # =========================================================================
    # XDC-001: CLI Flag Generation
    # =========================================================================
    def test_xdc_001_cli_flag_generation(self):
        """XDC-001: --xdc generates one <module>_axion_reg.xdc per module"""
        self._write_source("xdc_cdc_test.vhd", CDC_VHDL)
        self._write_source("xdc_nocdc_test.vhd", NOCDC_VHDL)

        result = subprocess.run(
            [sys.executable, '-m', 'axion_hdl.cli',
             '-s', self.temp_dir, '-o', self.output_dir, '--xdc'],
            capture_output=True, text=True, cwd=str(project_root))
        self.assertEqual(result.returncode, 0, result.stderr)

        for module in ("xdc_cdc_test", "xdc_nocdc_test"):
            self.assertTrue(
                os.path.exists(os.path.join(
                    self.output_dir, f"{module}_axion_reg.xdc")),
                f"Missing XDC for module {module}")

    # =========================================================================
    # XDC-002: Instance Independence
    # =========================================================================
    def test_xdc_002_instance_independence(self):
        """XDC-002: cells located via REF_NAME/ORIG_REF_NAME, no instance paths"""
        content = self._generate_xdc(CDC_VHDL, "xdc_cdc_test")

        self.assertIn("get_cells -hierarchical", content)
        self.assertIn("REF_NAME == xdc_cdc_test_axion_reg", content)
        self.assertIn("ORIG_REF_NAME == xdc_cdc_test_axion_reg", content)

        # Every hierarchy separator in active constraints must be part of a
        # wildcard pin pattern (*/...), never a hard-coded instance path.
        for line in self._active_lines(content):
            for idx, char in enumerate(line):
                if char == '/':
                    self.assertEqual(line[idx - 1], '*',
                                     f"Hard-coded hierarchy path in: {line}")

    # =========================================================================
    # XDC-003: RO False Path Direction
    # =========================================================================
    def test_xdc_003_ro_false_path_to(self):
        """XDC-003: RO registers produce set_false_path -to constraints"""
        content = self._generate_xdc(CDC_VHDL, "xdc_cdc_test")
        to_lines = [l for l in self._active_lines(content)
                    if l.startswith("set_false_path -to")]
        self.assertTrue(any("*/status_reg" in l for l in to_lines),
                        "RO register status_reg must be false-pathed with -to")

    # =========================================================================
    # XDC-004: RW/WO False Path Direction
    # =========================================================================
    def test_xdc_004_rw_wo_false_path_from(self):
        """XDC-004: RW/WO registers produce set_false_path -from constraints"""
        content = self._generate_xdc(CDC_VHDL, "xdc_cdc_test")
        from_lines = [l for l in self._active_lines(content)
                      if l.startswith("set_false_path -from")]
        self.assertTrue(any("*/config_reg" in l for l in from_lines),
                        "RW register config_reg must be false-pathed with -from")
        self.assertTrue(any("*/tx_reg" in l for l in from_lines),
                        "WO register tx_reg must be false-pathed with -from")
        self.assertTrue(any("*/enable_bit" in l for l in from_lines),
                        "RW register enable_bit must be false-pathed with -from")

    # =========================================================================
    # XDC-005: Packed Field Constraints
    # =========================================================================
    def test_xdc_005_packed_field_constraints(self):
        """XDC-005: packed fields constrained as <reg_name>_<field_name>"""
        content = self._generate_xdc(PACKED_VHDL, "xdc_packed_test")
        active = self._active_lines(content)

        from_lines = [l for l in active if l.startswith("set_false_path -from")]
        to_lines = [l for l in active if l.startswith("set_false_path -to")]

        self.assertTrue(any("*/control_ctrl_enable" in l for l in from_lines))
        self.assertTrue(any("*/control_ctrl_mode" in l for l in from_lines))
        self.assertTrue(any("*/status_stat_busy" in l for l in to_lines))

    # =========================================================================
    # XDC-006: Strobe Exclusion
    # =========================================================================
    def test_xdc_006_strobe_exclusion(self):
        """XDC-006: strobe outputs are never actively false-pathed"""
        content = self._generate_xdc(CDC_VHDL, "xdc_cdc_test")

        for line in self._active_lines(content):
            self.assertNotIn("_rd_strobe", line,
                             f"Active constraint on read strobe: {line}")
            self.assertNotIn("_wr_strobe", line,
                             f"Active constraint on write strobe: {line}")

        # The strobes must still be documented as commented-out constraints
        commented = [l.strip() for l in content.splitlines()
                     if l.strip().startswith('#')]
        self.assertTrue(any("status_reg_rd_strobe" in l for l in commented))
        self.assertTrue(any("config_reg_wr_strobe" in l for l in commented))

    # =========================================================================
    # XDC-007: Vector Pin Coverage
    # =========================================================================
    def test_xdc_007_vector_pin_coverage(self):
        """XDC-007: pin filters match scalar name and vector bit pins"""
        content = self._generate_xdc(CDC_VHDL, "xdc_cdc_test")
        active = self._active_lines(content)

        config_lines = [l for l in active if "config_reg" in l]
        self.assertEqual(len(config_lines), 1)
        self.assertIn("NAME =~ */config_reg ", config_lines[0])
        self.assertIn("NAME =~ */config_reg[*]", config_lines[0])

    # =========================================================================
    # XDC-008: AXI Port Exclusion
    # =========================================================================
    def test_xdc_008_axi_port_exclusion(self):
        """XDC-008: AXI bus pins are never targeted by false paths"""
        content = self._generate_xdc(CDC_VHDL, "xdc_cdc_test")
        for line in self._active_lines(content):
            if line.startswith("set_false_path"):
                self.assertNotIn("axi_", line,
                                 f"AXI bus pin constrained: {line}")

    # =========================================================================
    # XDC-009: Non-CDC Warning Header
    # =========================================================================
    def test_xdc_009_non_cdc_warning(self):
        """XDC-009: warning header only for CDC-disabled modules"""
        nocdc_content = self._generate_xdc(NOCDC_VHDL, "xdc_nocdc_test")
        self.assertIn("CDC is DISABLED", nocdc_content)

        cdc_content = self._generate_xdc(CDC_VHDL, "xdc_cdc_test")
        self.assertNotIn("CDC is DISABLED", cdc_content)

    # =========================================================================
    # XDC-010: Explicit Opt-In
    # =========================================================================
    def test_xdc_010_explicit_opt_in(self):
        """XDC-010: --xdc generates only XDC; --all does not emit XDC"""
        self._write_source("xdc_cdc_test.vhd", CDC_VHDL)

        # --xdc alone must not fall back to --all
        out_xdc = os.path.join(self.temp_dir, "out_xdc")
        result = subprocess.run(
            [sys.executable, '-m', 'axion_hdl.cli',
             '-s', self.temp_dir, '-o', out_xdc, '--xdc'],
            capture_output=True, text=True, cwd=str(project_root))
        self.assertEqual(result.returncode, 0, result.stderr)
        generated = os.listdir(out_xdc)
        self.assertIn("xdc_cdc_test_axion_reg.xdc", generated)
        self.assertNotIn("xdc_cdc_test_axion_reg.vhd", generated)

        # --all must not emit XDC files (explicit opt-in)
        out_all = os.path.join(self.temp_dir, "out_all")
        result = subprocess.run(
            [sys.executable, '-m', 'axion_hdl.cli',
             '-s', self.temp_dir, '-o', out_all, '--all'],
            capture_output=True, text=True, cwd=str(project_root))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("xdc_cdc_test_axion_reg.xdc", os.listdir(out_all))

    # =========================================================================
    # XDC-011: Input Format Independence
    # =========================================================================
    def test_xdc_011_input_format_independence(self):
        """XDC-011: XDC generation works for YAML-defined modules"""
        content = self._generate_xdc(YAML_INPUT, "xdc_yaml_test",
                                     extension="yaml")
        active = self._active_lines(content)
        self.assertIn("REF_NAME == xdc_yaml_test_axion_reg", content)
        self.assertTrue(any(l.startswith("set_false_path -to")
                            and "*/yaml_status" in l for l in active))
        self.assertTrue(any(l.startswith("set_false_path -from")
                            and "*/yaml_config" in l for l in active))

    # =========================================================================
    # XDC-012: API Safety
    # =========================================================================
    def test_xdc_012_api_safety(self):
        """XDC-012: generate_xdc() False before analyze(), True after"""
        axion = AxionHDL(output_dir=self.output_dir)
        self.assertFalse(axion.generate_xdc())

        src = self._write_source("xdc_cdc_test.vhd", CDC_VHDL)
        axion.add_source(src)
        axion.analyze()
        self.assertTrue(axion.generate_xdc())


if __name__ == '__main__':
    unittest.main(verbosity=2)
