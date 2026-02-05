#!/usr/bin/env python3
"""
test_width_propagation.py - Register Width Propagation Tests

Maps to requirements in docs/source/requirements-core.md.

Requirement ↔ test-class mapping
---------------------------------
YAML-INPUT-016  signal_type emitted by YAMLInputParser is parseable downstream
         → TestYAMLSignalTypeParseable

PARSER-009      signal_type emitted by VHDLParser is parseable downstream
         → TestVHDLSignalTypeParseable

GEN-019  CHeaderGenerator width extraction from YAML signal_type
         → TestCHeaderGetSignalWidth   (unit tests on _get_signal_width)
         → TestCHeaderWidthMacrosYAML  (generated WIDTH / NUM_REGS macros)

GEN-020  CHeaderGenerator width extraction from VHDL-annotation signal_type
         → TestCHeaderGetSignalWidth   (bracket-format unit tests)
         → TestCHeaderWidthMacrosVHDL  (generated WIDTH / NUM_REGS macros)

GEN-021  Struct layout: >32-bit → multi-member, ≤32-bit → single member
         → TestCHeaderStructLayoutYAML

GEN-022  Markdown Width column accuracy – YAML source
         → TestMarkdownWidthColumnYAML

GEN-023  Markdown Width column accuracy – VHDL-annotation source
         → TestMarkdownWidthColumnVHDL

SUB-007  Packed-register field width propagation to header – VHDL source
         → TestPackedFieldMasksVHDL

SUB-008  Packed-register field width propagation to header – YAML source
         → TestPackedFieldMasksYAML

GEN-026  Packed container is a single uint32_t in struct
         → TestPackedContainerWidth

GEN-027  VHDL entity port width – YAML source
         → TestVHDLPortWidthYAML

GEN-028  VHDL entity port width – VHDL-annotation source
         → TestVHDLPortWidthVHDL

ADDR-006 Regression / sanity guard – auto-address wide-register slot count
         → TestAutoAddressWideRegisters

End-to-end consistency (exercises GEN-019 + GEN-021 + GEN-022 together)
         → TestE2EConsistencyYAML
         → TestE2EConsistencyVHDL
"""

import os
import sys
import re
import unittest
import tempfile
import shutil
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from axion_hdl.yaml_input_parser import YAMLInputParser
from axion_hdl.parser import VHDLParser
from axion_hdl.doc_generators import DocGenerator, CHeaderGenerator
from axion_hdl.generator import VHDLGenerator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(directory: str, name: str, content: str) -> str:
    path = os.path.join(directory, name)
    with open(path, 'w') as f:
        f.write(content)
    return path


def _parse_yaml(content: str, tmp: str) -> dict:
    path = _write(tmp, "test.yaml", content)
    return YAMLInputParser().parse_file(path)


def _parse_vhdl(content: str, tmp: str) -> dict:
    path = _write(tmp, "test.vhd", content)
    return VHDLParser()._parse_vhdl_file(path)


def _generate_header(module: dict, tmp: str) -> str:
    gen = CHeaderGenerator(tmp)
    path = gen.generate_header(module)
    with open(path) as f:
        return f.read()


def _generate_vhdl(module: dict, tmp: str) -> str:
    gen = VHDLGenerator(tmp)
    path = gen.generate_module(module)
    with open(path) as f:
        return f.read()


def _generate_markdown(module: dict, tmp: str) -> str:
    gen = DocGenerator(tmp)
    path = gen.generate_markdown([module])
    with open(path) as f:
        return f.read()


def _extract_md_table_rows(md: str) -> list:
    """
    Parse the register-map markdown table.
    Table columns: Address | Offset | Register Name | Type | Width | Access | …
    Returns list of dicts: {name, width (int)}.
    """
    rows = []
    for line in md.splitlines():
        line = line.strip()
        if not line.startswith('|'):
            continue
        if 'Register Name' in line or re.match(r'^\|[\s\-:|]+\|$', line):
            continue
        cells = [c.strip() for c in line.split('|')[1:-1]]
        if len(cells) < 5:
            continue
        name = cells[2].strip('` ')
        try:
            width = int(cells[4])
        except ValueError:
            width = -1
        rows.append({'name': name, 'width': width})
    return rows


# ---------------------------------------------------------------------------
# Shared fixtures – register sets used across multiple test classes
# ---------------------------------------------------------------------------

