#!/usr/bin/env python3
"""
test_hierarchy.py - Hierarchy File Support Tests

Maps to requirements in docs/source/requirements-core.md.

Requirement ↔ test-class mapping
---------------------------------
HIER-001  CLI --hier flag
         → TestHierCLIFlag

HIER-002  YAML hierarchy parse
         → TestHierParserYAML

HIER-003  TOML hierarchy parse
         → TestHierParserTOML

HIER-004  JSON hierarchy parse
         → TestHierParserJSON

HIER-005  XML hierarchy parse
         → TestHierParserXML

HIER-006  base_addr override (single instance)
         → TestHierBaseAddrOverride

HIER-007  Single-instance output naming (unchanged)
         → TestHierOutputNaming

HIER-008  Multi-instance output naming (instance name)
         → TestHierOutputNaming

HIER-009  instance field required for duplicates
         → TestHierValidation

HIER-010  Duplicate instance name rejected (rule-check)
         → TestHierValidation

HIER-011  Address overlap detection (rule-check)
         → TestHierValidation

HIER-012  Unknown module error (rule-check)
         → TestHierValidation

HIER-013  address_map.html generation
         → TestHierAddressMapHTML

HIER-014  address_map.html table correctness
         → TestHierAddressMapHTML

HIER-015  Backward compatibility (no --hier)
         → TestHierBackwardCompat

HIER-016  Unsupported format error
         → TestHierParserFormats
"""

import os
import sys
import json
import tempfile
import shutil
import unittest
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from axion_hdl.hierarchy_parser import HierarchyParser
from axion_hdl.axion import AxionHDL
from axion_hdl.rule_checker import RuleChecker
from axion_hdl.generator import VHDLGenerator
from axion_hdl.systemverilog_generator import SystemVerilogGenerator
from axion_hdl.doc_generators import AddressMapHTMLGenerator


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

EXAMPLES_DIR = project_root / "examples"
SPI_TOML = str(EXAMPLES_DIR / "spi_master.toml")

_MINIMAL_MODULE = {
    'name': 'spi_master',
    'file': 'spi_master.toml',
    'base_address': 0x0000,
    'cdc_enabled': False,
    'cdc_stages': 2,
    'registers': [
        {'signal_name': 'control', 'address': 0x00, 'relative_address': '0x00',
         'access_mode': 'RW', 'width': 32, 'description': '', 'signal_type': '[31:0]',
         'read_strobe': False, 'write_strobe': False, 'default_value': '0x00000000',
         'is_packed': False},
        {'signal_name': 'status', 'address': 0x04, 'relative_address': '0x04',
         'access_mode': 'RO', 'width': 32, 'description': '', 'signal_type': '[31:0]',
         'read_strobe': False, 'write_strobe': False, 'default_value': '0x00000000',
         'is_packed': False},
    ],
    'parse_errors': [],
    'packed_registers': [],
}


def _write(directory, name, content):
    path = os.path.join(directory, name)
    with open(path, 'w') as f:
        f.write(content)
    return path


def _clone(module, **overrides):
    m = dict(module)
    m.update(overrides)
    return m


# ---------------------------------------------------------------------------
# HIER-002 — YAML hierarchy parse
# ---------------------------------------------------------------------------

class TestHierParserYAML(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_hier_002_yaml_parse(self):
        """HIER-002: YAML format hierarchy file is parsed correctly."""
        content = """
instances:
  - module: spi_master
    instance: spi_master_0
    base_addr: "0x20000"
  - module: uart_ctrl
    base_addr: 0x30000
"""
        path = _write(self.tmp, "hier.yaml", content)
        result = HierarchyParser().parse(path)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['module'], 'spi_master')
        self.assertEqual(result[0]['instance'], 'spi_master_0')
        self.assertEqual(result[0]['base_addr'], 0x20000)
        self.assertEqual(result[1]['module'], 'uart_ctrl')
        self.assertIsNone(result[1]['instance'])
        self.assertEqual(result[1]['base_addr'], 0x30000)


# ---------------------------------------------------------------------------
# HIER-003 — TOML hierarchy parse
# ---------------------------------------------------------------------------

class TestHierParserTOML(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_hier_003_toml_parse(self):
        """HIER-003: TOML format hierarchy file is parsed correctly."""
        content = """
[[instances]]
module = "spi_master"
instance = "spi_master_0"
base_addr = "0x20000"

[[instances]]
module = "uart_ctrl"
base_addr = "0x30000"
"""
        path = _write(self.tmp, "hier.toml", content)
        result = HierarchyParser().parse(path)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['module'], 'spi_master')
        self.assertEqual(result[0]['instance'], 'spi_master_0')
        self.assertEqual(result[0]['base_addr'], 0x20000)
        self.assertEqual(result[1]['module'], 'uart_ctrl')
        self.assertIsNone(result[1]['instance'])
        self.assertEqual(result[1]['base_addr'], 0x30000)


