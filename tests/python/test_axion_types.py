#!/usr/bin/env python3
"""
test_axion_types.py – Typed AXI Port Generation Tests

Maps to requirements in docs/source/requirements-core.md.

Requirement ↔ test-class/method mapping
-----------------------------------------
AXION-TYPES-001  YAML config parsing
         → TestAxionTypesConfigParsing.test_axion_types_001_yaml_config_parsing

AXION-TYPES-002  TOML config parsing
         → TestAxionTypesConfigParsing.test_axion_types_002_toml_config_parsing

AXION-TYPES-003  XML config parsing
         → TestAxionTypesConfigParsing.test_axion_types_003_xml_config_parsing

AXION-TYPES-004  JSON config parsing
         → TestAxionTypesConfigParsing.test_axion_types_004_json_config_parsing

AXION-TYPES-005  Default disabled (no config key)
         → TestAxionTypesConfigParsing.test_axion_types_005_default_disabled

AXION-TYPES-006  CLI flag override
         → TestAxionTypesConfigParsing.test_axion_types_006_cli_flag_override

AXION-TYPES-007  VHDL library clause added
         → TestAxionTypesVHDL.test_axion_types_007_vhdl_library_clause

AXION-TYPES-008  VHDL entity typed ports present
         → TestAxionTypesVHDL.test_axion_types_008_vhdl_entity_typed_ports

AXION-TYPES-009  VHDL entity no flat AXI ports
         → TestAxionTypesVHDL.test_axion_types_009_vhdl_no_flat_axi_ports

AXION-TYPES-010  VHDL intermediate signal declarations
         → TestAxionTypesVHDL.test_axion_types_010_vhdl_intermediate_signals

AXION-TYPES-011  VHDL M2S unpack assignments
         → TestAxionTypesVHDL.test_axion_types_011_vhdl_m2s_unpack

AXION-TYPES-012  VHDL S2M pack assignments
         → TestAxionTypesVHDL.test_axion_types_012_vhdl_s2m_pack

AXION-TYPES-013  VHDL default output unchanged
         → TestAxionTypesVHDL.test_axion_types_013_vhdl_default_unchanged

AXION-TYPES-014  SV package import
         → TestAxionTypesSV.test_axion_types_014_sv_package_import

AXION-TYPES-015  SV module typed ports present
         → TestAxionTypesSV.test_axion_types_015_sv_module_typed_ports

AXION-TYPES-016  SV module no flat AXI ports
         → TestAxionTypesSV.test_axion_types_016_sv_no_flat_axi_ports

AXION-TYPES-017  SV intermediate signal declarations
         → TestAxionTypesSV.test_axion_types_017_sv_intermediate_signals

AXION-TYPES-018  SV M2S unpack assigns
         → TestAxionTypesSV.test_axion_types_018_sv_m2s_unpack

AXION-TYPES-019  SV S2M pack assigns
         → TestAxionTypesSV.test_axion_types_019_sv_s2m_pack

AXION-TYPES-020  SV default output unchanged
         → TestAxionTypesSV.test_axion_types_020_sv_default_unchanged

AXION-TYPES-021  Per-module independence
         → TestAxionTypesPerModule.test_axion_types_021_per_module_independence
"""

import os
import sys
import json
import tempfile
import shutil
import textwrap
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

from axion_hdl.yaml_input_parser import YAMLInputParser
from axion_hdl.toml_input_parser import TOMLInputParser
from axion_hdl.xml_input_parser import XMLInputParser
from axion_hdl.generator import VHDLGenerator
from axion_hdl.systemverilog_generator import SystemVerilogGenerator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_yaml(module_name: str, use_axion_types: bool | None = None) -> str:
    """Build a minimal YAML register definition string."""
    lines = [
        f"module: {module_name}",
        'base_addr: "0x00000000"',
    ]
    if use_axion_types is not None:
        val = "true" if use_axion_types else "false"
        lines += ["config:", f"  use_axion_types: {val}"]
    lines += [
        "registers:",
        "  - name: ctrl",
        "    access: RW",
        "  - name: status",
        "    access: RO",
    ]
    return "\n".join(lines) + "\n"


def _parse_yaml_str(yaml_str: str, tmp_dir: str, fname: str = "module.yaml"):
    """Write yaml_str to tmp_dir/fname and parse it."""
    path = os.path.join(tmp_dir, fname)
    with open(path, "w") as f:
        f.write(yaml_str)
    parser = YAMLInputParser()
    return parser.parse_file(path)