# 1 / 5 / 32 / 33 / 64 bit registers – YAML
YAML_MULTI = """\
module: width_test
registers:
  - name: reg_1bit
    access: RW
    width: 1
  - name: reg_5bit
    access: RW
    width: 5
  - name: reg_32bit
    access: RW
    width: 32
  - name: reg_33bit
    access: RW
    width: 33
  - name: reg_64bit
    access: RW
    width: 64
"""

# Same register set – VHDL @axion annotations
VHDL_MULTI = """\
library ieee;
use ieee.std_logic_1164.all;

entity width_test is
end entity;

architecture rtl of width_test is
    signal reg_1bit  : std_logic;                            -- @axion RW ADDR=0x00
    signal reg_5bit  : std_logic_vector(4 downto 0);        -- @axion RW ADDR=0x04
    signal reg_32bit : std_logic_vector(31 downto 0);       -- @axion RW ADDR=0x08
    signal reg_33bit : std_logic_vector(32 downto 0);       -- @axion RW ADDR=0x0C
    signal reg_64bit : std_logic_vector(63 downto 0);       -- @axion RW ADDR=0x14
begin
end architecture;
"""

# Packed register – three fields in one 32-bit container – YAML
YAML_PACKED = """\
module: packed_test
registers:
  - name: enable
    reg_name: ctrl
    bit_offset: 0
    width: 1
    access: RW
    description: "Enable bit"
  - name: mode
    reg_name: ctrl
    bit_offset: 1
    width: 3
    access: RW
    description: "Mode selector"
  - name: divider
    reg_name: ctrl
    bit_offset: 4
    width: 8
    access: RW
    description: "Clock divider"
"""

# Same packed register set – VHDL @axion annotations
VHDL_PACKED = """\
library ieee;
use ieee.std_logic_1164.all;

entity packed_test is
end entity;

architecture rtl of packed_test is
    signal enable  : std_logic;                         -- @axion RW ADDR=0x00 REG_NAME=ctrl BIT_OFFSET=0
    signal mode    : std_logic_vector(2 downto 0);     -- @axion RW ADDR=0x00 REG_NAME=ctrl BIT_OFFSET=1
    signal divider : std_logic_vector(7 downto 0);     -- @axion RW ADDR=0x00 REG_NAME=ctrl BIT_OFFSET=4
begin
end architecture;
"""


# ---------------------------------------------------------------------------
# GEN-019 / GEN-020  –  CHeaderGenerator._get_signal_width unit tests
#
# GEN-019: must handle std_logic / std_logic_vector(N downto 0)  (YAML path)
# GEN-020: must handle [N:0]                                      (VHDL path)
# ---------------------------------------------------------------------------

class TestCHeaderGetSignalWidth(unittest.TestCase):
    """GEN-019, GEN-020: _get_signal_width handles both signal_type formats."""

    def setUp(self):
        self.gen = CHeaderGenerator.__new__(CHeaderGenerator)

    # ---- GEN-020: [N:0] bracket format (VHDL-annotation path) ----
    def test_gen_020_bracket_1bit(self):
        """GEN-020: [0:0] → width 1"""
        self.assertEqual(self.gen._get_signal_width("[0:0]"), 1)

    def test_gen_020_bracket_5bit(self):
        """GEN-020: [4:0] → width 5"""
        self.assertEqual(self.gen._get_signal_width("[4:0]"), 5)

    def test_gen_020_bracket_32bit(self):
        """GEN-020: [31:0] → width 32"""
        self.assertEqual(self.gen._get_signal_width("[31:0]"), 32)

    def test_gen_020_bracket_33bit(self):
        """GEN-020: [32:0] → width 33"""
        self.assertEqual(self.gen._get_signal_width("[32:0]"), 33)

    def test_gen_020_bracket_64bit(self):
        """GEN-020: [63:0] → width 64"""
        self.assertEqual(self.gen._get_signal_width("[63:0]"), 64)

    # ---- GEN-019: std_logic / std_logic_vector(…) format (YAML path) ----
    def test_gen_019_stdlogic_1bit(self):
        """GEN-019: std_logic → width 1"""
        self.assertEqual(self.gen._get_signal_width("std_logic"), 1)

    def test_gen_019_stdlogic_vector_5bit(self):
        """GEN-019: std_logic_vector(4 downto 0) → width 5"""
        self.assertEqual(self.gen._get_signal_width("std_logic_vector(4 downto 0)"), 5)

    def test_gen_019_stdlogic_vector_32bit(self):
        """GEN-019: std_logic_vector(31 downto 0) → width 32"""
        self.assertEqual(self.gen._get_signal_width("std_logic_vector(31 downto 0)"), 32)

    def test_gen_019_stdlogic_vector_33bit(self):
        """GEN-019: std_logic_vector(32 downto 0) → width 33"""
        self.assertEqual(self.gen._get_signal_width("std_logic_vector(32 downto 0)"), 33)

    def test_gen_019_stdlogic_vector_64bit(self):
        """GEN-019: std_logic_vector(63 downto 0) → width 64"""
        self.assertEqual(self.gen._get_signal_width("std_logic_vector(63 downto 0)"), 64)