# ---------------------------------------------------------------------------
# HIER-004 — JSON hierarchy parse
# ---------------------------------------------------------------------------

class TestHierParserJSON(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_hier_004_json_parse(self):
        """HIER-004: JSON format hierarchy file is parsed correctly."""
        data = {
            "instances": [
                {"module": "spi_master", "instance": "spi_master_0", "base_addr": "0x20000"},
                {"module": "uart_ctrl", "base_addr": "0x30000"},
            ]
        }
        path = _write(self.tmp, "hier.json", json.dumps(data))
        result = HierarchyParser().parse(path)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['module'], 'spi_master')
        self.assertEqual(result[0]['instance'], 'spi_master_0')
        self.assertEqual(result[0]['base_addr'], 0x20000)
        self.assertEqual(result[1]['module'], 'uart_ctrl')
        self.assertIsNone(result[1]['instance'])
        self.assertEqual(result[1]['base_addr'], 0x30000)


# ---------------------------------------------------------------------------
# HIER-005 — XML hierarchy parse
# ---------------------------------------------------------------------------

class TestHierParserXML(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_hier_005_xml_parse(self):
        """HIER-005: XML format hierarchy file is parsed correctly."""
        content = """<hierarchy>
  <instance module="spi_master" name="spi_master_0" base_addr="0x20000"/>
  <instance module="uart_ctrl" base_addr="0x30000"/>
</hierarchy>"""
        path = _write(self.tmp, "hier.xml", content)
        result = HierarchyParser().parse(path)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['module'], 'spi_master')
        self.assertEqual(result[0]['instance'], 'spi_master_0')
        self.assertEqual(result[0]['base_addr'], 0x20000)
        self.assertEqual(result[1]['module'], 'uart_ctrl')
        self.assertIsNone(result[1]['instance'])
        self.assertEqual(result[1]['base_addr'], 0x30000)


# ---------------------------------------------------------------------------
# HIER-016 — Unsupported format
# ---------------------------------------------------------------------------