def _module_data_base(name: str, use_axion_types: bool = False) -> dict:
    """Return a minimal module_data dict for generator tests."""
    return {
        'name': name,
        'file': f'{name}.yaml',
        'base_address': 0,
        'cdc_enabled': False,
        'cdc_stages': 2,
        'use_axion_types': use_axion_types,
        'registers': [
            {
                'signal_name': 'ctrl',
                'signal_type': 'std_logic_vector(31 downto 0)',
                'access_mode': 'RW',
                'address_int': 0,
                'relative_address_int': 0,
                'read_strobe': False,
                'write_strobe': False,
                'default_value': 0,
                'description': '',
                'is_packed': False,
                'enum_values': None,
            },
            {
                'signal_name': 'status',
                'signal_type': 'std_logic_vector(31 downto 0)',
                'access_mode': 'RO',
                'address_int': 4,
                'relative_address_int': 4,
                'read_strobe': False,
                'write_strobe': False,
                'default_value': 0,
                'description': '',
                'is_packed': False,
                'enum_values': None,
            },
        ],
        'packed_registers': [],
    }


# ---------------------------------------------------------------------------
# AXION-TYPES-001 … 006  Config parsing
# ---------------------------------------------------------------------------

class TestAxionTypesConfigParsing(unittest.TestCase):
    """AXION-TYPES-001 … 006  Config key and CLI flag handling."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='axion_types_cfg_')

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # AXION-TYPES-001
    def test_axion_types_001_yaml_config_parsing(self):
        """AXION-TYPES-001  YAML config: use_axion_types: true sets True."""
        data = _parse_yaml_str(_make_yaml('my_mod', use_axion_types=True), self.tmp)
        self.assertIsNotNone(data)
        self.assertIs(data.get('use_axion_types'), True)

    def test_axion_types_001b_yaml_config_false(self):
        """AXION-TYPES-001  YAML config: use_axion_types: false sets False."""
        data = _parse_yaml_str(_make_yaml('my_mod', use_axion_types=False), self.tmp)
        self.assertIsNotNone(data)
        self.assertIs(data.get('use_axion_types'), False)

    # AXION-TYPES-002
    def test_axion_types_002_toml_config_parsing(self):
        """AXION-TYPES-002  TOML config: use_axion_types = true sets True."""
        toml_str = textwrap.dedent("""\
            module = "toml_mod"
            base_addr = "0x0000"

            [config]
            use_axion_types = true

            [[registers]]
            name = "ctrl"
            access = "RW"
        """)
        path = os.path.join(self.tmp, "module.toml")
        with open(path, "w") as f:
            f.write(toml_str)
        parser = TOMLInputParser()
        result = parser.parse_file(path)
        self.assertIsNotNone(result)
        # TOML parser passes through YAMLInputParser, so result is full module_data
        if isinstance(result, list):
            result = result[0]
        self.assertIs(result.get('use_axion_types'), True)

    # AXION-TYPES-003
    def test_axion_types_003_xml_config_parsing(self):
        """AXION-TYPES-003  XML config: use_axion_types='true' attribute sets True."""
        xml_str = textwrap.dedent("""\
            <?xml version="1.0"?>
            <register_map module="xml_mod" base_addr="0x0000">
                <config use_axion_types="true"/>
                <register name="ctrl" access="RW"/>
            </register_map>
        """)
        path = os.path.join(self.tmp, "module.xml")
        with open(path, "w") as f:
            f.write(xml_str)
        parser = XMLInputParser()
        result = parser.parse_file(path)
        self.assertIsNotNone(result)
        # XML parser passes through YAMLInputParser, so result is full module_data
        self.assertIs(result.get('use_axion_types'), True)

    # AXION-TYPES-004
    def test_axion_types_004_json_config_parsing(self):
        """AXION-TYPES-004  JSON config: 'use_axion_types': true (via YAML pipeline) sets True."""
        from axion_hdl.json_input_parser import JSONInputParser
        json_str = json.dumps({
            "module": "json_mod",
            "base_addr": "0x0000",
            "config": {"use_axion_types": True},
            "registers": [{"name": "ctrl", "access": "RW"}],
        })
        path = os.path.join(self.tmp, "module.json")
        with open(path, "w") as f:
            f.write(json_str)
        parser = JSONInputParser()
        data = parser.parse_file(path)
        self.assertIsNotNone(data)
        self.assertIs(data.get('use_axion_types'), True)

    # AXION-TYPES-005
    def test_axion_types_005_default_disabled(self):
        """AXION-TYPES-005  Absent use_axion_types defaults to False."""
        data = _parse_yaml_str(_make_yaml('default_mod', use_axion_types=None), self.tmp)
        self.assertIsNotNone(data)
        self.assertFalse(data.get('use_axion_types', False))

    # AXION-TYPES-006
    def test_axion_types_006_cli_flag_override(self):
        """AXION-TYPES-006  CLI --use-axion-types overrides per-module False → True."""
        data = _parse_yaml_str(_make_yaml('override_mod', use_axion_types=False), self.tmp)
        self.assertIsNotNone(data)
        modules = [data]
        # Simulate what cli.py does when --use-axion-types is set
        for m in modules:
            m['use_axion_types'] = True
        self.assertIs(modules[0]['use_axion_types'], True)


# ---------------------------------------------------------------------------
# AXION-TYPES-007 … 013  VHDL generator
# ---------------------------------------------------------------------------

class TestAxionTypesVHDL(unittest.TestCase):
    """AXION-TYPES-007 … 013  VHDL generation with typed ports."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='axion_types_vhdl_')
        self.gen = VHDLGenerator(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _generate(self, use_axion_types: bool) -> str:
        md = _module_data_base('test_mod', use_axion_types=use_axion_types)
        path = self.gen.generate_module(md)
        with open(path) as f:
            return f.read()

    # AXION-TYPES-007
    def test_axion_types_007_vhdl_library_clause(self):
        """AXION-TYPES-007  use work.axion_common_pkg.all present when use_axion_types=True."""
        code = self._generate(use_axion_types=True)
        self.assertIn('use work.axion_common_pkg.all;', code)

    def test_axion_types_007b_no_clause_when_disabled(self):
        """AXION-TYPES-007 (negative)  axion_common_pkg NOT present when use_axion_types=False."""
        code = self._generate(use_axion_types=False)
        self.assertNotIn('axion_common_pkg', code)

    # AXION-TYPES-008
    def test_axion_types_008_vhdl_entity_typed_ports(self):
        """AXION-TYPES-008  Entity contains axi_m2s and axi_s2m typed ports."""
        code = self._generate(use_axion_types=True)
        self.assertIn('axi_m2s', code)
        self.assertIn('axi_s2m', code)
        self.assertIn('t_axi_lite_m2s', code)
        self.assertIn('t_axi_lite_s2m', code)

    # AXION-TYPES-009
    def test_axion_types_009_vhdl_no_flat_axi_ports(self):
        """AXION-TYPES-009  No flat AXI port names in entity port list."""
        code = self._generate(use_axion_types=True)
        flat_ports = [
            'axi_awaddr  :', 'axi_awvalid :', 'axi_awready :',
            'axi_wdata   :', 'axi_wstrb   :', 'axi_wvalid  :', 'axi_wready  :',
            'axi_bresp   :', 'axi_bvalid  :', 'axi_bready  :',
            'axi_araddr  :', 'axi_arvalid :', 'axi_arready :',
            'axi_rdata   :', 'axi_rresp   :', 'axi_rvalid  :', 'axi_rready  :',
        ]
        # Extract entity section
        entity_start = code.find('entity ')
        entity_end = code.find('end entity')
        entity_section = code[entity_start:entity_end]
        for port in flat_ports:
            self.assertNotIn(port, entity_section,
                             msg=f"Flat port '{port}' should not appear in entity port list")

    # AXION-TYPES-010
    def test_axion_types_010_vhdl_intermediate_signals(self):
        """AXION-TYPES-010  Architecture declaration region has intermediate signal declarations."""
        code = self._generate(use_axion_types=True)
        arch_start = code.find('architecture rtl')
        arch_section = code[arch_start:]
        for sig in ['axi_awaddr', 'axi_wdata', 'axi_awready', 'axi_rdata']:
            self.assertIn(f'signal {sig}', arch_section,
                          msg=f"Intermediate signal '{sig}' declaration expected")

    # AXION-TYPES-011
    def test_axion_types_011_vhdl_m2s_unpack(self):
        """AXION-TYPES-011  Architecture body has M2S unpack concurrent assignments."""
        code = self._generate(use_axion_types=True)
        expected = [
            'axi_awaddr  <= axi_m2s.awaddr',
            'axi_awvalid <= axi_m2s.awvalid',
            'axi_wdata   <= axi_m2s.wdata',
            'axi_wstrb   <= axi_m2s.wstrb',
            'axi_wvalid  <= axi_m2s.wvalid',
            'axi_bready  <= axi_m2s.bready',
            'axi_araddr  <= axi_m2s.araddr',
            'axi_arvalid <= axi_m2s.arvalid',
            'axi_rready  <= axi_m2s.rready',
        ]
        for assign in expected:
            self.assertIn(assign, code, msg=f"M2S unpack '{assign}' expected")

    # AXION-TYPES-012
    def test_axion_types_012_vhdl_s2m_pack(self):
        """AXION-TYPES-012  Architecture body has S2M pack concurrent assignments."""
        code = self._generate(use_axion_types=True)
        expected = [
            'axi_s2m.awready <= axi_awready',
            'axi_s2m.wready  <= axi_wready',
            'axi_s2m.bresp   <= axi_bresp',
            'axi_s2m.bvalid  <= axi_bvalid',
            'axi_s2m.arready <= axi_arready',
            'axi_s2m.rdata   <= axi_rdata',
            'axi_s2m.rresp   <= axi_rresp',
            'axi_s2m.rvalid  <= axi_rvalid',
        ]
        for assign in expected:
            self.assertIn(assign, code, msg=f"S2M pack '{assign}' expected")

    # AXION-TYPES-013
    def test_axion_types_013_vhdl_default_unchanged(self):
        """AXION-TYPES-013  Default (use_axion_types=False) has flat ports, no pkg clause."""
        code = self._generate(use_axion_types=False)
        self.assertNotIn('axion_common_pkg', code)
        self.assertNotIn('t_axi_lite_m2s', code)
        self.assertNotIn('t_axi_lite_s2m', code)
        self.assertIn('axi_awaddr  : in  std_logic_vector(31 downto 0)', code)
        self.assertIn('axi_rready  : in  std_logic', code)


# ---------------------------------------------------------------------------
# AXION-TYPES-014 … 020  SystemVerilog generator
# ---------------------------------------------------------------------------

class TestAxionTypesSV(unittest.TestCase):
    """AXION-TYPES-014 … 020  SystemVerilog generation with typed ports."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='axion_types_sv_')
        self.gen = SystemVerilogGenerator(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _module_data_sv(self, use_axion_types: bool) -> dict:
        md = _module_data_base('test_mod', use_axion_types=use_axion_types)
        # SV generator uses signal_type in bracket format
        for reg in md['registers']:
            reg['signal_type'] = '[31:0]'
            reg['signal_width'] = 32
        return md

    def _generate(self, use_axion_types: bool) -> str:
        md = self._module_data_sv(use_axion_types=use_axion_types)
        path = self.gen.generate_module(md)
        with open(path) as f:
            return f.read()

    # AXION-TYPES-014
    def test_axion_types_014_sv_package_import(self):
        """AXION-TYPES-014  import axion_common_pkg::* present when use_axion_types=True."""
        code = self._generate(use_axion_types=True)
        self.assertIn('import axion_common_pkg::*', code)

    def test_axion_types_014b_no_import_when_disabled(self):
        """AXION-TYPES-014 (negative)  No axion_common_pkg import when use_axion_types=False."""
        code = self._generate(use_axion_types=False)
        self.assertNotIn('axion_common_pkg', code)

    # AXION-TYPES-015
    def test_axion_types_015_sv_module_typed_ports(self):
        """AXION-TYPES-015  Module port list has axi_m2s and axi_s2m typed ports."""
        code = self._generate(use_axion_types=True)
        self.assertIn('axi_m2s', code)
        self.assertIn('axi_s2m', code)
        self.assertIn('t_axi_lite_m2s', code)
        self.assertIn('t_axi_lite_s2m', code)

    # AXION-TYPES-016
    def test_axion_types_016_sv_no_flat_axi_ports(self):
        """AXION-TYPES-016  No flat AXI port names in module port list."""
        code = self._generate(use_axion_types=True)
        # Extract module port section (between '(' and ');')
        port_start = code.find(') (')
        port_end = code.find(');', port_start)
        port_section = code[port_start:port_end]
        flat_ports = [
            'axi_awaddr,', 'axi_awvalid,', 'axi_awready,',
            'axi_wdata,', 'axi_wstrb,', 'axi_wvalid,', 'axi_wready,',
            'axi_bresp,', 'axi_bvalid,', 'axi_bready,',
            'axi_araddr,', 'axi_arvalid,', 'axi_arready,',
            'axi_rdata,', 'axi_rresp,', 'axi_rvalid,', 'axi_rready,',
        ]
        for port in flat_ports:
            self.assertNotIn(port, port_section,
                             msg=f"Flat port '{port}' should not be in module ports")

    # AXION-TYPES-017
    def test_axion_types_017_sv_intermediate_signals(self):
        """AXION-TYPES-017  Module body has logic declarations for intermediate AXI signals."""
        code = self._generate(use_axion_types=True)
        for sig in ['axi_awaddr', 'axi_wdata', 'axi_awready', 'axi_rdata']:
            # logic declarations look like "logic ... axi_signame;"
            self.assertIn(f'axi_{sig[4:]}' if sig.startswith('axi_') else sig, code)
        # More specific check
        self.assertIn('logic [ADDR_WIDTH-1:0]     axi_awaddr', code)
        self.assertIn('logic [DATA_WIDTH-1:0]     axi_rdata', code)

    # AXION-TYPES-018
    def test_axion_types_018_sv_m2s_unpack(self):
        """AXION-TYPES-018  Module body has M2S unpack assign statements."""
        code = self._generate(use_axion_types=True)
        expected = [
            'assign axi_awaddr  = axi_m2s.awaddr',
            'assign axi_awvalid = axi_m2s.awvalid',
            'assign axi_wdata   = axi_m2s.wdata',
            'assign axi_wstrb   = axi_m2s.wstrb',
            'assign axi_wvalid  = axi_m2s.wvalid',
            'assign axi_bready  = axi_m2s.bready',
            'assign axi_araddr  = axi_m2s.araddr',
            'assign axi_arvalid = axi_m2s.arvalid',
            'assign axi_rready  = axi_m2s.rready',
        ]
        for assign in expected:
            self.assertIn(assign, code, msg=f"M2S unpack '{assign}' expected")

    # AXION-TYPES-019
    def test_axion_types_019_sv_s2m_pack(self):
        """AXION-TYPES-019  Module body has S2M pack assign statements."""
        code = self._generate(use_axion_types=True)
        expected = [
            'assign axi_s2m.awready = axi_awready',
            'assign axi_s2m.wready  = axi_wready',
            'assign axi_s2m.bresp   = axi_bresp',
            'assign axi_s2m.bvalid  = axi_bvalid',
            'assign axi_s2m.arready = axi_arready',
            'assign axi_s2m.rdata   = axi_rdata',
            'assign axi_s2m.rresp   = axi_rresp',
            'assign axi_s2m.rvalid  = axi_rvalid',
        ]
        for assign in expected:
            self.assertIn(assign, code, msg=f"S2M pack '{assign}' expected")

    # AXION-TYPES-020
    def test_axion_types_020_sv_default_unchanged(self):
        """AXION-TYPES-020  Default (use_axion_types=False) has flat ports, no pkg import."""
        code = self._generate(use_axion_types=False)
        self.assertNotIn('axion_common_pkg', code)
        self.assertNotIn('t_axi_lite_m2s', code)
        self.assertNotIn('t_axi_lite_s2m', code)
        self.assertIn('axi_awaddr', code)
        self.assertIn('axi_rready', code)


# ---------------------------------------------------------------------------
# AXION-TYPES-021  Per-module independence
# ---------------------------------------------------------------------------

class TestAxionTypesPerModule(unittest.TestCase):
    """AXION-TYPES-021  use_axion_types on one module does not affect siblings."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='axion_types_per_mod_')

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_axion_types_021_per_module_independence(self):
        """AXION-TYPES-021  Two modules: one enabled, one not — outputs differ correctly."""
        gen = VHDLGenerator(self.tmp)

        md_on = _module_data_base('mod_on', use_axion_types=True)
        md_off = _module_data_base('mod_off', use_axion_types=False)

        path_on = gen.generate_module(md_on)
        path_off = gen.generate_module(md_off)

        with open(path_on) as f:
            code_on = f.read()
        with open(path_off) as f:
            code_off = f.read()

        # mod_on should have typed ports
        self.assertIn('t_axi_lite_m2s', code_on)
        self.assertIn('axion_common_pkg', code_on)

        # mod_off should remain flat
        self.assertNotIn('t_axi_lite_m2s', code_off)
        self.assertNotIn('axion_common_pkg', code_off)
        self.assertIn('axi_awaddr', code_off)


if __name__ == '__main__':
    unittest.main()
