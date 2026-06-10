#!/usr/bin/env python3
"""
test_doc_output_correctness.py – Documentation and XML output correctness tests

Requirement ↔ test-class mapping
---------------------------------
GEN-033  XML spirit:size and spirit:bitWidth reflect declared register width
         → TestXMLOutputWidth

GEN-034  HTML/Markdown Type column shows actual declared signal type
         → TestDocTypeColumn

GEN-035  Default value 0 renders as 0x0, not as the missing-value placeholder '-'
         → TestDocDefaultValue

GEN-036  Port Descriptions section uses correct direction (out/in) per access mode
         → TestDocPortDirection
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
from axion_hdl.doc_generators import DocGenerator, XMLGenerator


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


def _generate_xml(module: dict, tmp: str) -> str:
    gen = XMLGenerator(tmp)
    path = gen.generate_xml(module)
    with open(path) as f:
        return f.read()


def _generate_markdown(module: dict, tmp: str) -> str:
    gen = DocGenerator(tmp)
    path = gen.generate_markdown([module])
    with open(path) as f:
        return f.read()


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

# Registers with widths 1 / 5 / 16 / 32 – YAML
YAML_WIDTHS = """\
module: doc_test
registers:
  - name: flag
    access: RW
    width: 1
    default: 0
  - name: mode
    access: RW
    width: 5
    default: 0
  - name: data16
    access: RW
    width: 16
    default: 0
  - name: data32
    access: RW
    width: 32
    default: 0
"""

# Registers with default value 0 explicitly set vs no default
YAML_DEFAULT_ZERO = """\
module: default_test
registers:
  - name: ctrl
    access: RW
    width: 8
    default: 0
  - name: status
    access: RO
    width: 8
"""

# Registers with all three access modes
YAML_ACCESS_MODES = """\
module: access_test
registers:
  - name: rw_reg
    access: RW
    width: 8
    default: 0
  - name: ro_reg
    access: RO
    width: 8
  - name: wo_reg
    access: WO
    width: 8
    default: 0
"""

# Same widths – VHDL @axion annotations
VHDL_WIDTHS = """\
library ieee;
use ieee.std_logic_1164.all;

entity doc_test is
end entity;

architecture rtl of doc_test is
    signal flag   : std_logic;                        -- @axion RW ADDR=0x00
    signal mode   : std_logic_vector(4 downto 0);     -- @axion RW ADDR=0x04
    signal data16 : std_logic_vector(15 downto 0);    -- @axion RW ADDR=0x08
    signal data32 : std_logic_vector(31 downto 0);    -- @axion RW ADDR=0x0C