class TestHierParserFormats(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_hier_016_unsupported_format(self):
        """HIER-016: Unsupported file extension raises ValueError."""
        path = _write(self.tmp, "hier.csv", "module,base_addr\nspi_master,0x1000")
        with self.assertRaises(ValueError):
            HierarchyParser().parse(path)


# ---------------------------------------------------------------------------
# HIER-006 — base_addr override (single instance)
# HIER-007 — Single-instance output naming unchanged
# HIER-008 — Multi-instance output naming by instance name
# ---------------------------------------------------------------------------

class TestHierBaseAddrOverride(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_hier_006_base_addr_override_single(self):
        """HIER-006: apply_hierarchy() replaces base_address from the hierarchy file."""
        axion = AxionHDL(output_dir=self.tmp)
        axion.add_source(SPI_TOML)
        axion.analyze()

        original_base = axion.analyzed_modules[0]['base_address']

        hier_path = _write(self.tmp, "hier.yaml",
                           "instances:\n  - module: spi_master\n    base_addr: 0x50000\n")
        axion.load_hierarchy(hier_path)
        axion.apply_hierarchy()

        self.assertNotEqual(axion.analyzed_modules[0]['base_address'], original_base)
        self.assertEqual(axion.analyzed_modules[0]['base_address'], 0x50000)


class TestHierOutputNaming(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_hier_007_single_instance_filename(self):
        """HIER-007: Single-instance module keeps original name in output filename."""
        axion = AxionHDL(output_dir=self.tmp)
        axion.add_source(SPI_TOML)
        axion.analyze()
        gen = VHDLGenerator(self.tmp)
        path = gen.generate_module(axion.analyzed_modules[0])
        self.assertIn('spi_master_axion_reg', os.path.basename(path))

    def test_hier_008_multi_instance_filename_vhdl(self):
        """HIER-008: Multi-instance VHDL output files named after instance field."""
        axion = AxionHDL(output_dir=self.tmp)
        axion.add_source(SPI_TOML)
        axion.analyze()

        hier_content = """instances:
  - module: spi_master
    instance: spi_master_0
    base_addr: 0x20000
  - module: spi_master
    instance: spi_master_1
    base_addr: 0x21000
"""
        hier_path = _write(self.tmp, "hier.yaml", hier_content)
        axion.load_hierarchy(hier_path)
        axion.apply_hierarchy()

        out_dir = os.path.join(self.tmp, "vhdl_out")
        gen = VHDLGenerator(out_dir)
        for module in axion.analyzed_modules:
            gen.generate_module(module)

        files = os.listdir(out_dir)
        self.assertTrue(any('spi_master_0_axion_reg' in f for f in files),
                        f"Expected spi_master_0_axion_reg.vhd in {files}")
        self.assertTrue(any('spi_master_1_axion_reg' in f for f in files),
                        f"Expected spi_master_1_axion_reg.vhd in {files}")
        self.assertFalse(any(f == 'spi_master_axion_reg.vhd' for f in files),
                         "Original (non-suffixed) file should not exist for multi-instance")

    def test_hier_008_multi_instance_filename_sv(self):
        """HIER-008: Multi-instance SV output files named after instance field."""
        axion = AxionHDL(output_dir=self.tmp)
        axion.add_source(SPI_TOML)
        axion.analyze()

        hier_content = """instances:
  - module: spi_master
    instance: spi_master_0
    base_addr: 0x20000
  - module: spi_master
    instance: spi_master_1
    base_addr: 0x21000
"""
        hier_path = _write(self.tmp, "hier.yaml", hier_content)
        axion.load_hierarchy(hier_path)
        axion.apply_hierarchy()

        out_dir = os.path.join(self.tmp, "sv_out")
        gen = SystemVerilogGenerator(out_dir)
        for module in axion.analyzed_modules:
            gen.generate_module(module)

        files = os.listdir(out_dir)
        self.assertTrue(any('spi_master_0_axion_reg' in f for f in files),
                        f"Expected spi_master_0_axion_reg.sv in {files}")
        self.assertTrue(any('spi_master_1_axion_reg' in f for f in files),
                        f"Expected spi_master_1_axion_reg.sv in {files}")


# ---------------------------------------------------------------------------
# HIER-009 — instance field required for duplicates
# HIER-010 — Duplicate instance name → rule-check error
# HIER-011 — Address overlap → rule-check error
# HIER-012 — Unknown module → rule-check error
# ---------------------------------------------------------------------------

class TestHierValidation(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_hier_009_missing_instance_field(self):
        """HIER-009: Missing instance field when module appears twice raises ValueError."""
        content = """instances:
  - module: spi_master
    base_addr: 0x20000
  - module: spi_master
    base_addr: 0x21000
"""
        path = _write(self.tmp, "hier.yaml", content)
        with self.assertRaises(ValueError):
            HierarchyParser().parse(path)

    def test_hier_010_duplicate_instance_name(self):
        """HIER-010: Duplicate instance name produces a rule-check error."""
        hierarchy = [
            {'module': 'spi_master', 'instance': 'spi_0', 'base_addr': 0x20000},
            {'module': 'spi_master', 'instance': 'spi_0', 'base_addr': 0x21000},
        ]
        modules = [_clone(_MINIMAL_MODULE)]
        checker = RuleChecker()
        checker.check_hierarchy(hierarchy, modules)
        self.assertTrue(any('spi_0' in e['msg'] for e in checker.errors),
                        f"Expected duplicate instance error. Got: {checker.errors}")

    def test_hier_011_address_overlap(self):
        """HIER-011: Overlapping address ranges produce a rule-check error."""
        # _MINIMAL_MODULE has registers at 0x00 and 0x04 → size = 4+4 = 8 bytes
        # spi_0: 0x20000–0x20007, spi_1: 0x20004–0x2000B → overlap
        hierarchy = [
            {'module': 'spi_master', 'instance': 'spi_0', 'base_addr': 0x20000},
            {'module': 'spi_master', 'instance': 'spi_1', 'base_addr': 0x20004},
        ]
        modules = [_clone(_MINIMAL_MODULE)]
        checker = RuleChecker()
        checker.check_hierarchy(hierarchy, modules)
        self.assertTrue(len(checker.errors) > 0,
                        f"Expected address overlap error. Got: {checker.errors}")
        self.assertTrue(any('overlap' in e['msg'].lower() for e in checker.errors),
                        f"Expected 'overlap' in error message. Got: {checker.errors}")

    def test_hier_012_unknown_module_error(self):
        """HIER-012: Module in hierarchy not found in analyzed sources → rule-check error."""
        hierarchy = [
            {'module': 'nonexistent_module', 'instance': None, 'base_addr': 0x10000},
        ]
        modules = [_clone(_MINIMAL_MODULE)]
        checker = RuleChecker()
        checker.check_hierarchy(hierarchy, modules)
        self.assertTrue(len(checker.errors) > 0,
                        f"Expected error for unknown module. Got: {checker.errors}")
        self.assertTrue(any('nonexistent_module' in e['msg'] for e in checker.errors),
                        f"Expected module name in error. Got: {checker.errors}")


# ---------------------------------------------------------------------------
# HIER-013 / HIER-014 — address_map.html generation and content
# ---------------------------------------------------------------------------

class TestHierAddressMapHTML(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _make_modules(self):
        m0 = _clone(_MINIMAL_MODULE, base_address=0x20000, _effective_name='spi_master_0')
        m1 = _clone(_MINIMAL_MODULE, base_address=0x21000, _effective_name='spi_master_1')
        return [m0, m1]

    def test_hier_013_address_map_html_generated(self):
        """HIER-013: generate_address_map_html() produces address_map.html in output dir."""
        axion = AxionHDL(output_dir=self.tmp)
        axion.add_source(SPI_TOML)
        axion.analyze()

        hier_content = """instances:
  - module: spi_master
    instance: spi_master_0
    base_addr: 0x20000
  - module: spi_master
    instance: spi_master_1
    base_addr: 0x21000
"""
        hier_path = _write(self.tmp, "hier.yaml", hier_content)
        axion.load_hierarchy(hier_path)
        axion.apply_hierarchy()
        axion.generate_address_map_html()

        expected = os.path.join(self.tmp, 'address_map.html')
        self.assertTrue(os.path.isfile(expected),
                        f"address_map.html not found in {self.tmp}")

    def test_hier_014_address_map_html_content(self):
        """HIER-014: address_map.html contains correct columns and instance rows."""
        modules = self._make_modules()
        gen = AddressMapHTMLGenerator(self.tmp)
        path = gen.generate(modules)

        with open(path) as f:
            html = f.read()

        # Check column headers
        for col in ['Instance Name', 'Module', 'Base Address', 'End Address', 'Size']:
            self.assertIn(col, html, f"Missing column header: {col}")

        # Check instance names
        self.assertIn('spi_master_0', html)
        self.assertIn('spi_master_1', html)

        # Check base addresses (hex format)
        self.assertIn('0x00020000', html)
        self.assertIn('0x00021000', html)


# ---------------------------------------------------------------------------
# HIER-015 — Backward compatibility (no --hier)
# ---------------------------------------------------------------------------

class TestHierBackwardCompat(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_hier_015_no_hier_backward_compat(self):
        """HIER-015: Without --hier, output filename and base_address are unchanged."""
        axion = AxionHDL(output_dir=self.tmp)
        axion.add_source(SPI_TOML)
        axion.analyze()

        original_base = axion.analyzed_modules[0]['base_address']
        original_name = axion.analyzed_modules[0]['name']

        # No hierarchy loaded — generate VHDL directly
        axion.generate_vhdl()

        expected = os.path.join(self.tmp, 'spi_master_axion_reg.vhd')
        self.assertTrue(os.path.isfile(expected),
                        f"Expected spi_master_axion_reg.vhd but not found in {self.tmp}")
        self.assertEqual(axion.analyzed_modules[0]['base_address'], original_base)
        self.assertEqual(axion.analyzed_modules[0]['name'], original_name)
        self.assertNotIn('address_map.html', os.listdir(self.tmp))


# ---------------------------------------------------------------------------
# HIER-001 — CLI --hier flag
# ---------------------------------------------------------------------------

class TestHierCLIFlag(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_hier_001_cli_flag(self):
        """HIER-001: --hier flag is accepted; hierarchy is applied before generation."""
        import subprocess
        hier_content = "instances:\n  - module: spi_master\n    base_addr: 0x50000\n"
        hier_path = _write(self.tmp, "hier.yaml", hier_content)

        result = subprocess.run(
            [sys.executable, '-m', 'axion_hdl.cli',
             '-s', SPI_TOML,
             '-o', self.tmp,
             '--hier', hier_path,
             '--vhdl'],
            capture_output=True, text=True,
            cwd=str(project_root)
        )
        self.assertEqual(result.returncode, 0,
                         f"CLI returned non-zero.\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
        self.assertTrue(os.path.isfile(os.path.join(self.tmp, 'spi_master_axion_reg.vhd')),
                        f"VHDL output not found. Files: {os.listdir(self.tmp)}")
        self.assertTrue(os.path.isfile(os.path.join(self.tmp, 'address_map.html')),
                        f"address_map.html not found. Files: {os.listdir(self.tmp)}")


# ---------------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
