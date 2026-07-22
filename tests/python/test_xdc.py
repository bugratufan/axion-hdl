#!/usr/bin/env python3
"""
test_xdc.py - XDC Constraint Generation Requirements Tests

Tests for XDC-001 through XDC-013 requirements
Verifies instance-independent Xilinx XDC false-path constraint generation,
scoped tightly to Axion-HDL's own CDC synchronizer crossing points.
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

CDC_SV = '''
// @axion_def BASE_ADDR=0x0000 CDC_EN CDC_STAGE=2
module xdc_cdc_sv_test (
    input logic clk
);
    logic [31:0] status_reg; // @axion RO ADDR=0x00 R_STROBE
    logic [31:0] config_reg; // @axion RW ADDR=0x04 W_STROBE
    logic [15:0] tx_reg;     // @axion WO ADDR=0x08
    logic        enable_bit; // @axion RW ADDR=0x0C
endmodule
'''

PACKED_VHDL = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN CDC_STAGE=2
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
  cdc_en: true
  cdc_stage: 2

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


def _stage_vhdl(stages):
    """CDC_VHDL fixture parametrized by CDC_STAGE, for stage-independence tests"""
    return f'''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN CDC_STAGE={stages}
entity xdc_stage_test is
    port (clk : in std_logic);
end entity;
architecture rtl of xdc_stage_test is
    signal status_reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00 R_STROBE
    signal config_reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x04 W_STROBE
begin
end architecture;
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
                      extension: str = "vhd", expect_file: bool = True,
                      backend: str = "vhdl"):
        """
        Generate XDC from source content.

        Returns the generated text if expect_file is True (and asserts the
        file exists). Returns the path to where the file WOULD be (without
        asserting existence) if expect_file is False, for tests that verify
        a module is correctly skipped.

        backend selects which HDL backend the constraints are generated
        for ('vhdl' or 'systemverilog') - see XDCGenerator. The VHDL
        backend keeps the plain `<module>_axion_reg.xdc` filename; the
        SystemVerilog backend uses `<module>_axion_reg_sv.xdc`.
        """
        src = self._write_source(f"{module_name}.{extension}", content)

        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_source(src)
        axion.analyze()
        self.assertTrue(axion.generate_xdc(backend=backend))

        suffix = '_sv' if backend == 'systemverilog' else ''
        gen_file = os.path.join(self.output_dir,
                                 f"{module_name}_axion_reg{suffix}.xdc")
        if not expect_file:
            self.assertFalse(os.path.exists(gen_file),
                             f"XDC file should not have been generated: {gen_file}")
            return None

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
        """XDC-001: --xdc generates <module>_axion_reg.xdc for CDC-enabled modules"""
        self._write_source("xdc_cdc_test.vhd", CDC_VHDL)
        self._write_source("xdc_nocdc_test.vhd", NOCDC_VHDL)

        result = subprocess.run(
            [sys.executable, '-m', 'axion_hdl.cli',
             '-s', self.temp_dir, '-o', self.output_dir, '--xdc'],
            capture_output=True, text=True, cwd=str(project_root))
        self.assertEqual(result.returncode, 0, result.stderr)

        self.assertTrue(
            os.path.exists(os.path.join(
                self.output_dir, "xdc_cdc_test_axion_reg.xdc")),
            "Missing XDC for CDC-enabled module")
        self.assertFalse(
            os.path.exists(os.path.join(
                self.output_dir, "xdc_nocdc_test_axion_reg.xdc")),
            "CDC-disabled module must not produce an XDC file")

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
    # XDC-003: RO Crossing Constraint (module port -> sync0)
    # =========================================================================
    def test_xdc_003_ro_crossing_constraint(self):
        """XDC-003: RO register false-paths its port to the first sync stage only"""
        content = self._generate_xdc(CDC_VHDL, "xdc_cdc_test")
        lines = [l for l in self._active_lines(content)
                 if l.startswith("set_false_path")]

        status_lines = [l for l in lines if "status_reg" in l and "toggle" not in l]
        self.assertEqual(len(status_lines), 1,
            "Exactly one crossing constraint expected for status_reg")
        line = status_lines[0]
        self.assertIn("-from [get_pins", line,
            "RO source must be the module-side port (get_pins)")
        self.assertIn("*/status_reg ", line)
        self.assertIn("*/status_reg[*]", line, "Vector bit pins must be covered")
        self.assertIn("-to [get_cells", line,
            "RO destination must be an internal cell (get_cells)")
        self.assertIn("*/status_reg_sync0", line,
            "Destination must be the FIRST synchronizer stage only")
        self.assertNotIn("status_reg_sync1", line,
            "Only stage 0 (the actual crossing) should be constrained")

    # =========================================================================
    # XDC-004: RW/WO Crossing Constraint (storage reg -> sync0)
    # =========================================================================
    def test_xdc_004_rw_wo_crossing_constraint(self):
        """XDC-004: RW/WO register false-paths its storage cell to the first sync stage only"""
        content = self._generate_xdc(CDC_VHDL, "xdc_cdc_test")
        lines = [l for l in self._active_lines(content)
                 if l.startswith("set_false_path")]

        for name in ("config_reg", "tx_reg", "enable_bit"):
            matches = [l for l in lines if f"{name}_reg" in l and "toggle" not in l]
            self.assertEqual(len(matches), 1,
                f"Exactly one crossing constraint expected for {name}")
            line = matches[0]
            self.assertIn("-from [get_cells", line,
                f"{name} source must be the internal storage cell (get_cells)")
            self.assertIn(f"*/{name}_reg", line)
            self.assertIn("-to [get_cells", line)
            self.assertIn(f"*/{name}_sync0", line,
                "Destination must be the FIRST synchronizer stage only")

    # =========================================================================
    # XDC-005: Packed Field Crossing Constraints
    # =========================================================================
    def test_xdc_005_packed_field_constraints(self):
        """XDC-005: packed RO fields and RW/WO storage each get one crossing constraint"""
        content = self._generate_xdc(PACKED_VHDL, "xdc_packed_test")
        lines = [l for l in self._active_lines(content)
                 if l.startswith("set_false_path")]

        # RO field: control's status_stat_busy port -> sync0
        ro_matches = [l for l in lines if "status_stat_busy" in l]
        self.assertEqual(len(ro_matches), 1)
        self.assertIn("-from [get_pins", ro_matches[0])
        self.assertIn("*/status_stat_busy_sync0", ro_matches[0])

        # RW/WO storage: one constraint for the whole packed register, not per field
        rw_matches = [l for l in lines if "control_reg" in l and "toggle" not in l]
        self.assertEqual(len(rw_matches), 1,
            "Packed RW/WO fields share one storage word - one constraint, not per-field")
        self.assertIn("-from [get_cells", rw_matches[0])
        self.assertIn("*/control_reg", rw_matches[0])
        self.assertIn("*/control_reg_sync0", rw_matches[0])

    # =========================================================================
    # XDC-006: Strobe Toggle Crossing Constraint
    # =========================================================================
    def test_xdc_006_strobe_toggle_crossing(self):
        """XDC-006: strobe toggle registers are false-pathed to their first sync stage; the regenerated pulse port is not"""
        content = self._generate_xdc(CDC_VHDL, "xdc_cdc_test")
        lines = [l for l in self._active_lines(content)
                 if l.startswith("set_false_path")]

        rd_toggle = [l for l in lines if "status_reg_rd_toggle" in l]
        self.assertEqual(len(rd_toggle), 1)
        self.assertIn("-from [get_cells", rd_toggle[0])
        self.assertIn("*/status_reg_rd_toggle}", rd_toggle[0])
        self.assertIn("*/status_reg_rd_toggle_sync0", rd_toggle[0])

        wr_toggle = [l for l in lines if "config_reg_wr_toggle" in l]
        self.assertEqual(len(wr_toggle), 1)
        self.assertIn("*/config_reg_wr_toggle}", wr_toggle[0])
        self.assertIn("*/config_reg_wr_toggle_sync0", wr_toggle[0])

        # The final regenerated pulse port itself must NEVER be constrained -
        # it is a fully-resolved, single-domain module_clk signal.
        for line in lines:
            self.assertNotIn("*/status_reg_rd_strobe}", line,
                "The regenerated strobe port itself must not be false-pathed")
            self.assertNotIn("*/status_reg_rd_strobe ", line)
            self.assertNotIn("*/config_reg_wr_strobe}", line)
            self.assertNotIn("*/config_reg_wr_strobe ", line)

    # =========================================================================
    # XDC-007: Vector Pin Coverage
    # =========================================================================
    def test_xdc_007_vector_pin_coverage(self):
        """XDC-007: port-side pin filters match scalar name and vector bit pins"""
        content = self._generate_xdc(CDC_VHDL, "xdc_cdc_test")
        active = self._active_lines(content)

        status_lines = [l for l in active if "status_reg " in l or "status_reg[" in l]
        self.assertEqual(len(status_lines), 1)
        self.assertIn("NAME =~ */status_reg ", status_lines[0])
        self.assertIn("NAME =~ */status_reg[*]", status_lines[0])

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
    # XDC-009: CDC-Disabled Modules Produce No File
    # =========================================================================
    def test_xdc_009_cdc_disabled_no_file(self):
        """XDC-009: CDC-disabled modules have no internal crossing to scope, so no file is generated"""
        self._generate_xdc(NOCDC_VHDL, "xdc_nocdc_test", expect_file=False)

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
        self.assertTrue(any(l.startswith("set_false_path")
                            and "get_pins" in l and "*/yaml_status" in l
                            for l in active))
        self.assertTrue(any(l.startswith("set_false_path")
                            and "get_cells" in l and "*/yaml_config_reg" in l
                            for l in active))

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

    # =========================================================================
    # XDC-013: Stage-Count Independence
    # =========================================================================
    def test_xdc_013_stage_count_independence(self):
        """XDC-013: constraints always target sync0 only, regardless of CDC_STAGE"""
        content_2 = self._generate_xdc(_stage_vhdl(2), "xdc_stage_test")

        # Fresh AxionHDL/output dir for the 5-stage variant
        self.output_dir = os.path.join(self.temp_dir, "output5")
        content_5 = self._generate_xdc(_stage_vhdl(5), "xdc_stage_test")

        for content, stages in ((content_2, 2), (content_5, 5)):
            self.assertIn("*/status_reg_sync0", content)
            self.assertIn("*/config_reg_sync0", content)
            self.assertIn("*/status_reg_rd_toggle_sync0", content)
            self.assertIn("*/config_reg_wr_toggle_sync0", content)
            # No reference to any stage beyond 0 must ever appear
            for stage in range(1, stages):
                self.assertNotIn(f"_sync{stage} ", content + " ",
                    f"XDC must not reference stage {stage} (CDC_STAGE={stages})")

        # The two variants must be byte-for-byte identical except for the
        # version banner line, proving the constraints are fully
        # stage-count-agnostic.
        def _strip_version(text):
            return '\n'.join(l for l in text.splitlines()
                             if not l.startswith("# Generated by Axion-HDL"))

        self.assertEqual(_strip_version(content_2), _strip_version(content_5),
            "XDC output must be identical regardless of CDC_STAGE")

    # =========================================================================
    # XDC-014: SystemVerilog backend - RO crossing constraint targets the
    # real array-index cell name, not the VHDL discrete-signal name
    # =========================================================================
    def test_xdc_014_sv_ro_crossing_constraint(self):
        """XDC-014: for the SystemVerilog backend, RO false-path targets
        <name>_sync[0] (array element), matching SystemVerilogGenerator's
        actual `(* ASYNC_REG *) logic <name>_sync [N];` declaration - NOT
        <name>_sync0, which is the VHDL-only discrete-signal naming and
        never exists in generated SV RTL (the bug Copilot flagged on
        PR #130)."""
        content = self._generate_xdc(CDC_SV, "xdc_cdc_sv_test",
                                     extension="sv", backend="systemverilog")
        lines = [l for l in self._active_lines(content)
                 if l.startswith("set_false_path")]

        status_lines = [l for l in lines if "status_reg" in l and "toggle" not in l]
        self.assertEqual(len(status_lines), 1,
            "Exactly one crossing constraint expected for status_reg")
        line = status_lines[0]
        self.assertIn("-from [get_pins", line)
        self.assertIn("*/status_reg ", line)
        self.assertIn("*/status_reg[*]", line)
        self.assertIn("-to [get_cells", line)
        self.assertIn("*/status_reg_sync[0]", line,
            "SV destination must be the array-index cell name sync[0]")
        self.assertNotIn("status_reg_sync0", line,
            "SV output must never use the VHDL-only discrete _sync0 naming")
        self.assertNotIn("status_reg_sync[1]", line,
            "Only stage 0 (the actual crossing) should be constrained")

    def test_xdc_015_sv_rw_wo_crossing_constraint(self):
        """XDC-015: SV RW/WO false-path targets the storage cell -> sync[0]"""
        content = self._generate_xdc(CDC_SV, "xdc_cdc_sv_test",
                                     extension="sv", backend="systemverilog")
        lines = [l for l in self._active_lines(content)
                 if l.startswith("set_false_path")]

        for name in ("config_reg", "tx_reg", "enable_bit"):
            matches = [l for l in lines if f"{name}_reg" in l and "toggle" not in l]
            self.assertEqual(len(matches), 1,
                f"Exactly one crossing constraint expected for {name}")
            line = matches[0]
            self.assertIn("-from [get_cells", line)
            self.assertIn(f"*/{name}_reg", line)
            self.assertIn("-to [get_cells", line)
            self.assertIn(f"*/{name}_sync[0]", line,
                "SV destination must be the array-index cell name sync[0]")
            self.assertNotIn(f"{name}_sync0", line)

    def test_xdc_016_sv_strobe_toggle_crossing(self):
        """XDC-016: SV strobe toggle crossing targets <base>_sync[0], not <base>_sync0"""
        content = self._generate_xdc(CDC_SV, "xdc_cdc_sv_test",
                                     extension="sv", backend="systemverilog")
        lines = [l for l in self._active_lines(content)
                 if l.startswith("set_false_path")]

        rd_toggle = [l for l in lines if "status_reg_rd_toggle" in l]
        self.assertEqual(len(rd_toggle), 1)
        self.assertIn("-from [get_cells", rd_toggle[0])
        self.assertIn("*/status_reg_rd_toggle}", rd_toggle[0])
        self.assertIn("*/status_reg_rd_toggle_sync[0]", rd_toggle[0])
        self.assertNotIn("status_reg_rd_toggle_sync0", rd_toggle[0])

        wr_toggle = [l for l in lines if "config_reg_wr_toggle" in l]
        self.assertEqual(len(wr_toggle), 1)
        self.assertIn("*/config_reg_wr_toggle}", wr_toggle[0])
        self.assertIn("*/config_reg_wr_toggle_sync[0]", wr_toggle[0])
        self.assertNotIn("config_reg_wr_toggle_sync0", wr_toggle[0])

        for line in lines:
            self.assertNotIn("*/status_reg_rd_strobe}", line)
            self.assertNotIn("*/config_reg_wr_strobe}", line)

    # NOTE: there is no SV counterpart to test_xdc_005_packed_field_constraints
    # here. Unlike the VHDL parser, axion_hdl/systemverilog_parser.py does not
    # currently assemble REG_NAME/BIT_OFFSET-annotated signals into a
    # `packed_registers` list with `reg_name`/`fields` (its module-level
    # `_parse_module_config` only reacts to an unused `PACK=` @axion_def
    # attribute, and per-signal `bits`/`reg` grouping is never folded into
    # module_data['packed_registers']). SystemVerilogGenerator and
    # XDCGenerator both already handle `packed_registers` correctly *if*
    # populated - this is a pre-existing SV-parser gap unrelated to the XDC
    # backend-naming bug this test file targets, and is out of scope here.
    # Flagged for separate follow-up.

    def test_xdc_018_sv_stage_count_independence(self):
        """XDC-018: SV constraints always target sync[0] only, regardless of CDC_STAGE"""
        def _stage_sv(stages):
            return f'''
// @axion_def BASE_ADDR=0x0000 CDC_EN CDC_STAGE={stages}
module xdc_stage_sv_test (
    input logic clk
);
    logic [31:0] status_reg; // @axion RO ADDR=0x00 R_STROBE
    logic [31:0] config_reg; // @axion RW ADDR=0x04 W_STROBE
endmodule
'''
        content_2 = self._generate_xdc(_stage_sv(2), "xdc_stage_sv_test",
                                       extension="sv", backend="systemverilog")

        self.output_dir = os.path.join(self.temp_dir, "output5_sv")
        content_5 = self._generate_xdc(_stage_sv(5), "xdc_stage_sv_test",
                                       extension="sv", backend="systemverilog")

        for content, stages in ((content_2, 2), (content_5, 5)):
            self.assertIn("*/status_reg_sync[0]", content)
            self.assertIn("*/config_reg_sync[0]", content)
            self.assertIn("*/status_reg_rd_toggle_sync[0]", content)
            self.assertIn("*/config_reg_wr_toggle_sync[0]", content)
            for stage in range(1, stages):
                self.assertNotIn(f"_sync[{stage}]", content,
                    f"XDC must not reference stage {stage} (CDC_STAGE={stages})")

        def _strip_version(text):
            return '\n'.join(l for l in text.splitlines()
                             if not l.startswith("# Generated by Axion-HDL"))

        self.assertEqual(_strip_version(content_2), _strip_version(content_5),
            "XDC output must be identical regardless of CDC_STAGE")

    def test_xdc_019_cli_systemverilog_xdc_flag(self):
        """XDC-019: `--systemverilog --xdc` on the CLI produces a real SV XDC
        file (<module>_axion_reg_sv.xdc) whose -to filter uses SV array-index
        naming, and does not silently reuse the VHDL naming/filename."""
        self._write_source("xdc_cdc_sv_test.sv", CDC_SV)

        result = subprocess.run(
            [sys.executable, '-m', 'axion_hdl.cli',
             '-s', self.temp_dir, '-o', self.output_dir,
             '--systemverilog', '--xdc'],
            capture_output=True, text=True, cwd=str(project_root))
        self.assertEqual(result.returncode, 0, result.stderr)

        gen_file = os.path.join(self.output_dir, "xdc_cdc_sv_test_axion_reg_sv.xdc")
        self.assertTrue(os.path.exists(gen_file),
            "CLI --systemverilog --xdc must produce a *_sv.xdc file")
        with open(gen_file) as f:
            content = f.read()
        self.assertIn("*/status_reg_sync[0]", content)
        self.assertNotIn("status_reg_sync0", content)

    def test_xdc_020_cli_both_backends_no_collision(self):
        """XDC-020: `--vhdl --systemverilog --xdc` together must produce two
        distinct, correctly-named XDC files (one per backend) rather than
        one backend's file silently overwriting the other's."""
        self._write_source("xdc_cdc_test.vhd", CDC_VHDL)
        self._write_source("xdc_cdc_sv_test.sv", CDC_SV)

        result = subprocess.run(
            [sys.executable, '-m', 'axion_hdl.cli',
             '-s', self.temp_dir, '-o', self.output_dir,
             '--vhdl', '--systemverilog', '--xdc'],
            capture_output=True, text=True, cwd=str(project_root))
        self.assertEqual(result.returncode, 0, result.stderr)

        vhdl_xdc = os.path.join(self.output_dir, "xdc_cdc_test_axion_reg.xdc")
        sv_xdc = os.path.join(self.output_dir, "xdc_cdc_sv_test_axion_reg_sv.xdc")
        self.assertTrue(os.path.exists(vhdl_xdc), "VHDL XDC file missing")
        self.assertTrue(os.path.exists(sv_xdc), "SystemVerilog XDC file missing")

        with open(vhdl_xdc) as f:
            vhdl_content = f.read()
        with open(sv_xdc) as f:
            sv_content = f.read()
        self.assertIn("_sync0", vhdl_content)
        self.assertNotIn("_sync[0]", vhdl_content)
        self.assertIn("_sync[0]", sv_content)
        self.assertNotIn("_sync0", sv_content)


if __name__ == '__main__':
    unittest.main(verbosity=2)