# ---------------------------------------------------------------------------
# YAML-INPUT-016  –  signal_type produced by YAML parser is parseable
# ---------------------------------------------------------------------------

class TestYAMLSignalTypeParseable(unittest.TestCase):
    """YAML-INPUT-016: signal_type emitted by YAMLInputParser must be
    parseable by CHeaderGenerator._get_signal_width with the correct result."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.module = _parse_yaml(YAML_MULTI, self.tmp)
        self.gen = CHeaderGenerator.__new__(CHeaderGenerator)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _downstream_width(self, name: str) -> int:
        for r in self.module['registers']:
            if r['signal_name'] == name:
                return self.gen._get_signal_width(r['signal_type'])
        self.fail(f"Register '{name}' not found")

    def test_yaml_input_016_signal_type_1bit(self):
        """YAML-INPUT-016: YAML 1-bit signal_type is parseable downstream"""
        self.assertEqual(self._downstream_width('reg_1bit'), 1)

    def test_yaml_input_016_signal_type_5bit(self):
        """YAML-INPUT-016: YAML 5-bit signal_type is parseable downstream"""
        self.assertEqual(self._downstream_width('reg_5bit'), 5)

    def test_yaml_input_016_signal_type_32bit(self):
        """YAML-INPUT-016: YAML 32-bit signal_type is parseable downstream"""
        self.assertEqual(self._downstream_width('reg_32bit'), 32)

    def test_yaml_input_016_signal_type_33bit(self):
        """YAML-INPUT-016: YAML 33-bit signal_type is parseable downstream"""
        self.assertEqual(self._downstream_width('reg_33bit'), 33)

    def test_yaml_input_016_signal_type_64bit(self):
        """YAML-INPUT-016: YAML 64-bit signal_type is parseable downstream"""
        self.assertEqual(self._downstream_width('reg_64bit'), 64)


# ---------------------------------------------------------------------------
# PARSER-009  –  signal_type produced by VHDL parser is parseable
# ---------------------------------------------------------------------------

class TestVHDLSignalTypeParseable(unittest.TestCase):
    """PARSER-009: signal_type emitted by VHDLParser must be parseable by
    CHeaderGenerator._get_signal_width with the correct result."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.module = _parse_vhdl(VHDL_MULTI, self.tmp)
        self.gen = CHeaderGenerator.__new__(CHeaderGenerator)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _downstream_width(self, name: str) -> int:
        for r in self.module['registers']:
            if r['signal_name'] == name:
                return self.gen._get_signal_width(r['signal_type'])
        self.fail(f"Register '{name}' not found")

    def test_parser_009_vhdl_signal_type_1bit(self):
        """PARSER-009: VHDL 1-bit signal_type is parseable downstream"""
        self.assertEqual(self._downstream_width('reg_1bit'), 1)

    def test_parser_009_vhdl_signal_type_5bit(self):
        """PARSER-009: VHDL 5-bit signal_type is parseable downstream"""
        self.assertEqual(self._downstream_width('reg_5bit'), 5)

    def test_parser_009_vhdl_signal_type_32bit(self):
        """PARSER-009: VHDL 32-bit signal_type is parseable downstream"""
        self.assertEqual(self._downstream_width('reg_32bit'), 32)

    def test_parser_009_vhdl_signal_type_33bit(self):
        """PARSER-009: VHDL 33-bit signal_type is parseable downstream"""
        self.assertEqual(self._downstream_width('reg_33bit'), 33)

    def test_parser_009_vhdl_signal_type_64bit(self):
        """PARSER-009: VHDL 64-bit signal_type is parseable downstream"""
        self.assertEqual(self._downstream_width('reg_64bit'), 64)


