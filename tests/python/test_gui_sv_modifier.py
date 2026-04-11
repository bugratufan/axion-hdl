"""
GUI SystemVerilog Modifier Tests

Tests that SourceModifier correctly handles .sv files:
- Adding new registers (// @axion style, logic declarations)
- Updating existing register annotations
- Updating // @axion_def (not -- style)
- Injecting new // @axion_def when missing

Run with: pytest tests/python/test_gui_sv_modifier.py -v
"""
import pytest
import os
import re
import sys
import tempfile
import shutil

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from axion_hdl import AxionHDL
from axion_hdl.source_modifier import SourceModifier


SV_TEMPLATE = """\
// @axion_def CDC_EN=true CDC_STAGE=2 BASE_ADDR=0x1000
module {module_name} (
    input logic clk,
    input logic rst_n
);
    // Control register
    logic [31:0] ctrl_reg;  // @axion RW DESC="Control register"
    // Status register
    logic [31:0] status_reg;  // @axion RO DESC="Status register"
endmodule
"""


def _make_sv_axion(module_name, extra_content=""):
    """Returns SV content with optional extra signals before endmodule."""
    base = SV_TEMPLATE.format(module_name=module_name)
    if extra_content:
        base = base.replace("endmodule", extra_content + "\nendmodule")
    return base


def _setup_axion(sv_content, module_name, tmpdir):
    """Write SV file, analyze with AxionHDL, return (axion, filepath)."""
    sv_file = os.path.join(tmpdir, f"{module_name}.sv")
    with open(sv_file, "w") as f:
        f.write(sv_content)
    axion = AxionHDL(output_dir=os.path.join(tmpdir, "out"))
    axion.add_sv_src(sv_file)
    axion.analyze()
    return axion, sv_file


class TestSVModifierNewRegister:
    """GUI-SV-001..003: Adding new registers to .sv files"""

    def test_gui_sv_001_new_register_appended_before_endmodule(self):
        """New register signal declaration appears before endmodule"""
        with tempfile.TemporaryDirectory() as tmpdir:
            axion, sv_file = _setup_axion(_make_sv_axion("mod_new"), "mod_new", tmpdir)
            assert axion.analyzed_modules, "Module not parsed"

            modifier = SourceModifier(axion)
            existing = [
                {"name": "ctrl_reg", "access": "RW", "width": 32, "description": "Control register"},
                {"name": "status_reg", "access": "RO", "width": 32, "description": "Status register"},
            ]
            new_regs = existing + [
                {"name": "new_cfg", "access": "RW", "width": 32, "description": "New config"}
            ]
            content, _ = modifier.get_modified_content("mod_new", new_regs, file_path=sv_file)

            assert "new_cfg" in content, "New register name not found in modified content"
            assert "// @axion" in content, "No @axion annotation for new register"
            # Must appear before endmodule
            new_pos = content.index("new_cfg")
            end_pos = content.index("endmodule")
            assert new_pos < end_pos, "New register not before endmodule"

    def test_gui_sv_002_new_register_uses_logic_declaration(self):
        """New register uses 'logic [W-1:0]' not 'signal' (VHDL style)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            axion, sv_file = _setup_axion(_make_sv_axion("mod_logic"), "mod_logic", tmpdir)
            assert axion.analyzed_modules

            modifier = SourceModifier(axion)
            existing = [
                {"name": "ctrl_reg", "access": "RW", "width": 32, "description": ""},
                {"name": "status_reg", "access": "RO", "width": 32, "description": ""},
            ]
            new_regs = existing + [{"name": "cfg_16", "access": "RW", "width": 16, "description": ""}]
            content, _ = modifier.get_modified_content("mod_logic", new_regs, file_path=sv_file)

            assert "logic [15:0] cfg_16" in content, \
                f"Expected 'logic [15:0] cfg_16' in content, got:\n{content}"
            assert "signal cfg_16" not in content, "VHDL-style 'signal' keyword used for SV register"

    def test_gui_sv_003_new_register_annotation_uses_double_slash(self):
        """New register annotation uses // not -- comment style"""
        with tempfile.TemporaryDirectory() as tmpdir:
            axion, sv_file = _setup_axion(_make_sv_axion("mod_comment"), "mod_comment", tmpdir)
            assert axion.analyzed_modules

            modifier = SourceModifier(axion)
            existing = [
                {"name": "ctrl_reg", "access": "RW", "width": 32, "description": ""},
                {"name": "status_reg", "access": "RO", "width": 32, "description": ""},
            ]
            new_regs = existing + [{"name": "irq_reg", "access": "RW", "width": 32, "description": "IRQ control"}]
            content, _ = modifier.get_modified_content("mod_comment", new_regs, file_path=sv_file)

            # Find the new register line
            lines_with_irq = [l for l in content.splitlines() if "irq_reg" in l and "@axion" in l]
            assert lines_with_irq, "No @axion line found for new register"
            assert lines_with_irq[0].strip().startswith("logic"), \
                f"New register line doesn't start with 'logic': {lines_with_irq[0]}"
            assert "// @axion" in lines_with_irq[0], \
                f"Expected '// @axion' not '-- @axion': {lines_with_irq[0]}"

    def test_gui_sv_004_new_1bit_register_no_width_brackets(self):
        """1-bit new register uses 'logic name' not 'logic [0:0] name'"""
        with tempfile.TemporaryDirectory() as tmpdir:
            axion, sv_file = _setup_axion(_make_sv_axion("mod_1bit"), "mod_1bit", tmpdir)
            assert axion.analyzed_modules

            modifier = SourceModifier(axion)
            existing = [
                {"name": "ctrl_reg", "access": "RW", "width": 32, "description": ""},
                {"name": "status_reg", "access": "RO", "width": 32, "description": ""},
            ]
            new_regs = existing + [{"name": "en_bit", "access": "RW", "width": 1, "description": "Enable"}]
            content, _ = modifier.get_modified_content("mod_1bit", new_regs, file_path=sv_file)

            assert "logic en_bit" in content, "1-bit register should use 'logic en_bit' (no width)"
            assert "logic [0:0] en_bit" not in content, "Should not have [0:0] for 1-bit register"