begin
end architecture;
"""


# ---------------------------------------------------------------------------
# GEN-033 – XML spirit:size and spirit:bitWidth reflect declared width
# ---------------------------------------------------------------------------

class TestXMLOutputWidth(unittest.TestCase):
    """GEN-033: Generated SPIRIT XML must use the declared register width in
    spirit:size and spirit:bitWidth, not a hardcoded 32."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        module = _parse_yaml(YAML_WIDTHS, self.tmp)
        self.xml = _generate_xml(module, self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _sizes_for(self, reg_name: str):
        """Return (spirit:size, spirit:bitWidth) values for a register."""
        pattern = (
            rf'<spirit:name>{reg_name}</spirit:name>.*?'
            r'<spirit:size>(\d+)</spirit:size>.*?'
            r'<spirit:bitWidth>(\d+)</spirit:bitWidth>'
        )
        m = re.search(pattern, self.xml, re.DOTALL)
        if not m:
            self.fail(f"Register '{reg_name}' not found in XML output")
        return int(m.group(1)), int(m.group(2))

    def test_gen_033_1bit_size(self):
        """GEN-033: 1-bit register → spirit:size=1, spirit:bitWidth=1"""
        size, bitwidth = self._sizes_for('flag')
        self.assertEqual(size, 1)
        self.assertEqual(bitwidth, 1)

    def test_gen_033_5bit_size(self):
        """GEN-033: 5-bit register → spirit:size=5, spirit:bitWidth=5"""
        size, bitwidth = self._sizes_for('mode')
        self.assertEqual(size, 5)
        self.assertEqual(bitwidth, 5)

    def test_gen_033_16bit_size(self):
        """GEN-033: 16-bit register → spirit:size=16, spirit:bitWidth=16"""
        size, bitwidth = self._sizes_for('data16')
        self.assertEqual(size, 16)
        self.assertEqual(bitwidth, 16)

    def test_gen_033_32bit_size(self):
        """GEN-033: 32-bit register → spirit:size=32, spirit:bitWidth=32"""
        size, bitwidth = self._sizes_for('data32')
        self.assertEqual(size, 32)
        self.assertEqual(bitwidth, 32)

    def test_gen_033_no_hardcoded_32_for_narrow(self):
        """GEN-033: narrow registers must not have spirit:size=32 or spirit:bitWidth=32"""
        # Split on register boundaries so we don't match across registers
        blocks = re.split(r'<spirit:register[^>]*>', self.xml)
        for block in blocks:
            name_m = re.search(r'<spirit:name>(\w+)</spirit:name>', block)
            if not name_m or name_m.group(1) not in ('flag', 'mode', 'data16'):
                continue
            reg = name_m.group(1)
            self.assertNotIn('<spirit:size>32</spirit:size>', block,
                             f"Register '{reg}' still has hardcoded spirit:size=32")
            self.assertNotIn('<spirit:bitWidth>32</spirit:bitWidth>', block,
                             f"Register '{reg}' still has hardcoded spirit:bitWidth=32")


class TestXMLOutputWidthVHDL(unittest.TestCase):
    """GEN-033: XML width correctness for VHDL-annotation source."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        module = _parse_vhdl(VHDL_WIDTHS, self.tmp)
        self.xml = _generate_xml(module, self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _sizes_for(self, reg_name: str):
        pattern = (
            rf'<spirit:name>{reg_name}</spirit:name>.*?'
            r'<spirit:size>(\d+)</spirit:size>.*?'
            r'<spirit:bitWidth>(\d+)</spirit:bitWidth>'
        )
        m = re.search(pattern, self.xml, re.DOTALL)
        if not m:
            self.fail(f"Register '{reg_name}' not found in XML output")
        return int(m.group(1)), int(m.group(2))

    def test_gen_033_vhdl_1bit(self):
        """GEN-033: VHDL std_logic → spirit:size=1, spirit:bitWidth=1"""
        size, bitwidth = self._sizes_for('flag')
        self.assertEqual(size, 1)
        self.assertEqual(bitwidth, 1)

    def test_gen_033_vhdl_16bit(self):
        """GEN-033: VHDL std_logic_vector(15 downto 0) → spirit:size=16, spirit:bitWidth=16"""
        size, bitwidth = self._sizes_for('data16')
        self.assertEqual(size, 16)
        self.assertEqual(bitwidth, 16)


# ---------------------------------------------------------------------------
# GEN-034 – Type column in Markdown shows actual declared signal type
# ---------------------------------------------------------------------------

class TestDocTypeColumn(unittest.TestCase):
    """GEN-034: The Type column in the register table and the Type field in
    Port Descriptions must show the actual declared signal type, not a
    hardcoded string like 'std_logic_vector(31 downto 0)'."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        module = _parse_yaml(YAML_WIDTHS, self.tmp)
        self.md = _generate_markdown(module, self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_gen_034_1bit_table_type(self):
        """GEN-034: 1-bit register shows std_logic in table Type column"""
        self.assertRegex(self.md, r'\|\s*`flag`\s*\|\s*std_logic\b')

    def test_gen_034_5bit_table_type(self):
        """GEN-034: 5-bit register shows std_logic_vector(4 downto 0) in table"""
        self.assertRegex(self.md, r'\|\s*`mode`\s*\|\s*std_logic_vector\(4 downto 0\)')

    def test_gen_034_16bit_table_type(self):
        """GEN-034: 16-bit register shows std_logic_vector(15 downto 0) in table"""
        self.assertRegex(self.md, r'\|\s*`data16`\s*\|\s*std_logic_vector\(15 downto 0\)')

    def test_gen_034_no_hardcoded_31_for_narrow(self):
        """GEN-034: narrow registers must not show std_logic_vector(31 downto 0) as their type"""
        for reg in ('flag', 'mode', 'data16'):
            self.assertNotRegex(
                self.md,
                rf'\|\s*`{reg}`\s*\|\s*std_logic_vector\(31 downto 0\)',
                f"Register '{reg}' still shows hardcoded 32-bit type"
            )

    def _port_desc_block(self, reg_name: str) -> str:
        """Extract the Port Descriptions section for a single register."""
        m = re.search(
            rf'#### {reg_name}\n(.*?)(?=\n#### |\n---|\Z)',
            self.md, re.DOTALL
        )
        return m.group(0) if m else ''

    def test_gen_034_port_desc_1bit_type(self):
        """GEN-034: Port Descriptions Type field for 1-bit register shows std_logic"""
        block = self._port_desc_block('flag')
        self.assertIn('std_logic', block)
        self.assertNotIn('std_logic_vector(31 downto 0)', block)

    def test_gen_034_port_desc_16bit_type(self):
        """GEN-034: Port Descriptions Type field for 16-bit register shows correct type"""
        block = self._port_desc_block('data16')
        self.assertIn('std_logic_vector(15 downto 0)', block)
        self.assertNotIn('std_logic_vector(31 downto 0)', block)


# ---------------------------------------------------------------------------
# GEN-035 – Default value 0 renders as 0x0, not '-'
# ---------------------------------------------------------------------------

class TestDocDefaultValue(unittest.TestCase):
    """GEN-035: A register with default: 0 must display '0x0' in the
    generated Markdown table. The '-' placeholder is only for registers
    with no declared default."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        module = _parse_yaml(YAML_DEFAULT_ZERO, self.tmp)
        self.md = _generate_markdown(module, self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_gen_035_default_zero_shows_0x0(self):
        """GEN-035: Register with default=0 shows 0x0 in table"""
        self.assertRegex(self.md, r'\|\s*`ctrl`\s*\|.*?\|\s*0x0\s*\|')

    def test_gen_035_no_default_shows_dash(self):
        """GEN-035: Register with no default still shows '-' in table"""
        self.assertRegex(self.md, r'\|\s*`status`\s*\|.*?\|\s*-\s*\|')

    def test_gen_035_zero_is_not_dash(self):
        """GEN-035: '0x0' and '-' must not appear on the same ctrl row"""
        for line in self.md.splitlines():
            if '`ctrl`' in line:
                self.assertIn('0x0', line, "ctrl default should be 0x0")
                self.assertNotRegex(line, r'\|\s*-\s*\|', "ctrl default must not be '-'")
                break
        else:
            self.fail("ctrl register not found in markdown table")


# ---------------------------------------------------------------------------
# GEN-036 – Port direction in Port Descriptions matches access mode
# ---------------------------------------------------------------------------

class TestDocPortDirection(unittest.TestCase):
    """GEN-036: The port direction in Port Descriptions must reflect the
    access mode — 'out' for RW/WO registers, 'in' for RO registers."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        module = _parse_yaml(YAML_ACCESS_MODES, self.tmp)
        self.md = _generate_markdown(module, self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_gen_036_rw_is_out(self):
        """GEN-036: RW register data port direction is 'out'"""
        self.assertRegex(self.md, r'`rw_reg`\s*\(out\)')

    def test_gen_036_ro_is_in(self):
        """GEN-036: RO register data port direction is 'in'"""
        self.assertRegex(self.md, r'`ro_reg`\s*\(in\)')

    def test_gen_036_wo_is_out(self):
        """GEN-036: WO register data port direction is 'out'"""
        self.assertRegex(self.md, r'`wo_reg`\s*\(out\)')

    def test_gen_036_rw_not_inout(self):
        """GEN-036: RW register must not be labelled 'inout'"""
        self.assertNotRegex(self.md, r'`rw_reg`\s*\(inout\)')

    def test_gen_036_ro_not_inout(self):
        """GEN-036: RO register must not be labelled 'inout'"""
        self.assertNotRegex(self.md, r'`ro_reg`\s*\(inout\)')


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