# ---------------------------------------------------------------------------
# GEN-019 (cont.)  –  generated header WIDTH / NUM_REGS macros – YAML source
# ---------------------------------------------------------------------------

class TestCHeaderWidthMacrosYAML(unittest.TestCase):
    """GEN-019: Header WIDTH and NUM_REGS macros correct for YAML-sourced
    registers.  >32-bit signals get WIDTH/NUM_REGS; ≤32-bit do not get
    spurious _REG0 offset suffixes."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        module = _parse_yaml(YAML_MULTI, self.tmp)
        self.header = _generate_header(module, self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_gen_019_yaml_33bit_width_macro(self):
        """GEN-019: 33-bit register produces WIDTH macro = 33"""
        self.assertRegex(self.header, r'REG_33BIT_WIDTH\s+33')

    def test_gen_019_yaml_64bit_width_macro(self):
        """GEN-019: 64-bit register produces WIDTH macro = 64"""
        self.assertRegex(self.header, r'REG_64BIT_WIDTH\s+64')

    def test_gen_019_yaml_33bit_num_regs_macro(self):
        """GEN-019: 33-bit register produces NUM_REGS macro = 2"""
        self.assertRegex(self.header, r'REG_33BIT_NUM_REGS\s+2')

    def test_gen_019_yaml_64bit_num_regs_macro(self):
        """GEN-019: 64-bit register produces NUM_REGS macro = 2"""
        self.assertRegex(self.header, r'REG_64BIT_NUM_REGS\s+2')

    def test_gen_019_yaml_5bit_no_reg0(self):
        """GEN-019: 5-bit register must not get _REG0 offset suffix"""
        self.assertNotIn("REG_5BIT_REG0", self.header)

    def test_gen_019_yaml_1bit_no_reg0(self):
        """GEN-019: 1-bit register must not get _REG0 offset suffix"""
        self.assertNotIn("REG_1BIT_REG0", self.header)


# ---------------------------------------------------------------------------
# GEN-020 (cont.)  –  generated header WIDTH / NUM_REGS macros – VHDL source
# ---------------------------------------------------------------------------

class TestCHeaderWidthMacrosVHDL(unittest.TestCase):
    """GEN-020: Header WIDTH and NUM_REGS macros correct for
    VHDL-annotation-sourced registers."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        module = _parse_vhdl(VHDL_MULTI, self.tmp)
        self.header = _generate_header(module, self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_gen_020_vhdl_33bit_width_macro(self):
        """GEN-020: 33-bit register produces WIDTH macro = 33"""
        self.assertRegex(self.header, r'REG_33BIT_WIDTH\s+33')

    def test_gen_020_vhdl_64bit_width_macro(self):
        """GEN-020: 64-bit register produces WIDTH macro = 64"""
        self.assertRegex(self.header, r'REG_64BIT_WIDTH\s+64')

    def test_gen_020_vhdl_33bit_num_regs_macro(self):
        """GEN-020: 33-bit register produces NUM_REGS macro = 2"""
        self.assertRegex(self.header, r'REG_33BIT_NUM_REGS\s+2')

    def test_gen_020_vhdl_64bit_num_regs_macro(self):
        """GEN-020: 64-bit register produces NUM_REGS macro = 2"""
        self.assertRegex(self.header, r'REG_64BIT_NUM_REGS\s+2')

    def test_gen_020_vhdl_5bit_no_reg0(self):
        """GEN-020: 5-bit register must not get _REG0 offset suffix"""
        self.assertNotIn("REG_5BIT_REG0", self.header)

    def test_gen_020_vhdl_1bit_no_reg0(self):
        """GEN-020: 1-bit register must not get _REG0 offset suffix"""
        self.assertNotIn("REG_1BIT_REG0", self.header)


# ---------------------------------------------------------------------------
# GEN-021  –  Struct layout: multi-member for >32-bit, single for ≤32-bit
# ---------------------------------------------------------------------------

class TestCHeaderStructLayoutYAML(unittest.TestCase):
    """GEN-021: Struct splits >32-bit into _reg0/_reg1 members;
    ≤32-bit stays as a single member (YAML source)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        module = _parse_yaml(YAML_MULTI, self.tmp)
        self.header = _generate_header(module, self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_gen_021_33bit_has_reg0_and_reg1(self):
        """GEN-021: 33-bit register has _reg0 and _reg1 struct members"""
        self.assertIn("reg_33bit_reg0", self.header)
        self.assertIn("reg_33bit_reg1", self.header)

    def test_gen_021_64bit_has_reg0_and_reg1(self):
        """GEN-021: 64-bit register has _reg0 and _reg1 struct members"""
        self.assertIn("reg_64bit_reg0", self.header)
        self.assertIn("reg_64bit_reg1", self.header)

    def test_gen_021_5bit_single_member(self):
        """GEN-021: 5-bit register is a single struct member, no _reg0"""
        self.assertIn("reg_5bit;", self.header)
        self.assertNotIn("reg_5bit_reg0", self.header)

    def test_gen_021_1bit_single_member(self):
        """GEN-021: 1-bit register is a single struct member, no _reg0"""
        self.assertIn("reg_1bit;", self.header)
        self.assertNotIn("reg_1bit_reg0", self.header)


# ---------------------------------------------------------------------------
# GEN-022  –  Markdown Width column – YAML source
# ---------------------------------------------------------------------------

class TestMarkdownWidthColumnYAML(unittest.TestCase):
    """GEN-022: Markdown register-map table Width column reports the actual
    declared width for every register defined via YAML."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        module = _parse_yaml(YAML_MULTI, self.tmp)
        self.rows = _extract_md_table_rows(_generate_markdown(module, self.tmp))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _width_of(self, name: str) -> int:
        for r in self.rows:
            if r['name'] == name:
                return r['width']
        self.fail(f"Register '{name}' not found in markdown table")

    def test_gen_022_1bit(self):
        """GEN-022: Markdown Width = 1 for 1-bit register"""
        self.assertEqual(self._width_of('reg_1bit'), 1)

    def test_gen_022_5bit(self):
        """GEN-022: Markdown Width = 5 for 5-bit register"""
        self.assertEqual(self._width_of('reg_5bit'), 5)

    def test_gen_022_32bit(self):
        """GEN-022: Markdown Width = 32 for 32-bit register"""
        self.assertEqual(self._width_of('reg_32bit'), 32)

    def test_gen_022_33bit(self):
        """GEN-022: Markdown Width = 33 for 33-bit register"""
        self.assertEqual(self._width_of('reg_33bit'), 33)

    def test_gen_022_64bit(self):
        """GEN-022: Markdown Width = 64 for 64-bit register"""
        self.assertEqual(self._width_of('reg_64bit'), 64)


# ---------------------------------------------------------------------------
# GEN-023  –  Markdown Width column – VHDL-annotation source
# ---------------------------------------------------------------------------

class TestMarkdownWidthColumnVHDL(unittest.TestCase):
    """GEN-023: Markdown register-map table Width column reports the actual
    declared width for every register defined via VHDL @axion annotations."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        module = _parse_vhdl(VHDL_MULTI, self.tmp)
        self.rows = _extract_md_table_rows(_generate_markdown(module, self.tmp))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _width_of(self, name: str) -> int:
        for r in self.rows:
            if r['name'] == name:
                return r['width']
        self.fail(f"Register '{name}' not found in markdown table")

    def test_gen_023_1bit(self):
        """GEN-023: Markdown Width = 1 for 1-bit register"""
        self.assertEqual(self._width_of('reg_1bit'), 1)

    def test_gen_023_5bit(self):
        """GEN-023: Markdown Width = 5 for 5-bit register"""
        self.assertEqual(self._width_of('reg_5bit'), 5)

    def test_gen_023_32bit(self):
        """GEN-023: Markdown Width = 32 for 32-bit register"""
        self.assertEqual(self._width_of('reg_32bit'), 32)

    def test_gen_023_33bit(self):
        """GEN-023: Markdown Width = 33 for 33-bit register"""
        self.assertEqual(self._width_of('reg_33bit'), 33)

    def test_gen_023_64bit(self):
        """GEN-023: Markdown Width = 64 for 64-bit register"""
        self.assertEqual(self._width_of('reg_64bit'), 64)


# ---------------------------------------------------------------------------
# SUB-008  –  Packed field width propagation to header – YAML source
# ---------------------------------------------------------------------------

class TestPackedFieldMasksYAML(unittest.TestCase):
    """SUB-008: Generated header MASK and SHIFT macros match declared
    bit_offset and width for packed fields defined via YAML.

    Fields:  enable  bit_offset=0 width=1  → MASK=0x1   SHIFT=0
             mode    bit_offset=1 width=3  → MASK=0xE   SHIFT=1
             divider bit_offset=4 width=8  → MASK=0xFF0 SHIFT=4
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        module = _parse_yaml(YAML_PACKED, self.tmp)
        self.header = _generate_header(module, self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_sub_008_enable_mask(self):
        """SUB-008: enable MASK = 0x1"""
        self.assertRegex(self.header, r'CTRL_ENABLE_MASK\s+0x1\b')

    def test_sub_008_enable_shift(self):
        """SUB-008: enable SHIFT = 0"""
        self.assertRegex(self.header, r'CTRL_ENABLE_SHIFT\s+0\b')

    def test_sub_008_mode_mask(self):
        """SUB-008: mode MASK = 0xE"""
        self.assertRegex(self.header, r'CTRL_MODE_MASK\s+0xE\b')

    def test_sub_008_mode_shift(self):
        """SUB-008: mode SHIFT = 1"""
        self.assertRegex(self.header, r'CTRL_MODE_SHIFT\s+1\b')

    def test_sub_008_divider_mask(self):
        """SUB-008: divider MASK = 0xFF0"""
        self.assertRegex(self.header, r'CTRL_DIVIDER_MASK\s+0xFF0\b')

    def test_sub_008_divider_shift(self):
        """SUB-008: divider SHIFT = 4"""
        self.assertRegex(self.header, r'CTRL_DIVIDER_SHIFT\s+4\b')


# ---------------------------------------------------------------------------
# SUB-007  –  Packed field width propagation to header – VHDL source
# ---------------------------------------------------------------------------

class TestPackedFieldMasksVHDL(unittest.TestCase):
    """SUB-007: Generated header MASK and SHIFT macros match declared
    BIT_OFFSET and width for packed fields defined via VHDL @axion
    annotations with REG_NAME / BIT_OFFSET."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        module = _parse_vhdl(VHDL_PACKED, self.tmp)
        self.header = _generate_header(module, self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_sub_007_enable_mask(self):
        """SUB-007: enable MASK = 0x1"""
        self.assertRegex(self.header, r'CTRL_ENABLE_MASK\s+0x1\b')

    def test_sub_007_enable_shift(self):
        """SUB-007: enable SHIFT = 0"""
        self.assertRegex(self.header, r'CTRL_ENABLE_SHIFT\s+0\b')

    def test_sub_007_mode_mask(self):
        """SUB-007: mode MASK = 0xE"""
        self.assertRegex(self.header, r'CTRL_MODE_MASK\s+0xE\b')

    def test_sub_007_mode_shift(self):
        """SUB-007: mode SHIFT = 1"""
        self.assertRegex(self.header, r'CTRL_MODE_SHIFT\s+1\b')

    def test_sub_007_divider_mask(self):
        """SUB-007: divider MASK = 0xFF0"""
        self.assertRegex(self.header, r'CTRL_DIVIDER_MASK\s+0xFF0\b')

    def test_sub_007_divider_shift(self):
        """SUB-007: divider SHIFT = 4"""
        self.assertRegex(self.header, r'CTRL_DIVIDER_SHIFT\s+4\b')


# ---------------------------------------------------------------------------
# GEN-026  –  Packed container is exactly one uint32_t, no split
# ---------------------------------------------------------------------------

class TestPackedContainerWidth(unittest.TestCase):
    """GEN-026: Packed register container appears as a single uint32_t
    member in the struct – no _reg0 / _reg1 splitting."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        module = _parse_yaml(YAML_PACKED, self.tmp)
        self.header = _generate_header(module, self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_gen_026_single_member(self):
        """GEN-026: Packed container 'ctrl' is one member, no _reg0"""
        self.assertIn("ctrl;", self.header)
        self.assertNotIn("ctrl_reg0", self.header)


# ---------------------------------------------------------------------------
# GEN-027  –  VHDL entity port width – YAML source
# ---------------------------------------------------------------------------

class TestVHDLPortWidthYAML(unittest.TestCase):
    """GEN-027: Generated VHDL entity ports use the declared width for
    registers defined via YAML. Must not default to 32-bit."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        module = _parse_yaml(YAML_MULTI, self.tmp)
        self.vhdl = _generate_vhdl(module, self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_gen_027_1bit_port(self):
        """GEN-027: 1-bit register generates std_logic port"""
        self.assertRegex(self.vhdl, r'reg_1bit\s*:\s*(in|out)\s+std_logic\b')
        self.assertNotIn('reg_1bit : out std_logic_vector(31 downto 0)', self.vhdl)

    def test_gen_027_5bit_port(self):
        """GEN-027: 5-bit register generates std_logic_vector(4 downto 0)"""
        self.assertRegex(self.vhdl, r'reg_5bit\s*:\s*(in|out)\s+std_logic_vector\(4 downto 0\)')
        self.assertNotIn('reg_5bit : out std_logic_vector(31 downto 0)', self.vhdl)

    def test_gen_027_32bit_port(self):
        """GEN-027: 32-bit register generates std_logic_vector(31 downto 0)"""
        self.assertRegex(self.vhdl, r'reg_32bit\s*:\s*(in|out)\s+std_logic_vector\(31 downto 0\)')

    def test_gen_027_33bit_port(self):
        """GEN-027: 33-bit register generates std_logic_vector(32 downto 0)"""
        self.assertRegex(self.vhdl, r'reg_33bit\s*:\s*(in|out)\s+std_logic_vector\(32 downto 0\)')
        self.assertNotIn('reg_33bit : out std_logic_vector(31 downto 0)', self.vhdl)

    def test_gen_027_64bit_port(self):
        """GEN-027: 64-bit register generates std_logic_vector(63 downto 0)"""
        self.assertRegex(self.vhdl, r'reg_64bit\s*:\s*(in|out)\s+std_logic_vector\(63 downto 0\)')
        self.assertNotIn('reg_64bit : out std_logic_vector(31 downto 0)', self.vhdl)


# ---------------------------------------------------------------------------
# GEN-028  –  VHDL entity port width – VHDL-annotation source
# ---------------------------------------------------------------------------

class TestVHDLPortWidthVHDL(unittest.TestCase):
    """GEN-028: Generated VHDL entity ports use the declared width for
    registers defined via VHDL @axion annotations."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        module = _parse_vhdl(VHDL_MULTI, self.tmp)
        self.vhdl = _generate_vhdl(module, self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_gen_028_1bit_port(self):
        """GEN-028: 1-bit register generates std_logic port"""
        self.assertRegex(self.vhdl, r'reg_1bit\s*:\s*(in|out)\s+std_logic\b')

    def test_gen_028_5bit_port(self):
        """GEN-028: 5-bit register generates std_logic_vector(4 downto 0)"""
        self.assertRegex(self.vhdl, r'reg_5bit\s*:\s*(in|out)\s+std_logic_vector\(4 downto 0\)')

    def test_gen_028_32bit_port(self):
        """GEN-028: 32-bit register generates std_logic_vector(31 downto 0)"""
        self.assertRegex(self.vhdl, r'reg_32bit\s*:\s*(in|out)\s+std_logic_vector\(31 downto 0\)')

    def test_gen_028_33bit_port(self):
        """GEN-028: 33-bit register generates std_logic_vector(32 downto 0)"""
        self.assertRegex(self.vhdl, r'reg_33bit\s*:\s*(in|out)\s+std_logic_vector\(32 downto 0\)')

    def test_gen_028_64bit_port(self):
        """GEN-028: 64-bit register generates std_logic_vector(63 downto 0)"""
        self.assertRegex(self.vhdl, r'reg_64bit\s*:\s*(in|out)\s+std_logic_vector\(63 downto 0\)')


# ---------------------------------------------------------------------------
# ADDR-006 regression guard  –  auto-address skips correctly for >32-bit
# ---------------------------------------------------------------------------

class TestAutoAddressWideRegisters(unittest.TestCase):
    """ADDR-006 regression: auto-address assignment reserves the right
    number of 4-byte slots for wide registers.

    Expected layout:
      reg_1bit   @ 0x00  (1 reg  → next 0x04)
      reg_5bit   @ 0x04  (1 reg  → next 0x08)
      reg_32bit  @ 0x08  (1 reg  → next 0x0C)
      reg_33bit  @ 0x0C  (2 regs → next 0x14)
      reg_64bit  @ 0x14  (2 regs → next 0x1C)
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.module = _parse_yaml(YAML_MULTI, self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _reg(self, name: str) -> dict:
        for r in self.module['registers']:
            if r['signal_name'] == name:
                return r
        self.fail(f"Register '{name}' not found")

    def test_addr_006_sequential_addresses(self):
        """ADDR-006: Wide registers reserve correct address slots"""
        self.assertEqual(self._reg('reg_1bit')['relative_address_int'],  0x00)
        self.assertEqual(self._reg('reg_5bit')['relative_address_int'],  0x04)
        self.assertEqual(self._reg('reg_32bit')['relative_address_int'], 0x08)
        self.assertEqual(self._reg('reg_33bit')['relative_address_int'], 0x0C)
        self.assertEqual(self._reg('reg_64bit')['relative_address_int'], 0x14)


# ---------------------------------------------------------------------------
# End-to-end consistency  –  GEN-019 + GEN-021 + GEN-022 exercised together
# ---------------------------------------------------------------------------

class TestE2EConsistencyYAML(unittest.TestCase):
    """E2E: Header and Markdown are mutually consistent for all registers
    when the source is YAML.  Exercises GEN-019, GEN-021, GEN-022."""

    EXPECTED = {
        'reg_1bit':  1,
        'reg_5bit':  5,
        'reg_32bit': 32,
        'reg_33bit': 33,
        'reg_64bit': 64,
    }

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.module = _parse_yaml(YAML_MULTI, self.tmp)
        self.header = _generate_header(self.module, self.tmp)
        self.md_rows = _extract_md_table_rows(
            _generate_markdown(self.module, self.tmp)
        )

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_e2e_yaml_markdown_widths(self):
        """GEN-022 E2E: all markdown widths match declared widths"""
        md_map = {r['name']: r['width'] for r in self.md_rows}
        for name, expected_w in self.EXPECTED.items():
            with self.subTest(register=name):
                self.assertIn(name, md_map)
                self.assertEqual(md_map[name], expected_w)

    def test_e2e_yaml_header_wide_split(self):
        """GEN-021 E2E: 33-bit and 64-bit produce _REG0/_REG1 offset macros"""
        for name in ('reg_33bit', 'reg_64bit'):
            with self.subTest(register=name):
                self.assertIn(f"{name.upper()}_REG0_OFFSET", self.header)
                self.assertIn(f"{name.upper()}_REG1_OFFSET", self.header)

    def test_e2e_yaml_header_narrow_not_split(self):
        """GEN-019 E2E: 1/5/32-bit produce single _OFFSET macro"""
        for name in ('reg_1bit', 'reg_5bit', 'reg_32bit'):
            with self.subTest(register=name):
                self.assertIn(f"{name.upper()}_OFFSET", self.header)
                self.assertNotIn(f"{name.upper()}_REG0_OFFSET", self.header)


class TestE2EConsistencyVHDL(unittest.TestCase):
    """E2E: Header and Markdown are mutually consistent for all registers
    when the source is VHDL annotations.  Exercises GEN-020, GEN-021, GEN-023."""

    EXPECTED = {
        'reg_1bit':  1,
        'reg_5bit':  5,
        'reg_32bit': 32,
        'reg_33bit': 33,
        'reg_64bit': 64,
    }

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.module = _parse_vhdl(VHDL_MULTI, self.tmp)
        self.header = _generate_header(self.module, self.tmp)
        self.md_rows = _extract_md_table_rows(
            _generate_markdown(self.module, self.tmp)
        )

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_e2e_vhdl_markdown_widths(self):
        """GEN-023 E2E: all markdown widths match declared widths"""
        md_map = {r['name']: r['width'] for r in self.md_rows}
        for name, expected_w in self.EXPECTED.items():
            with self.subTest(register=name):
                self.assertIn(name, md_map)
                self.assertEqual(md_map[name], expected_w)

    def test_e2e_vhdl_header_wide_split(self):
        """GEN-021 E2E: 33-bit and 64-bit produce _REG0/_REG1 offset macros"""
        for name in ('reg_33bit', 'reg_64bit'):
            with self.subTest(register=name):
                self.assertIn(f"{name.upper()}_REG0_OFFSET", self.header)
                self.assertIn(f"{name.upper()}_REG1_OFFSET", self.header)

    def test_e2e_vhdl_header_narrow_not_split(self):
        """GEN-020 E2E: 1/5/32-bit produce single _OFFSET macro"""
        for name in ('reg_1bit', 'reg_5bit', 'reg_32bit'):
            with self.subTest(register=name):
                self.assertIn(f"{name.upper()}_OFFSET", self.header)
                self.assertNotIn(f"{name.upper()}_REG0_OFFSET", self.header)


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