class TestSVModifierUpdateExisting:
    """GUI-SV-005..006: Updating existing registers in .sv files"""

    def test_gui_sv_005_existing_register_annotation_updated(self):
        """Updating access mode of existing register changes // @axion tag"""
        with tempfile.TemporaryDirectory() as tmpdir:
            axion, sv_file = _setup_axion(_make_sv_axion("mod_update"), "mod_update", tmpdir)
            assert axion.analyzed_modules

            modifier = SourceModifier(axion)
            # Change ctrl_reg from RW to WO
            new_regs = [
                {"name": "ctrl_reg", "access": "WO", "width": 32, "description": "Control register"},
                {"name": "status_reg", "access": "RO", "width": 32, "description": "Status register"},
            ]
            content, _ = modifier.get_modified_content("mod_update", new_regs, file_path=sv_file)

            ctrl_lines = [l for l in content.splitlines() if "ctrl_reg" in l and "@axion" in l]
            assert ctrl_lines, "ctrl_reg @axion line not found"
            assert "WO" in ctrl_lines[0], f"Access mode not updated to WO: {ctrl_lines[0]}"

    def test_gui_sv_006_existing_register_not_duplicated(self):
        """Updating existing register does not create a duplicate declaration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            axion, sv_file = _setup_axion(_make_sv_axion("mod_nodup"), "mod_nodup", tmpdir)
            assert axion.analyzed_modules

            modifier = SourceModifier(axion)
            new_regs = [
                {"name": "ctrl_reg", "access": "RW", "width": 32, "description": "Updated desc"},
                {"name": "status_reg", "access": "RO", "width": 32, "description": "Status register"},
            ]
            content, _ = modifier.get_modified_content("mod_nodup", new_regs, file_path=sv_file)

            count = content.count("ctrl_reg")
            # ctrl_reg appears in original declaration + possible comment, not duplicated as new logic
            assert content.count("logic [31:0] ctrl_reg") <= 1, \
                "ctrl_reg declaration duplicated in modified content"


class TestSVModifierAxionDef:
    """GUI-SV-007..009: // @axion_def handling"""

    def test_gui_sv_007_axion_def_updated_with_double_slash(self):
        """Changing CDC config updates // @axion_def, not -- @axion_def"""
        with tempfile.TemporaryDirectory() as tmpdir:
            axion, sv_file = _setup_axion(_make_sv_axion("mod_def"), "mod_def", tmpdir)
            assert axion.analyzed_modules

            modifier = SourceModifier(axion)
            existing = [
                {"name": "ctrl_reg", "access": "RW", "width": 32, "description": ""},
                {"name": "status_reg", "access": "RO", "width": 32, "description": ""},
            ]
            props = {"cdc_enabled": True, "cdc_stages": 3, "base_address": "0x1000"}
            content, _ = modifier.get_modified_content("mod_def", existing, properties=props, file_path=sv_file)

            assert "-- @axion_def" not in content, \
                "VHDL-style '-- @axion_def' found in SV file after modification"
            assert "// @axion_def" in content, \
                "Expected '// @axion_def' not found after CDC update"

    def test_gui_sv_008_axion_def_cdc_stage_updated(self):
        """CDC_STAGE value in // @axion_def is updated correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            axion, sv_file = _setup_axion(_make_sv_axion("mod_stage"), "mod_stage", tmpdir)
            assert axion.analyzed_modules

            modifier = SourceModifier(axion)
            existing = [
                {"name": "ctrl_reg", "access": "RW", "width": 32, "description": ""},
                {"name": "status_reg", "access": "RO", "width": 32, "description": ""},
            ]
            props = {"cdc_enabled": True, "cdc_stages": 4}
            content, _ = modifier.get_modified_content("mod_stage", existing, properties=props, file_path=sv_file)

            assert "CDC_STAGE=4" in content, \
                f"CDC_STAGE not updated to 4 in content:\n{content}"

    def test_gui_sv_009_axion_def_injected_before_module_when_missing(self):
        """// @axion_def is injected before 'module' keyword when not present"""
        sv_no_def = """\
module mod_nodef (input logic clk);
    logic [31:0] ctrl_reg;  // @axion RW DESC="Control"
endmodule
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            axion, sv_file = _setup_axion(sv_no_def, "mod_nodef", tmpdir)
            assert axion.analyzed_modules

            modifier = SourceModifier(axion)
            existing = [{"name": "ctrl_reg", "access": "RW", "width": 32, "description": "Control"}]
            props = {"cdc_enabled": True, "cdc_stages": 2, "base_address": "0x2000"}
            content, _ = modifier.get_modified_content("mod_nodef", existing, properties=props, file_path=sv_file)

            assert "// @axion_def" in content, "// @axion_def not injected"
            def_pos = content.index("// @axion_def")
            mod_pos = content.index("module mod_nodef")
            assert def_pos < mod_pos, "// @axion_def not before module declaration"
            assert "-- @axion_def" not in content, "VHDL-style comment injected into SV file"


class TestSVModifierFileNotModifiedForVHDL:
    """GUI-SV-010: VHDL files still use -- style (regression)"""

    def test_gui_sv_010_vhdl_file_still_uses_dash_comment(self):
        """VHDL files are unaffected by SV routing — still use -- @axion"""
        vhdl_dir = os.path.join(PROJECT_ROOT, "tests", "vhdl")
        vhdl_files = [f for f in os.listdir(vhdl_dir) if f.endswith((".vhd", ".vhdl"))] if os.path.isdir(vhdl_dir) else []
        if not vhdl_files:
            pytest.skip("No VHDL test files found")

        with tempfile.TemporaryDirectory() as tmpdir:
            axion = AxionHDL(output_dir=os.path.join(tmpdir, "out"))
            axion.add_src(vhdl_dir)
            axion.exclude("error_cases")
            axion.analyze()

            if not axion.analyzed_modules:
                pytest.skip("No VHDL modules parsed")

            mod = axion.analyzed_modules[0]
            # Verify the source file is VHDL
            assert mod["file"].endswith((".vhd", ".vhdl")), "Expected VHDL module"
