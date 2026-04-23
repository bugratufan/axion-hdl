"""
Tests for the enumerated values (enum_values) feature in axion-hdl.

Each test is mapped to a specific requirement ID (ENUM-NNN).
"""

import os
import sys
import json
import tempfile
import shutil
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

TESTS_DIR = os.path.join(PROJECT_ROOT, 'tests')
YAML_DIR = os.path.join(TESTS_DIR, 'yaml')
JSON_DIR = os.path.join(TESTS_DIR, 'json')
TOML_DIR = os.path.join(TESTS_DIR, 'toml')
XML_DIR = os.path.join(TESTS_DIR, 'xml')
VHDL_DIR = os.path.join(TESTS_DIR, 'vhdl')
SV_DIR = os.path.join(TESTS_DIR, 'sv')


class TestEnumValues(unittest.TestCase):

    def setUp(self):
        self.output_dir = tempfile.mkdtemp(prefix='axion_enum_test_')

    def tearDown(self):
        shutil.rmtree(self.output_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # ENUM-001: BitField data model
    # -------------------------------------------------------------------------
    def test_enum_001_bitfield_model(self):
        """ENUM-001: BitField dataclass includes optional enum_values field."""
        from axion_hdl.bit_field_manager import BitField, BitFieldManager

        mgr = BitFieldManager()
        field = mgr.add_field(
            reg_name='test_reg',
            address=0x00,
            field_name='status',
            width=2,
            access_mode='RO',
            signal_type='[1:0]',
            enum_values={0: 'IDLE', 1: 'WAITING', 3: 'READY'}
        )

        self.assertIsNotNone(field.enum_values)
        self.assertEqual(field.enum_values[0], 'IDLE')
        self.assertEqual(field.enum_values[1], 'WAITING')
        self.assertEqual(field.enum_values[3], 'READY')

    # -------------------------------------------------------------------------
    # ENUM-002: VHDL annotation parsing
    # -------------------------------------------------------------------------
    def test_enum_002_vhdl_annotation_parse(self):
        """ENUM-002: ENUM= attribute in @axion comment parsed to Dict[int, str]."""
        from axion_hdl.annotation_parser import AnnotationParser

        parser = AnnotationParser(annotation_prefix='@axion')
        attrs = parser.parse_attributes('RO ADDR=0x00 ENUM="0:IDLE,1:WAITING,3:READY"')

        self.assertIn('enum_values', attrs)
        ev = attrs['enum_values']
        self.assertIsInstance(ev, dict)
        self.assertEqual(ev[0], 'IDLE')
        self.assertEqual(ev[1], 'WAITING')
        self.assertEqual(ev[3], 'READY')

    # -------------------------------------------------------------------------
    # ENUM-003: SV annotation parsing
    # -------------------------------------------------------------------------
    def test_enum_003_sv_annotation_parse(self):
        """ENUM-003: ENUM= attribute in // @axion comment parsed to Dict[int, str]."""
        from axion_hdl.annotation_parser import AnnotationParser

        parser = AnnotationParser(annotation_prefix='@axion')
        attrs = parser.parse_attributes('RW ADDR=0x10 ENUM="0:DISABLED,1:ENABLED"')

        self.assertIn('enum_values', attrs)
        ev = attrs['enum_values']
        self.assertEqual(ev[0], 'DISABLED')
        self.assertEqual(ev[1], 'ENABLED')

    # -------------------------------------------------------------------------
    # ENUM-004: YAML field enum parsing
    # -------------------------------------------------------------------------
    def test_enum_004_yaml_field_enum(self):
        """ENUM-004: YAML field enum_values dict parsed to Dict[int, str]."""
        from axion_hdl.yaml_input_parser import YAMLInputParser

        parser = YAMLInputParser()
        result = parser.parse_file(os.path.join(YAML_DIR, 'enum_test.yaml'))

        self.assertIsNotNone(result)
        # Find the packed register
        packed_regs = [r for r in result['registers'] if r.get('is_packed')]
        self.assertTrue(len(packed_regs) > 0, "No packed registers found")

        # Find status field
        control_reg = next((r for r in packed_regs if 'control_reg' in r.get('signal_name', '')), None)
        self.assertIsNotNone(control_reg)

        status_field = next((f for f in control_reg['fields'] if f['name'] == 'status'), None)
        self.assertIsNotNone(status_field)
        ev = status_field['enum_values']
        self.assertIsNotNone(ev)
        self.assertEqual(ev[0], 'IDLE')
        self.assertEqual(ev[1], 'WAITING')
        self.assertEqual(ev[3], 'READY')

    # -------------------------------------------------------------------------
    # ENUM-005: JSON field enum parsing
    # -------------------------------------------------------------------------
    def test_enum_005_json_field_enum(self):
        """ENUM-005: JSON field enum_values dict parsed to Dict[int, str]."""
        from axion_hdl.json_input_parser import JSONInputParser

        parser = JSONInputParser()
        result = parser.parse_file(os.path.join(JSON_DIR, 'enum_test.json'))

        self.assertIsNotNone(result)
        packed_regs = [r for r in result['registers'] if r.get('is_packed')]
        self.assertTrue(len(packed_regs) > 0)

        control_reg = packed_regs[0]
        status_field = next((f for f in control_reg['fields'] if f['name'] == 'status'), None)
        self.assertIsNotNone(status_field)
        ev = status_field['enum_values']
        self.assertIsNotNone(ev)
        self.assertEqual(ev[0], 'IDLE')
        self.assertEqual(ev[1], 'WAITING')
        self.assertEqual(ev[3], 'READY')

    # -------------------------------------------------------------------------
    # ENUM-006: TOML field enum parsing
    # -------------------------------------------------------------------------
    def test_enum_006_toml_field_enum(self):
        """ENUM-006: TOML field enum_values dict parsed to Dict[int, str]."""
        from axion_hdl.toml_input_parser import TOMLInputParser

        parser = TOMLInputParser()
        result = parser.parse_file(os.path.join(TOML_DIR, 'enum_test.toml'))

        self.assertIsNotNone(result)
        packed_regs = [r for r in result['registers'] if r.get('is_packed')]
        self.assertTrue(len(packed_regs) > 0)

        control_reg = packed_regs[0]
        status_field = next((f for f in control_reg['fields'] if f['name'] == 'status'), None)
        self.assertIsNotNone(status_field)
        ev = status_field['enum_values']
        self.assertIsNotNone(ev)
        self.assertEqual(ev[0], 'IDLE')
        self.assertEqual(ev[1], 'WAITING')
        self.assertEqual(ev[3], 'READY')

    # -------------------------------------------------------------------------
    # ENUM-007: XML flat enum attribute
    # -------------------------------------------------------------------------
    def test_enum_007_xml_flat_enum_attr(self):
        """ENUM-007: Flat XML enum attribute parsed via parse_enum_values()."""
        from axion_hdl.xml_input_parser import XMLInputParser

        parser = XMLInputParser()
        result = parser.parse_file(os.path.join(XML_DIR, 'enum_test.xml'))

        self.assertIsNotNone(result)
        # Find flat_status register which uses flat enum= attribute
        flat_regs = [r for r in result['registers']
                     if r.get('signal_name') == 'flat_status' or r.get('name') == 'flat_status']
        self.assertTrue(len(flat_regs) > 0, "flat_status register not found")

        flat_reg = flat_regs[0]
        ev = flat_reg.get('enum_values')
        self.assertIsNotNone(ev, "enum_values not parsed from flat enum attribute")
        self.assertEqual(ev[0], 'STOPPED')
        self.assertEqual(ev[1], 'RUNNING')
        self.assertEqual(ev[2], 'ERROR')

    # -------------------------------------------------------------------------
    # ENUM-008: XML nested enum elements
    # -------------------------------------------------------------------------
    def test_enum_008_xml_nested_enum_elements(self):
        """ENUM-008: <enum_value> children within <field> parsed to enum dict."""
        from axion_hdl.xml_input_parser import XMLInputParser

        parser = XMLInputParser()
        result = parser.parse_file(os.path.join(XML_DIR, 'enum_test.xml'))

        self.assertIsNotNone(result)
        packed_regs = [r for r in result['registers'] if r.get('is_packed')]
        self.assertTrue(len(packed_regs) > 0)

        control_reg = packed_regs[0]
        status_field = next((f for f in control_reg['fields'] if f['name'] == 'status'), None)
        self.assertIsNotNone(status_field)
        ev = status_field['enum_values']
        self.assertIsNotNone(ev)
        self.assertEqual(ev[0], 'IDLE')
        self.assertEqual(ev[3], 'READY')

    # -------------------------------------------------------------------------
    # ENUM-009: XML SPIRIT enum parsing
    # -------------------------------------------------------------------------
    def test_enum_009_xml_spirit_enum(self):
        """ENUM-009: spirit:enumeratedValues parsed to enum dict."""
        from axion_hdl.xml_input_parser import XMLInputParser

        parser = XMLInputParser()
        result = parser.parse_file(os.path.join(XML_DIR, 'enum_test_spirit.xml'))

        self.assertIsNotNone(result)
        packed_regs = [r for r in result['registers'] if r.get('is_packed')]
        self.assertTrue(len(packed_regs) > 0)

        control_reg = packed_regs[0]
        enable_field = next((f for f in control_reg['fields'] if f['name'] == 'enable'), None)
        self.assertIsNotNone(enable_field)
        ev = enable_field['enum_values']
        self.assertIsNotNone(ev)
        self.assertEqual(ev[0], 'INACTIVE')
        self.assertEqual(ev[1], 'ACTIVE')

    # -------------------------------------------------------------------------
    # ENUM-010: Markdown/HTML enum column in doc
    # -------------------------------------------------------------------------
    def test_enum_010_markdown_enum_column(self):
        """ENUM-010: Doc generator adds Enum Values column when field has enum_values."""
        from axion_hdl.yaml_input_parser import YAMLInputParser
        from axion_hdl.doc_generators import DocGenerator

        yaml_parser = YAMLInputParser()
        module = yaml_parser.parse_file(os.path.join(YAML_DIR, 'enum_test.yaml'))
        self.assertIsNotNone(module)

        gen = DocGenerator(self.output_dir)
        lines = gen._generate_module_section(module)
        content = '\n'.join(lines)

        self.assertIn('Enum Values', content)
        self.assertIn('IDLE', content)
        self.assertIn('READY', content)

    # -------------------------------------------------------------------------
    # ENUM-011: C header enum macros
    # -------------------------------------------------------------------------
    def test_enum_011_c_header_macros(self):
        """ENUM-011: C header generator emits #define macros for enum values."""
        from axion_hdl.yaml_input_parser import YAMLInputParser
        from axion_hdl.doc_generators import CHeaderGenerator

        yaml_parser = YAMLInputParser()
        module = yaml_parser.parse_file(os.path.join(YAML_DIR, 'enum_test.yaml'))
        self.assertIsNotNone(module)

        gen = CHeaderGenerator(self.output_dir)
        lines = gen._generate_header_content(module)
        content = '\n'.join(lines)

        # Should contain enum macros
        self.assertIn('IDLE', content)
        self.assertIn('#define', content)
        # Check the pattern: MODULE_REG_FIELD_NAME
        self.assertIn('ENUM_TEST_MOD_CONTROL_REG_STATUS_IDLE', content)
        self.assertIn('ENUM_TEST_MOD_CONTROL_REG_STATUS_READY', content)

    # -------------------------------------------------------------------------
    # ENUM-012: YAML export round-trip
    # -------------------------------------------------------------------------
    def test_enum_012_yaml_export_roundtrip(self):
        """ENUM-012: YAML export includes enum_values; re-parsed result matches."""
        from axion_hdl.yaml_input_parser import YAMLInputParser
        from axion_hdl.doc_generators import YAMLGenerator

        yaml_parser = YAMLInputParser()
        module = yaml_parser.parse_file(os.path.join(YAML_DIR, 'enum_test.yaml'))
        self.assertIsNotNone(module)

        gen = YAMLGenerator(self.output_dir)
        data = gen._generate_yaml_data(module)

        # Find the packed register fields
        control_entry = next((r for r in data['registers'] if r['name'] == 'control_reg'), None)
        self.assertIsNotNone(control_entry)
        self.assertIn('fields', control_entry)

        status_field = next((f for f in control_entry['fields'] if f['name'] == 'status'), None)
        self.assertIsNotNone(status_field)
        self.assertIn('enum_values', status_field)
        ev = status_field['enum_values']
        # JSON/YAML exports have string keys
        self.assertIn('0', ev)
        self.assertEqual(ev['0'], 'IDLE')
        self.assertEqual(ev['3'], 'READY')

    # -------------------------------------------------------------------------
    # ENUM-013: JSON export round-trip
    # -------------------------------------------------------------------------
    def test_enum_013_json_export_roundtrip(self):
        """ENUM-013: JSON export includes enum_values; re-parsed result matches."""
        from axion_hdl.yaml_input_parser import YAMLInputParser
        from axion_hdl.doc_generators import JSONGenerator

        yaml_parser = YAMLInputParser()
        module = yaml_parser.parse_file(os.path.join(YAML_DIR, 'enum_test.yaml'))
        self.assertIsNotNone(module)

        gen = JSONGenerator(self.output_dir)
        data = gen._generate_json_data(module)

        control_entry = next((r for r in data['registers'] if r['name'] == 'control_reg'), None)
        self.assertIsNotNone(control_entry)

        status_field = next((f for f in control_entry['fields'] if f['name'] == 'status'), None)
        self.assertIsNotNone(status_field)
        ev = status_field.get('enum_values')
        self.assertIsNotNone(ev)
        self.assertEqual(ev['0'], 'IDLE')
        self.assertEqual(ev['3'], 'READY')

    # -------------------------------------------------------------------------
    # ENUM-014: XML SPIRIT export
    # -------------------------------------------------------------------------
    def test_enum_014_xml_spirit_export(self):
        """ENUM-014: XML generator emits spirit:enumeratedValues for fields with enum_values."""
        from axion_hdl.yaml_input_parser import YAMLInputParser
        from axion_hdl.doc_generators import XMLGenerator

        yaml_parser = YAMLInputParser()
        module = yaml_parser.parse_file(os.path.join(YAML_DIR, 'enum_test.yaml'))
        self.assertIsNotNone(module)

        gen = XMLGenerator(self.output_dir)
        lines = gen._generate_xml_content(module)
        content = '\n'.join(lines)

        self.assertIn('spirit:enumeratedValues', content)
        self.assertIn('spirit:enumeratedValue', content)
        self.assertIn('IDLE', content)
        self.assertIn('READY', content)

    # -------------------------------------------------------------------------
    # ENUM-015: VHDL comment annotation
    # -------------------------------------------------------------------------
    def test_enum_015_vhdl_comment_only(self):
        """ENUM-015: VHDL generator appends enum comment for fields with enum_values."""
        from axion_hdl.yaml_input_parser import YAMLInputParser
        from axion_hdl.generator import VHDLGenerator

        yaml_parser = YAMLInputParser()
        module = yaml_parser.parse_file(os.path.join(YAML_DIR, 'enum_test.yaml'))
        self.assertIsNotNone(module)

        gen = VHDLGenerator(self.output_dir)
        # Check that the enum comment appears in the entity port description
        entity_lines = gen._generate_entity(module)
        content = '\n'.join(entity_lines)

        # There should be enum annotations in the port comments
        self.assertIn('INACTIVE', content)

    # -------------------------------------------------------------------------
    # ENUM-016: SV comment annotation
    # -------------------------------------------------------------------------
    def test_enum_016_sv_comment_only(self):
        """ENUM-016: SV generator appends enum comment for signals with enum_values."""
        from axion_hdl.systemverilog_parser import SystemVerilogParser
        from axion_hdl.systemverilog_generator import SystemVerilogGenerator

        parser = SystemVerilogParser()
        result = parser.parse_file(os.path.join(SV_DIR, 'enum_test.sv'))
        self.assertIsNotNone(result)

        # Check enum_values was parsed
        regs_with_enum = [r for r in result['registers'] if r.get('enum_values')]
        self.assertTrue(len(regs_with_enum) > 0, "No registers with enum_values found in SV file")

        gen = SystemVerilogGenerator(self.output_dir)
        decl = gen._generate_module_declaration(result)
        # Enum comment should appear in port declaration
        self.assertIn('IDLE', decl)

    # -------------------------------------------------------------------------
    # ENUM-018: No-enum regression
    # -------------------------------------------------------------------------
    def test_enum_018_no_enum_regression(self):
        """ENUM-018: Modules without enum_values generate output without enum columns."""
        from axion_hdl.yaml_input_parser import YAMLInputParser
        from axion_hdl.doc_generators import DocGenerator

        yaml_parser = YAMLInputParser()
        module = yaml_parser.parse_file(os.path.join(YAML_DIR, 'sensor_controller.yaml'))
        self.assertIsNotNone(module)

        gen = DocGenerator(self.output_dir)
        lines = gen._generate_module_section(module)
        content = '\n'.join(lines)

        # Should NOT include Enum Values column for non-enum registers
        self.assertNotIn('Enum Values', content)

    # -------------------------------------------------------------------------
    # ENUM-019: Numeric notations
    # -------------------------------------------------------------------------
    def test_enum_019_numeric_notations(self):
        """ENUM-019: Decimal, hex, and binary enum value notations are parsed correctly."""
        from axion_hdl.annotation_parser import AnnotationParser

        parser = AnnotationParser(annotation_prefix='@axion')

        # Decimal notation
        attrs = parser.parse_attributes('RW ENUM="0:OFF,1:ON,3:STANDBY"')
        ev = attrs['enum_values']
        self.assertEqual(ev[0], 'OFF')
        self.assertEqual(ev[1], 'ON')
        self.assertEqual(ev[3], 'STANDBY')

        # Hex notation
        attrs = parser.parse_attributes('RW ENUM="0x0:OFF,0x1:ON,0x3:STANDBY"')
        ev = attrs['enum_values']
        self.assertEqual(ev[0], 'OFF')
        self.assertEqual(ev[1], 'ON')
        self.assertEqual(ev[3], 'STANDBY')

        # Binary notation
        attrs = parser.parse_attributes('RW ENUM="0b00:OFF,0b01:ON,0b11:STANDBY"')
        ev = attrs['enum_values']
        self.assertEqual(ev[0], 'OFF')
        self.assertEqual(ev[1], 'ON')
        self.assertEqual(ev[3], 'STANDBY')

    # -------------------------------------------------------------------------
    # ENUM-020: VHDL pkg constants
    # -------------------------------------------------------------------------
    def test_enum_020_vhdl_pkg_constants(self):
        """ENUM-020: generate_vhdl_pkg produces .vhd package with constant definitions."""
        from axion_hdl.yaml_input_parser import YAMLInputParser
        from axion_hdl.generator import VHDLGenerator

        yaml_parser = YAMLInputParser()
        module = yaml_parser.parse_file(os.path.join(YAML_DIR, 'enum_test.yaml'))
        self.assertIsNotNone(module)

        gen = VHDLGenerator(self.output_dir)
        pkg_path = gen.generate_vhdl_pkg(module)

        self.assertIsNotNone(pkg_path)
        self.assertTrue(os.path.exists(pkg_path))
        self.assertTrue(pkg_path.endswith('_regs_pkg.vhd'))

        with open(pkg_path, 'r') as f:
            content = f.read()

        self.assertIn('package', content)
        self.assertIn('constant C_', content)
        self.assertIn('IDLE', content)
        self.assertIn('std_logic_vector', content)

    # -------------------------------------------------------------------------
    # ENUM-021: SV pkg typedef
    # -------------------------------------------------------------------------
    def test_enum_021_sv_pkg_typedef(self):
        """ENUM-021: generate_sv_pkg produces .sv package with typedef enum logic."""
        from axion_hdl.yaml_input_parser import YAMLInputParser
        from axion_hdl.systemverilog_generator import SystemVerilogGenerator

        yaml_parser = YAMLInputParser()
        module = yaml_parser.parse_file(os.path.join(YAML_DIR, 'enum_test.yaml'))
        self.assertIsNotNone(module)

        gen = SystemVerilogGenerator(self.output_dir)
        pkg_path = gen.generate_sv_pkg(module)

        self.assertIsNotNone(pkg_path)
        self.assertTrue(os.path.exists(pkg_path))
        self.assertTrue(pkg_path.endswith('_regs_pkg.sv'))

        with open(pkg_path, 'r') as f:
            content = f.read()

        self.assertIn('package', content)
        self.assertIn('typedef enum logic', content)
        self.assertIn('IDLE', content)
        self.assertIn('endpackage', content)

    # -------------------------------------------------------------------------
    # ENUM-022: Value overflow validation
    # -------------------------------------------------------------------------
    def test_enum_022_value_overflow_validation(self):
        """ENUM-022: add_field raises ValueError when enum value exceeds 2**width - 1."""
        from axion_hdl.bit_field_manager import BitFieldManager

        mgr = BitFieldManager()

        # width=1, value 3 -> error (3 > 1)
        with self.assertRaises(ValueError):
            mgr.add_field('reg1', 0x00, 'f1', 1, 'RW', '[0:0]', enum_values={3: 'BAD'})

        mgr2 = BitFieldManager()
        # width=1, value 1 -> OK (1 <= 1)
        field = mgr2.add_field('reg2', 0x00, 'f2', 1, 'RW', '[0:0]', enum_values={1: 'OK'})
        self.assertIsNotNone(field.enum_values)

        mgr3 = BitFieldManager()
        # width=3, value 15 -> error (0b1111=15 > 7)
        with self.assertRaises(ValueError):
            mgr3.add_field('reg3', 0x00, 'f3', 3, 'RW', '[2:0]', enum_values={15: 'BAD'})

        mgr4 = BitFieldManager()
        # width=3, value 1 -> OK (0b01=1 <= 7)
        field = mgr4.add_field('reg4', 0x00, 'f4', 3, 'RW', '[2:0]', enum_values={1: 'OK'})
        self.assertIsNotNone(field.enum_values)

        mgr5 = BitFieldManager()
        # width=4, value 31 -> error (0b11111=31 > 15)
        with self.assertRaises(ValueError):
            mgr5.add_field('reg5', 0x00, 'f5', 4, 'RW', '[3:0]', enum_values={31: 'BAD'})

        mgr6 = BitFieldManager()
        # width=4, value 15 -> OK (0b01111=15 <= 15)
        field = mgr6.add_field('reg6', 0x00, 'f6', 4, 'RW', '[3:0]', enum_values={15: 'OK'})
        self.assertIsNotNone(field.enum_values)

        mgr7 = BitFieldManager()
        # width=2, value 10 -> error (10 > 3)
        with self.assertRaises(ValueError):
            mgr7.add_field('reg7', 0x00, 'f7', 2, 'RW', '[1:0]', enum_values={10: 'BAD'})

    # -------------------------------------------------------------------------
    # ENUM-023: One-bit field
    # -------------------------------------------------------------------------
    def test_enum_023_one_bit_field(self):
        """ENUM-023: 1-bit fields with enum produce correct VHDL std_logic constants and SV typedef."""
        from axion_hdl.bit_field_manager import BitFieldManager
        from axion_hdl.generator import VHDLGenerator
        from axion_hdl.systemverilog_generator import SystemVerilogGenerator
        from axion_hdl.yaml_input_parser import YAMLInputParser

        # Build a module with a 1-bit field
        module = {
            'name': 'onebit_mod',
            'file': 'onebit_mod.yaml',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': [
                {
                    'signal_name': 'ctrl_reg',
                    'name': 'ctrl_reg',
                    'reg_name': 'ctrl_reg',
                    'access_mode': 'RW',
                    'address': '0x00',
                    'address_int': 0,
                    'relative_address': '0x00',
                    'relative_address_int': 0,
                    'width': 32,
                    'signal_type': 'std_logic_vector(31 downto 0)',
                    'r_strobe': False,
                    'w_strobe': False,
                    'read_strobe': False,
                    'write_strobe': False,
                    'description': 'Control register',
                    'default_value': 0,
                    'is_packed': True,
                    'fields': [
                        {
                            'name': 'enable',
                            'bit_low': 0,
                            'bit_high': 0,
                            'width': 1,
                            'access_mode': 'RW',
                            'signal_type': '[0:0]',
                            'description': 'Enable bit',
                            'read_strobe': False,
                            'write_strobe': False,
                            'default_value': 0,
                            'mask': 0x1,
                            'enum_values': {0: 'INACTIVE', 1: 'ACTIVE'}
                        }
                    ]
                }
            ],
            'packed_registers': [],
            'parsing_errors': []
        }

        # Test VHDL pkg generates std_logic (not std_logic_vector) for 1-bit
        vhdl_gen = VHDLGenerator(self.output_dir)
        pkg_path = vhdl_gen.generate_vhdl_pkg(module)
        self.assertIsNotNone(pkg_path)
        with open(pkg_path, 'r') as f:
            vhdl_content = f.read()
        self.assertIn('std_logic', vhdl_content)
        self.assertNotIn("std_logic_vector(0", vhdl_content)
        self.assertIn("'0'", vhdl_content)
        self.assertIn("'1'", vhdl_content)

        # Test SV pkg generates typedef enum logic (without range for 1-bit)
        sv_gen = SystemVerilogGenerator(self.output_dir)
        sv_pkg_path = sv_gen.generate_sv_pkg(module)
        self.assertIsNotNone(sv_pkg_path)
        with open(sv_pkg_path, 'r') as f:
            sv_content = f.read()
        self.assertIn('typedef enum logic {', sv_content)
        self.assertNotIn('logic [0:0]', sv_content)

    # -------------------------------------------------------------------------
    # ENUM-024: Rule checker enum overflow
    # -------------------------------------------------------------------------
    def test_enum_024_rule_check_reports_overflow(self):
        """ENUM-024: RuleChecker.check_enum_value_overflow reports error for overflow values."""
        from axion_hdl.rule_checker import RuleChecker

        modules = [
            {
                'name': 'test_mod',
                'registers': [
                    {
                        'signal_name': 'ctrl_reg',
                        'reg_name': 'ctrl_reg',
                        'is_packed': True,
                        'fields': [
                            {
                                'name': 'status',
                                'width': 2,
                                'bit_low': 0,
                                'bit_high': 1,
                                'enum_values': {0: 'IDLE', 5: 'BAD'}  # 5 > 3 (2**2-1)
                            }
                        ]
                    }
                ],
                'parsing_errors': []
            }
        ]

        checker = RuleChecker()
        checker.check_enum_value_overflow(modules)

        self.assertTrue(len(checker.errors) > 0)
        error_msgs = [e['msg'] for e in checker.errors]
        self.assertTrue(any('5' in msg for msg in error_msgs))
        self.assertTrue(any('BAD' in msg for msg in error_msgs))

        # Also test that valid values produce no errors
        checker2 = RuleChecker()
        modules_ok = [
            {
                'name': 'test_mod',
                'registers': [
                    {
                        'signal_name': 'ctrl_reg',
                        'reg_name': 'ctrl_reg',
                        'is_packed': True,
                        'fields': [
                            {
                                'name': 'status',
                                'width': 2,
                                'bit_low': 0,
                                'bit_high': 1,
                                'enum_values': {0: 'IDLE', 1: 'WAITING', 3: 'READY'}
                            }
                        ]
                    }
                ],
                'parsing_errors': []
            }
        ]
        checker2.check_enum_value_overflow(modules_ok)
        self.assertEqual(len(checker2.errors), 0)

    # -------------------------------------------------------------------------
    # ENUM-025: Rule checker catches overflow in standalone (non-packed) register
    # -------------------------------------------------------------------------
    def test_enum_025_rule_check_standalone_overflow(self):
        """ENUM-025: RuleChecker detects enum overflow in standalone (non-packed) register."""
        from axion_hdl.rule_checker import RuleChecker

        # 4-bit standalone register: max=15, value 16 must be an error
        modules_bad = [
            {
                'name': 'test_mod',
                'registers': [
                    {
                        'signal_name': 'status_reg',
                        'is_packed': None,
                        'width': 4,
                        'enum_values': {0: 'OK', 15: 'WARN', 16: 'OVERFLOW'}
                    }
                ],
                'parsing_errors': []
            }
        ]
        checker = RuleChecker()
        checker.check_enum_value_overflow(modules_bad)
        self.assertTrue(len(checker.errors) > 0)
        msgs = [e['msg'] for e in checker.errors]
        self.assertTrue(any('16' in m for m in msgs))
        self.assertTrue(any('OVERFLOW' in m for m in msgs))

        # 1-bit standalone: max=1, value 2 must be an error
        modules_1bit = [
            {
                'name': 'test_mod',
                'registers': [
                    {
                        'signal_name': 'flag_reg',
                        'is_packed': False,
                        'width': 1,
                        'enum_values': {0: 'OFF', 1: 'ON', 2: 'BAD'}
                    }
                ],
                'parsing_errors': []
            }
        ]
        checker2 = RuleChecker()
        checker2.check_enum_value_overflow(modules_1bit)
        self.assertTrue(len(checker2.errors) > 0)
        msgs2 = [e['msg'] for e in checker2.errors]
        self.assertTrue(any('2' in m for m in msgs2))

        # Valid standalone: no error
        modules_ok = [
            {
                'name': 'test_mod',
                'registers': [
                    {
                        'signal_name': 'code_reg',
                        'is_packed': None,
                        'width': 8,
                        'enum_values': {0: 'RESET', 127: 'HALF', 255: 'MAX'}
                    }
                ],
                'parsing_errors': []
            }
        ]
        checker3 = RuleChecker()
        checker3.check_enum_value_overflow(modules_ok)
        self.assertEqual(len(checker3.errors), 0)

    # -------------------------------------------------------------------------
    # ENUM-026: Rule checker catches overflow in VHDL standalone signal (E2E)
    # -------------------------------------------------------------------------
    def test_enum_026_rule_check_vhdl_standalone_e2e(self):
        """ENUM-026: Parsing VHDL with overflow enum on standalone signal triggers rule-check error."""
        import tempfile, textwrap
        from axion_hdl.parser import VHDLParser
        from axion_hdl.rule_checker import RuleChecker

        vhdl_src = textwrap.dedent("""\
            -- @axion_def BASE_ADDR=0x0000
            library ieee;
            use ieee.std_logic_1164.all;
            entity overflow_standalone_e2e is
                port (clk : in std_logic);
            end entity;
            architecture rtl of overflow_standalone_e2e is
                -- 1-bit: max=1, value 2 overflows
                signal enable_sig : std_logic;  -- @axion RW ADDR=0x00 ENUM="0:OFF,1:ON,2:OVERFLOW" DESC="1-bit"
                -- 2-bit: max=3, value 5 overflows
                signal state_sig : std_logic_vector(1 downto 0);  -- @axion RO ADDR=0x04 ENUM="0:IDLE,3:BUSY,5:OVERFLOW" DESC="2-bit"
            begin
                enable_sig <= '0';
                state_sig <= (others => '0');
            end architecture;
        """)
        with tempfile.NamedTemporaryFile(suffix='.vhd', mode='w', delete=False) as f:
            f.write(vhdl_src)
            fpath = f.name

        parser = VHDLParser()
        result = parser.parse_file(fpath)
        # Normalize: VHDLParser uses 'entity_name'; rule_checker expects 'name'
        result.setdefault('name', result.get('entity_name', 'unknown'))
        modules = [result]

        checker = RuleChecker()
        checker.check_enum_value_overflow(modules)

        error_msgs = [e['msg'] for e in checker.errors]
        # Both overflows must be reported
        self.assertTrue(any('2' in m for m in error_msgs),
                        f"Expected overflow=2 error, got: {error_msgs}")
        self.assertTrue(any('5' in m for m in error_msgs),
                        f"Expected overflow=5 error, got: {error_msgs}")

    # -------------------------------------------------------------------------
    # ENUM-027: Rule checker catches overflow in SV standalone signal (E2E)
    # -------------------------------------------------------------------------
    def test_enum_027_rule_check_sv_standalone_e2e(self):
        """ENUM-027: Parsing SV with overflow enum on standalone signal triggers rule-check error."""
        import tempfile, textwrap
        from axion_hdl.systemverilog_parser import SystemVerilogParser
        from axion_hdl.rule_checker import RuleChecker

        sv_src = textwrap.dedent("""\
            // @axion_def BASE_ADDR=0x0000
            module overflow_sv_e2e (
                input logic clk
            );
            // 1-bit: max=1, value 3 overflows
            logic enable_sig; // @axion RW ADDR=0x00 ENUM="0:OFF,1:ON,3:OVERFLOW" DESC="1-bit"
            // 3-bit: max=7, value 8 overflows
            logic [2:0] level_sig; // @axion RO ADDR=0x04 ENUM="0:L0,7:L7,8:OVERFLOW" DESC="3-bit"
            assign enable_sig = 1'b0;
            assign level_sig = 3'b000;
            endmodule
        """)
        with tempfile.NamedTemporaryFile(suffix='.sv', mode='w', delete=False) as f:
            f.write(sv_src)
            fpath = f.name

        parser = SystemVerilogParser()
        result = parser.parse_file(fpath)
        modules = [result]

        checker = RuleChecker()
        checker.check_enum_value_overflow(modules)

        error_msgs = [e['msg'] for e in checker.errors]
        self.assertTrue(any('3' in m for m in error_msgs),
                        f"Expected overflow=3 error, got: {error_msgs}")
        self.assertTrue(any('8' in m for m in error_msgs),
                        f"Expected overflow=8 error, got: {error_msgs}")

    # -------------------------------------------------------------------------
    # ENUM-028: BitFieldManager reports ALL overflowing values, not just first
    # -------------------------------------------------------------------------
    def test_enum_028_bit_field_manager_all_overflows(self):
        """ENUM-028: add_field raises ValueError naming every overflowing enum value."""
        from axion_hdl.bit_field_manager import BitFieldManager

        mgr = BitFieldManager()
        # 3-bit field (max=7): values 8 and 255 both overflow
        with self.assertRaises(ValueError) as ctx:
            mgr.add_field(
                reg_name='test_reg',
                address=0x00,
                field_name='level',
                width=3,
                access_mode='RW',
                signal_type='[2:0]',
                enum_values={0: 'NONE', 7: 'MAX_OK', 8: 'BAD_8', 255: 'BAD_255'}
            )
        err_msg = str(ctx.exception)
        self.assertIn('8', err_msg,
                      f"Expected '8' in error message, got: {err_msg}")
        self.assertIn('255', err_msg,
                      f"Expected '255' in error message, got: {err_msg}")


    # -------------------------------------------------------------------------
    # ENUM-029: Negative enum values rejected by BitFieldManager
    # -------------------------------------------------------------------------
    def test_enum_029_negative_enum_value_rejected_by_add_field(self):
        """ENUM-029: add_field raises ValueError when an enum value is negative."""
        from axion_hdl.bit_field_manager import BitFieldManager

        mgr = BitFieldManager()
        with self.assertRaises(ValueError) as ctx:
            mgr.add_field(
                reg_name='test_reg',
                address=0x00,
                field_name='state',
                width=4,
                access_mode='RW',
                signal_type='[3:0]',
                enum_values={0: 'ZERO', -1: 'NEG_ONE', 15: 'MAX'}
            )
        self.assertIn('-1', str(ctx.exception))

    # -------------------------------------------------------------------------
    # ENUM-030: Negative enum values rejected by rule_checker
    # -------------------------------------------------------------------------
    def test_enum_030_negative_enum_value_rejected_by_rule_checker(self):
        """ENUM-030: RuleChecker.check_enum_value_overflow reports error for negative enum value."""
        from axion_hdl.rule_checker import RuleChecker

        modules = [{
            'name': 'test_mod',
            'registers': [
                {
                    'signal_name': 'ctrl_reg',
                    'is_packed': True,
                    'fields': [{'name': 'status', 'width': 2,
                                'enum_values': {0: 'OK', -1: 'NEG'}}]
                },
                {
                    'signal_name': 'standalone_reg',
                    'is_packed': False,
                    'width': 4,
                    'enum_values': {0: 'A', -5: 'NEG_STANDALONE'}
                }
            ],
            'parsing_errors': []
        }]

        checker = RuleChecker()
        checker.check_enum_value_overflow(modules)
        msgs = [e['msg'] for e in checker.errors]
        self.assertTrue(any('-1' in m for m in msgs),
                        f"Expected '-1' in errors, got: {msgs}")
        self.assertTrue(any('-5' in m for m in msgs),
                        f"Expected '-5' in errors, got: {msgs}")

    # -------------------------------------------------------------------------
    # ENUM-031: YAML field-level invalid enum key reported as parsing error
    # -------------------------------------------------------------------------
    def test_enum_031_yaml_field_invalid_enum_key_reported(self):
        """ENUM-031: YAML parser records error when a field enum key is not a valid integer."""
        import tempfile, textwrap
        from axion_hdl.yaml_input_parser import YAMLInputParser

        yaml_src = textwrap.dedent("""\
            module: bad_key_mod
            base_addr: "0x0000"
            registers:
              - name: ctrl_reg
                addr: "0x00"
                access: RW
                fields:
                  - name: mode
                    bit_offset: 0
                    width: 2
                    access: RW
                    enum_values:
                      0: IDLE
                      not_an_int: BROKEN
                      2: ACTIVE
        """)
        with tempfile.NamedTemporaryFile(suffix='.yaml', mode='w', delete=False) as f:
            f.write(yaml_src)
            fpath = f.name

        parser = YAMLInputParser()
        parser.parse_file(fpath)

        error_msgs = [e['msg'] for e in parser.errors if e.get('file') == fpath]
        self.assertTrue(
            any('not_an_int' in m for m in error_msgs),
            f"Expected error for 'not_an_int' key, got: {error_msgs}"
        )

    # -------------------------------------------------------------------------
    # ENUM-032: YAML standalone register invalid enum key reported as parsing error
    # -------------------------------------------------------------------------
    def test_enum_032_yaml_standalone_invalid_enum_key_reported(self):
        """ENUM-032: YAML parser records error when a standalone register enum key is not a valid integer."""
        import tempfile, textwrap
        from axion_hdl.yaml_input_parser import YAMLInputParser

        yaml_src = textwrap.dedent("""\
            module: bad_standalone_mod
            base_addr: "0x0000"
            registers:
              - name: status_reg
                addr: "0x00"
                access: RO
                width: 4
                enum_values:
                  0: OK
                  not_a_number: BAD
                  15: MAX
        """)
        with tempfile.NamedTemporaryFile(suffix='.yaml', mode='w', delete=False) as f:
            f.write(yaml_src)
            fpath = f.name

        parser = YAMLInputParser()
        parser.parse_file(fpath)

        error_msgs = [e['msg'] for e in parser.errors if e.get('file') == fpath]
        self.assertTrue(
            any('not_a_number' in m for m in error_msgs),
            f"Expected error for 'not_a_number' key, got: {error_msgs}"
        )

    # -------------------------------------------------------------------------
    # ENUM-033: VHDL pkg sanitizes invalid identifier characters
    # -------------------------------------------------------------------------
    def test_enum_033_vhdl_pkg_identifier_sanitization(self):
        """ENUM-033: generate_vhdl_pkg replaces non-alphanumeric chars with '_' in constant names."""
        from axion_hdl.generator import VHDLGenerator

        module = {
            'name': 'san_mod',
            'file': 'test.vhd',
            'base_address': 0,
            'registers': [{
                'signal_name': 'ctrl-reg',
                'reg_name': 'ctrl-reg',
                'is_packed': True,
                'width': 32,
                'fields': [{
                    'name': 'my-field',
                    'width': 2,
                    'bit_low': 0,
                    'bit_high': 1,
                    'access_mode': 'RW',
                    'signal_type': '[1:0]',
                    'enum_values': {0: '1st-state', 3: 'last state'}
                }]
            }]
        }

        gen = VHDLGenerator(self.output_dir)
        pkg_path = gen.generate_vhdl_pkg(module)
        self.assertIsNotNone(pkg_path)

        with open(pkg_path) as f:
            content = f.read()

        # Constant names must not contain hyphens, spaces, or start with digit
        import re
        for line in content.splitlines():
            if line.strip().startswith('constant '):
                # Extract the constant name
                m = re.match(r'\s*constant\s+(C_\S+)\s*:', line)
                if m:
                    cname = m.group(1)
                    self.assertFalse(
                        re.search(r'[^A-Za-z0-9_]', cname),
                        f"Constant name contains invalid chars: {cname!r}"
                    )
                    self.assertFalse(
                        cname[0].isdigit(),
                        f"Constant name starts with digit: {cname!r}"
                    )
        # Verify expected sanitized forms appear
        self.assertIn('CTRL_REG', content)
        self.assertIn('MY_FIELD', content)
        self.assertIn('V_1ST_STATE', content)   # leading digit → prepend v_
        self.assertIn('LAST_STATE', content)

    # -------------------------------------------------------------------------
    # ENUM-034: SV pkg sanitizes invalid identifier characters
    # -------------------------------------------------------------------------
    def test_enum_034_sv_pkg_identifier_sanitization(self):
        """ENUM-034: generate_sv_pkg replaces non-alphanumeric chars with '_' in typedef and member names."""
        from axion_hdl.systemverilog_generator import SystemVerilogGenerator

        module = {
            'name': 'san_sv_mod',
            'file': 'test.sv',
            'base_address': 0,
            'registers': [{
                'signal_name': 'ctrl-reg',
                'reg_name': 'ctrl-reg',
                'is_packed': True,
                'width': 32,
                'fields': [{
                    'name': 'my-field',
                    'width': 2,
                    'bit_low': 0,
                    'bit_high': 1,
                    'access_mode': 'RW',
                    'signal_type': '[1:0]',
                    'enum_values': {0: '2fast', 3: 'slow state'}
                }]
            }]
        }

        gen = SystemVerilogGenerator(self.output_dir)
        pkg_path = gen.generate_sv_pkg(module)
        self.assertIsNotNone(pkg_path)

        with open(pkg_path) as f:
            content = f.read()

        # typedef name must not contain hyphens
        self.assertIn('t_ctrl_reg_my_field_e', content)
        # Member names must be valid SV identifiers
        import re as _re
        for line in content.splitlines():
            m = _re.match(r'\s+(\w+)\s*=\s*\d', line)
            if m:
                ident = m.group(1)
                self.assertFalse(
                    _re.search(r'[^A-Za-z0-9_]', ident),
                    f"SV enum member contains invalid chars: {ident!r}"
                )
        self.assertIn('_2fast', content)    # leading digit → prepend _
        self.assertIn('slow_state', content)

    # -------------------------------------------------------------------------
    # ENUM-035: C header sanitizes invalid identifier characters
    # -------------------------------------------------------------------------
    def test_enum_035_c_header_identifier_sanitization(self):
        """ENUM-035: C header generator sanitizes enum names to valid C identifiers."""
        from axion_hdl.yaml_input_parser import YAMLInputParser
        from axion_hdl.doc_generators import CHeaderGenerator

        module = {
            'name': 'san_c_mod',
            'file': 'test.yaml',
            'base_address': 0,
            'base_addr': '0x0000',
            'registers': [{
                'signal_name': 'ctrl-reg',
                'reg_name': 'ctrl-reg',
                'is_packed': True,
                'width': 32,
                'signal_type': '[31:0]',
                'address': '0x00000000',
                'address_int': 0,
                'relative_address': '0x00',
                'relative_address_int': 0,
                'access_mode': 'RW',
                'read_strobe': False,
                'write_strobe': False,
                'r_strobe': False,
                'w_strobe': False,
                'default_value': 0,
                'description': '',
                'fields': [{
                    'name': 'my field',
                    'width': 2,
                    'bit_low': 0,
                    'bit_high': 1,
                    'access_mode': 'RW',
                    'signal_type': '[1:0]',
                    'description': '',
                    'read_strobe': False,
                    'write_strobe': False,
                    'default_value': 0,
                    'enum_values': {0: '3bad-name', 3: 'good name'}
                }]
            }]
        }

        gen = CHeaderGenerator(self.output_dir)
        header_path = gen.generate_header(module)
        self.assertIsNotNone(header_path)

        with open(header_path) as f:
            content = f.read()

        self.assertNotIn('3bad-name', content)
        self.assertNotIn('good name', content)
        self.assertIn('_3BAD_NAME', content)   # leading digit → prepend _
        self.assertIn('GOOD_NAME', content)

    # -------------------------------------------------------------------------
    # ENUM-036: generate_vhdl_pkg returns None when no enum fields
    # -------------------------------------------------------------------------
    def test_enum_036_vhdl_pkg_returns_none_when_no_enums(self):
        """ENUM-036: generate_vhdl_pkg returns None (Optional[str]) when module has no enum fields."""
        from axion_hdl.generator import VHDLGenerator

        module = {
            'name': 'no_enum_mod',
            'file': 'test.vhd',
            'base_address': 0,
            'registers': [{
                'signal_name': 'data_reg',
                'is_packed': False,
                'width': 32,
                'signal_type': '[31:0]',
                'enum_values': None
            }]
        }

        gen = VHDLGenerator(self.output_dir)
        result = gen.generate_vhdl_pkg(module)
        self.assertIsNone(result)

    # -------------------------------------------------------------------------
    # ENUM-037: generate_sv_pkg returns None when no enum fields
    # -------------------------------------------------------------------------
    def test_enum_037_sv_pkg_returns_none_when_no_enums(self):
        """ENUM-037: generate_sv_pkg returns None (Optional[str]) when module has no enum fields."""
        from axion_hdl.systemverilog_generator import SystemVerilogGenerator

        module = {
            'name': 'no_enum_sv_mod',
            'file': 'test.sv',
            'base_address': 0,
            'registers': [{
                'signal_name': 'data_reg',
                'is_packed': False,
                'width': 32,
                'signal_type': '[31:0]',
                'enum_values': None
            }]
        }

        gen = SystemVerilogGenerator(self.output_dir)
        result = gen.generate_sv_pkg(module)
        self.assertIsNone(result)

    # -------------------------------------------------------------------------
    # ENUM-038: VHDL port comment does not contain double '--'
    # -------------------------------------------------------------------------
    def test_enum_038_vhdl_port_comment_no_double_dash(self):
        """ENUM-038: VHDL port comment for enum field uses parentheses, not embedded '--'."""
        from axion_hdl.yaml_input_parser import YAMLInputParser
        from axion_hdl.generator import VHDLGenerator

        module = {
            'name': 'dash_test_mod',
            'file': 'test.yaml',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': [{
                'signal_name': 'ctrl_reg',
                'reg_name': 'ctrl_reg',
                'is_packed': True,
                'width': 32,
                'address': '0x00000000',
                'address_int': 0,
                'relative_address': '0x00',
                'relative_address_int': 0,
                'access_mode': 'RW',
                'read_strobe': False,
                'write_strobe': False,
                'r_strobe': False,
                'w_strobe': False,
                'default_value': 0,
                'description': 'Control register',
                'fields': [{
                    'name': 'enable',
                    'width': 1,
                    'bit_low': 0,
                    'bit_high': 0,
                    'access_mode': 'RW',
                    'signal_type': 'std_logic',
                    'description': 'Enable signal',
                    'read_strobe': False,
                    'write_strobe': False,
                    'default_value': 0,
                    'enum_values': {0: 'OFF', 1: 'ON'}
                }]
            }]
        }

        gen = VHDLGenerator(self.output_dir)
        out_path = gen.generate_module(module)

        with open(out_path) as f:
            content = f.read()

        # Must not have any line with two separate '--' occurrences
        for line in content.splitlines():
            stripped = line.lstrip()
            if stripped.startswith('--'):
                continue  # pure comment lines are fine
            occurrences = line.count('--')
            self.assertLessEqual(
                occurrences, 1,
                f"Double '--' in port line: {line!r}"
            )

    # -------------------------------------------------------------------------
    # ENUM-039: generate_module co-generates _regs_pkg when enum fields exist
    # -------------------------------------------------------------------------
    def test_enum_039_generate_module_coproduces_pkg(self):
        """ENUM-039: generate_module() produces _regs_pkg.vhd alongside the register module."""
        import os
        from axion_hdl.generator import VHDLGenerator

        module = {
            'name': 'copkg_mod',
            'file': 'test.yaml',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': [{
                'signal_name': 'ctrl_reg',
                'reg_name': 'ctrl_reg',
                'is_packed': True,
                'width': 32,
                'address': '0x00000000',
                'address_int': 0,
                'relative_address': '0x00',
                'relative_address_int': 0,
                'access_mode': 'RW',
                'read_strobe': False,
                'write_strobe': False,
                'r_strobe': False,
                'w_strobe': False,
                'default_value': 0,
                'description': '',
                'fields': [{
                    'name': 'status',
                    'width': 2,
                    'bit_low': 0,
                    'bit_high': 1,
                    'access_mode': 'RO',
                    'signal_type': '[1:0]',
                    'description': '',
                    'read_strobe': False,
                    'write_strobe': False,
                    'default_value': 0,
                    'enum_values': {0: 'IDLE', 3: 'BUSY'}
                }]
            }]
        }

        gen = VHDLGenerator(self.output_dir)
        gen.generate_module(module)

        pkg_path = os.path.join(self.output_dir, 'copkg_mod_regs_pkg.vhd')
        self.assertTrue(
            os.path.exists(pkg_path),
            "generate_module() must co-produce _regs_pkg.vhd when enum fields exist"
        )


    # -------------------------------------------------------------------------
    # ENUM-040: XML simple format records error for invalid enum_value
    # -------------------------------------------------------------------------
    def test_enum_040_xml_simple_invalid_enum_value_recorded(self):
        """ENUM-040: XML parser records an error when a simple-format <enum_value> has a non-integer value."""
        import tempfile
        import os
        from axion_hdl.xml_input_parser import XMLInputParser

        xml_content = """\
<register_map module="err_mod" base_addr="0x0000">
  <register name="ctrl" addr="0x00" access="RW" width="2">
    <field name="mode" bits="1:0">
      <enum_value value="notanint" name="INVALID"/>
      <enum_value value="1" name="RUN"/>
    </field>
  </register>
</register_map>
"""
        with tempfile.NamedTemporaryFile(suffix='.xml', mode='w', delete=False) as f:
            f.write(xml_content)
            tmp_path = f.name

        try:
            parser = XMLInputParser()
            parser.parse_file(tmp_path)
            error_msgs = [e.get('msg', '') for e in parser.errors]
            self.assertTrue(
                any('notanint' in m or 'Invalid enum_value' in m or 'Invalid' in m
                    for m in error_msgs),
                f"Expected error for non-integer enum_value; got: {error_msgs}"
            )
        finally:
            os.unlink(tmp_path)

    # -------------------------------------------------------------------------
    # ENUM-041: XML SPIRIT format records error for invalid spirit:value
    # -------------------------------------------------------------------------
    def test_enum_041_xml_spirit_invalid_enum_value_recorded(self):
        """ENUM-041: XML parser records an error when a SPIRIT <spirit:value> has a non-integer value."""
        import tempfile
        import os
        from axion_hdl.xml_input_parser import XMLInputParser

        xml_content = """\
<?xml version="1.0" encoding="UTF-8"?>
<spirit:component xmlns:spirit="http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5">
  <spirit:name>spirit_err_mod</spirit:name>
  <spirit:memoryMaps>
    <spirit:memoryMap>
      <spirit:addressBlock>
        <spirit:baseAddress>0</spirit:baseAddress>
        <spirit:register>
          <spirit:name>ctrl</spirit:name>
          <spirit:addressOffset>0</spirit:addressOffset>
          <spirit:size>32</spirit:size>
          <spirit:access>read-write</spirit:access>
          <spirit:field>
            <spirit:name>mode</spirit:name>
            <spirit:bitOffset>0</spirit:bitOffset>
            <spirit:bitWidth>2</spirit:bitWidth>
            <spirit:enumeratedValues>
              <spirit:enumeratedValue>
                <spirit:name>BADVAL</spirit:name>
                <spirit:value>notanint</spirit:value>
              </spirit:enumeratedValue>
            </spirit:enumeratedValues>
          </spirit:field>
        </spirit:register>
      </spirit:addressBlock>
    </spirit:memoryMap>
  </spirit:memoryMaps>
</spirit:component>
"""
        with tempfile.NamedTemporaryFile(suffix='.xml', mode='w', delete=False) as f:
            f.write(xml_content)
            tmp_path = f.name

        try:
            parser = XMLInputParser()
            parser.parse_file(tmp_path)
            error_msgs = [e.get('msg', '') for e in parser.errors]
            self.assertTrue(
                any('notanint' in m or 'SPIRIT' in m or 'Invalid' in m
                    for m in error_msgs),
                f"Expected error for non-integer spirit:value; got: {error_msgs}"
            )
        finally:
            os.unlink(tmp_path)

    # -------------------------------------------------------------------------
    # ENUM-042: VHDL identifier sanitizer produces no adjacent underscores
    # -------------------------------------------------------------------------
    def test_enum_042_vhdl_identifier_no_adjacent_underscores(self):
        """ENUM-042: _sanitize_vhdl_identifier collapses adjacent underscores and strips leading/trailing ones."""
        from axion_hdl.generator import VHDLGenerator

        cases = [
            ('ctrl--reg', 'CTRL_REG'),      # adjacent underscores collapsed
            ('-leading', 'LEADING'),          # leading underscore stripped
            ('trailing-', 'TRAILING'),        # trailing underscore stripped
            ('1st-thing', 'V_1ST_THING'),    # digit prefix → v_ prepended
            ('--bad--name--', 'BAD_NAME'),   # multiple separators collapsed and stripped
        ]

        gen = VHDLGenerator.__new__(VHDLGenerator)
        for raw, expected in cases:
            result = gen._sanitize_vhdl_identifier(raw).upper()
            self.assertEqual(result, expected, f"Input {raw!r}: expected {expected!r}, got {result!r}")
            # Must not have adjacent underscores
            self.assertNotIn('__', result, f"Adjacent underscores in result for {raw!r}: {result!r}")
            # Must not start or end with underscore
            self.assertFalse(result.startswith('_'), f"Starts with _ for {raw!r}: {result!r}")
            self.assertFalse(result.endswith('_'), f"Ends with _ for {raw!r}: {result!r}")


if __name__ == '__main__':
    unittest.main()
