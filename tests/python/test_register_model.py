"""
Tests for the Python Register Model feature in axion-hdl.

Each test is mapped to a specific requirement ID (REG-MODEL-NNN).
All tests use inline module dicts — no YAML/VHDL parsing required.
"""

import os
import sys
import tempfile
import shutil
import unittest
import importlib.util

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

TESTS_DIR = os.path.join(PROJECT_ROOT, 'tests')
YAML_DIR = os.path.join(TESTS_DIR, 'yaml')


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _make_field_dict(name='ready', bit_low=0, bit_high=0, width=1,
                     access_mode='RO', default_value=0,
                     read_strobe=False, write_strobe=False,
                     enum_values=None, description=''):
    return {
        'name': name,
        'bit_low': bit_low,
        'bit_high': bit_high,
        'width': width,
        'access_mode': access_mode,
        'default_value': default_value,
        'read_strobe': read_strobe,
        'write_strobe': write_strobe,
        'enum_values': enum_values or {},
        'description': description,
    }


def _make_reg_dict(name, addr_int, rel_int, access_mode='RW', width=32,
                   default_value=0, read_strobe=False, write_strobe=False,
                   is_packed=False, fields=None, description='', enum_values=None):
    return {
        'signal_name': name,
        'name': name,
        'address_int': addr_int,
        'relative_address_int': rel_int,
        'access_mode': access_mode,
        'width': width,
        'default_value': default_value,
        'read_strobe': read_strobe,
        'write_strobe': write_strobe,
        'is_packed': is_packed,
        'fields': fields or [],
        'description': description,
        'enum_values': enum_values or {},
    }


SAMPLE_MODULE = {
    'name': 'test_mod',
    'entity_name': 'test_mod',
    'base_address': 0x1000,
    'cdc_enabled': False,
    'cdc_stages': 2,
    'use_axion_types': False,
    'parsing_errors': [],
    'packed_registers': [],
    'registers': [
        _make_reg_dict('control', 0x1000, 0, access_mode='RW', default_value=0,
                       write_strobe=True, description='Control register'),
        _make_reg_dict('command', 0x1004, 4, access_mode='WO', default_value=0),
        _make_reg_dict('status', 0x1008, 8, access_mode='RO', default_value=0,
                       is_packed=True,
                       fields=[
                           _make_field_dict('ready', 0, 0, 1, 'RO', 0,
                                            enum_values={0: 'NOT_READY', 1: 'READY'}),
                           _make_field_dict('state', 4, 7, 4, 'RO', 0),
                       ]),
        _make_reg_dict('config', 0x100C, 12, access_mode='RW', default_value=0xAB,
                       is_packed=True,
                       fields=[
                           _make_field_dict('enable', 0, 0, 1, 'RW', 1, write_strobe=True),
                           _make_field_dict('mode', 1, 2, 2, 'RW', 0),
                       ]),
        _make_reg_dict('irq_status', 0x1010, 16, access_mode='RW', default_value=0,
                       read_strobe=True),
    ],
}


# ---------------------------------------------------------------------------
# TestFieldModel — REG-MODEL-001..006
# ---------------------------------------------------------------------------

class TestFieldModel(unittest.TestCase):

    def setUp(self):
        from axion_hdl.register_model import RegisterModel
        reg_dict = _make_reg_dict('status', 0x1008, 8, access_mode='RO', is_packed=True,
                                  fields=[
                                      _make_field_dict('ready', 0, 0, 1, 'RO', 0,
                                                       enum_values={0: 'NOT_READY', 1: 'READY'}),
                                      _make_field_dict('err_flag', 1, 1, 1, 'RO', 0),
                                      _make_field_dict('state', 4, 7, 4, 'RO', 0),
                                  ])
        self.reg = RegisterModel(reg_dict, base_address=0x1000)

    def test_register_model_001_field_model_construction(self):
        """REG-MODEL-001: FieldModel constructed correctly from field dict."""
        from axion_hdl.register_model import FieldModel
        f = self.reg.fields['ready']
        self.assertIsInstance(f, FieldModel)
        self.assertEqual(f.name, 'ready')
        self.assertEqual(f.bit_low, 0)
        self.assertEqual(f.bit_high, 0)
        self.assertEqual(f.width, 1)
        self.assertEqual(f.default_value, 0)
        self.assertEqual(f.mask, 0b1)

    def test_register_model_002_field_value_bit_masking_read(self):
        """REG-MODEL-002: FieldModel.value extracts correct bits from parent raw_value."""
        # Force parent raw value: set bits [7:4] = 0b1010, bit 0 = 1
        self.reg._raw_value = 0b10100001
        self.assertEqual(self.reg.fields['ready'].value, 1)
        self.assertEqual(self.reg.fields['state'].value, 0b1010)

    def test_register_model_003_field_value_setter_bit_masking(self):
        """REG-MODEL-003: FieldModel.value setter updates only field bits, others intact."""
        from axion_hdl.register_model import RegisterModel
        reg_dict = _make_reg_dict('cfg', 0x0, 0, access_mode='RW', is_packed=True,
                                  fields=[
                                      _make_field_dict('low', 0, 3, 4, 'RW', 0),
                                      _make_field_dict('high', 4, 7, 4, 'RW', 0),
                                  ])
        reg = RegisterModel(reg_dict, 0)
        reg._raw_value = 0xFF  # all bits set
        reg.fields['low'].value = 0b0101
        # Only bits [3:0] changed; bits [7:4] still 0xF
        self.assertEqual(reg._raw_value & 0xF, 0b0101)
        self.assertEqual((reg._raw_value >> 4) & 0xF, 0xF)

    def test_register_model_004_ro_field_write_raises(self):
        """REG-MODEL-004: RO field write raises ReadOnlyError."""
        from axion_hdl.register_model import ReadOnlyError
        with self.assertRaises(ReadOnlyError):
            self.reg.fields['ready'].value = 1

    def test_register_model_005_enum_name(self):
        """REG-MODEL-005: FieldModel.enum_name returns string from enum table."""
        self.reg._raw_value = 0b0  # ready = 0
        self.assertEqual(self.reg.fields['ready'].enum_name, 'NOT_READY')
        self.reg._raw_value = 0b1  # ready = 1
        self.assertEqual(self.reg.fields['ready'].enum_name, 'READY')
        # Field with no enum mapping
        self.assertIsNone(self.reg.fields['state'].enum_name)

    def test_register_model_006_field_reset_bypasses_ro(self):
        """REG-MODEL-006: FieldModel.reset() restores default without RO check."""
        self.reg._raw_value = 0b1111_1111  # force all bits
        # ready is RO but reset() should not raise
        self.reg.fields['ready'].reset()
        # ready bit should now be its default (0)
        self.assertEqual(self.reg.fields['ready'].raw_value, 0)


# ---------------------------------------------------------------------------
# TestRegisterModel — REG-MODEL-010..022
# ---------------------------------------------------------------------------

class TestRegisterModel(unittest.TestCase):

    def setUp(self):
        from axion_hdl.register_model import RegisterSpaceModel
        self.space = RegisterSpaceModel.from_module_dict(SAMPLE_MODULE)

    def test_register_model_010_register_construction(self):
        """REG-MODEL-010: RegisterModel constructed correctly from register dict."""
        reg = self.space.get_register('control')
        self.assertEqual(reg.name, 'control')
        self.assertEqual(reg.address, 0x1000)
        self.assertEqual(reg.access_mode, 'RW')
        self.assertEqual(reg.default_value, 0)
        self.assertEqual(reg.width, 32)

    def test_register_model_011_rw_read_returns_raw(self):
        """REG-MODEL-011: RW register .value returns raw_value."""
        reg = self.space.get_register('control')
        reg._raw_value = 0xDEAD
        self.assertEqual(reg.value, 0xDEAD)

    def test_register_model_011b_ro_read_returns_raw(self):
        """REG-MODEL-011: RO register .value returns raw_value."""
        reg = self.space.get_register('status')
        reg._raw_value = 0x55
        self.assertEqual(reg.value, 0x55)

    def test_register_model_011c_wo_value_returns_zero(self):
        """REG-MODEL-011: WO register .value returns 0 (bus read semantics)."""
        reg = self.space.get_register('command')
        reg._raw_value = 0xBEEF
        self.assertEqual(reg.value, 0)

    def test_register_model_012_ro_write_raises(self):
        """REG-MODEL-012: write() on RO register raises ReadOnlyError."""
        from axion_hdl.register_model import ReadOnlyError
        reg = self.space.get_register('status')
        with self.assertRaises(ReadOnlyError):
            reg.write(0x1)

    def test_register_model_013_wo_read_returns_zero(self):
        """REG-MODEL-013: WO register read() returns 0."""
        reg = self.space.get_register('command')
        reg._raw_value = 0xCAFE
        self.assertEqual(reg.read(), 0)

    def test_register_model_014_reset_restores_default(self):
        """REG-MODEL-014: RegisterModel.reset() restores _raw_value to default_value."""
        reg = self.space.get_register('config')
        reg._raw_value = 0xFFFF_FFFF
        reg.reset()
        self.assertEqual(reg._raw_value, 0xAB)

    def test_register_model_015_packed_register_fields(self):
        """REG-MODEL-015: Packed register exposes correct FieldModel entries."""
        from axion_hdl.register_model import FieldModel
        reg = self.space.get_register('status')
        self.assertTrue(reg.is_packed)
        self.assertIn('ready', reg.fields)
        self.assertIn('state', reg.fields)
        self.assertIsInstance(reg.fields['ready'], FieldModel)

    def test_register_model_016_getattr_field_access(self):
        """REG-MODEL-016: reg.fieldname → reg.fields['fieldname']."""
        reg = self.space.get_register('status')
        self.assertIs(reg.ready, reg.fields['ready'])

    def test_register_model_017_dump_contains_name_and_value(self):
        """REG-MODEL-017: RegisterModel.dump() returns string with name and value."""
        reg = self.space.get_register('control')
        dumped = reg.dump()
        self.assertIn('control', dumped)
        self.assertIn('RW', dumped)

    def test_register_model_018_write_strobe_callback_fires(self):
        """REG-MODEL-018: Write-strobe callback fires exactly once on write() when write_strobe=True."""
        reg = self.space.get_register('control')
        calls = []
        reg.on_write(lambda name, val: calls.append((name, val)))
        reg.write(0x42)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0], ('control', 0x42))

    def test_register_model_019_write_strobe_silent_when_false(self):
        """REG-MODEL-019: Write-strobe callback not triggered when write_strobe=False."""
        reg = self.space.get_register('config')
        # config has write_strobe=False at register level
        calls = []
        reg.on_write(lambda name, val: calls.append((name, val)))
        reg.write(0x3)
        # Callback should not fire (register-level write_strobe is False)
        self.assertEqual(len(calls), 0)

    def test_register_model_020_read_strobe_callback_fires(self):
        """REG-MODEL-020: Read-strobe callback fires on read() when read_strobe=True."""
        reg = self.space.get_register('irq_status')
        calls = []
        reg.on_read(lambda name, val: calls.append((name, val)))
        reg.read()
        self.assertEqual(len(calls), 1)

    def test_register_model_021_callback_arguments(self):
        """REG-MODEL-021: Callback receives correct (register_name, value) arguments."""
        reg = self.space.get_register('control')
        received = []
        reg.on_write(lambda name, val: received.append((name, val)))
        reg.write(0xBEEF)
        self.assertEqual(received[0][0], 'control')
        self.assertEqual(received[0][1], 0xBEEF)

    def test_register_model_022_raw_value_wo_bypass(self):
        """REG-MODEL-022: raw_value always returns _raw_value regardless of access mode."""
        reg = self.space.get_register('command')
        reg._raw_value = 0x1234
        self.assertEqual(reg.raw_value, 0x1234)
        self.assertEqual(reg.value, 0)  # bus read → 0 for WO


# ---------------------------------------------------------------------------
# TestRegisterSpaceModel — REG-MODEL-030..042
# ---------------------------------------------------------------------------

class TestRegisterSpaceModel(unittest.TestCase):

    def setUp(self):
        from axion_hdl.register_model import RegisterSpaceModel
        self.space = RegisterSpaceModel.from_module_dict(SAMPLE_MODULE)

    def test_register_model_030_from_module_dict_loads_all(self):
        """REG-MODEL-030: from_module_dict() loads all registers from module dict."""
        self.assertEqual(self.space.name, 'test_mod')
        self.assertEqual(self.space.base_address, 0x1000)
        self.assertEqual(len(self.space.registers), 5)

    def test_register_model_031_bus_read_returns_value(self):
        """REG-MODEL-031: space.read(addr) returns register value at absolute address."""
        self.space.get_register('control')._raw_value = 0xCAFE
        self.assertEqual(self.space.read(0x1000), 0xCAFE)

    def test_register_model_032_bus_write_updates_register(self):
        """REG-MODEL-032: space.write(addr, val) updates register raw value."""
        self.space.write(0x1000, 0x1234)
        self.assertEqual(self.space.get_register('control')._raw_value, 0x1234)

    def test_register_model_033_ro_bus_write_raises(self):
        """REG-MODEL-033: space.write() to RO register raises ReadOnlyError."""
        from axion_hdl.register_model import ReadOnlyError
        with self.assertRaises(ReadOnlyError):
            self.space.write(0x1008, 0xFF)

    def test_register_model_034_unknown_address_read_raises(self):
        """REG-MODEL-034: space.read() at unknown address raises AddressError."""
        from axion_hdl.register_model import AddressError
        with self.assertRaises(AddressError):
            self.space.read(0xDEAD)

    def test_register_model_035_unknown_address_write_raises(self):
        """REG-MODEL-035: space.write() at unknown address raises AddressError."""
        from axion_hdl.register_model import AddressError
        with self.assertRaises(AddressError):
            self.space.write(0xDEAD, 0)

    def test_register_model_036_space_reset_restores_defaults(self):
        """REG-MODEL-036: space.reset() restores all registers to default values."""
        self.space.write(0x1000, 0xFFFF_FFFF)
        self.space.reset()
        self.assertEqual(self.space.get_register('control')._raw_value, 0)
        self.assertEqual(self.space.get_register('config')._raw_value, 0xAB)

    def test_register_model_037_space_attribute_access(self):
        """REG-MODEL-037: space.regname → correct RegisterModel."""
        from axion_hdl.register_model import RegisterModel
        self.assertIsInstance(self.space.control, RegisterModel)
        self.assertEqual(self.space.control.name, 'control')

    def test_register_model_038_field_chain_access(self):
        """REG-MODEL-038: space.status.fields['ready'] → correct FieldModel."""
        from axion_hdl.register_model import FieldModel
        f = self.space.status.fields['ready']
        self.assertIsInstance(f, FieldModel)
        self.assertEqual(f.name, 'ready')

    def test_register_model_039_space_on_write_attaches_callback(self):
        """REG-MODEL-039: space.on_write() attaches callback; fires on next write."""
        calls = []
        self.space.on_write('control', lambda name, val: calls.append((name, val)))
        self.space.write(0x1000, 0x77)
        self.assertEqual(len(calls), 1)

    def test_register_model_040_space_dump_covers_all_registers(self):
        """REG-MODEL-040: space.dump() returns multi-line string covering all registers."""
        dumped = self.space.dump()
        self.assertIn('test_mod', dumped)
        for name in ['control', 'status', 'config']:
            self.assertIn(name, dumped)

    def test_register_model_041_space_registers_property(self):
        """REG-MODEL-041: space.registers returns Dict[str, RegisterModel]."""
        from axion_hdl.register_model import RegisterModel
        regs = self.space.registers
        self.assertIsInstance(regs, dict)
        self.assertIn('control', regs)
        self.assertIsInstance(regs['control'], RegisterModel)

    def test_register_model_042_space_iteration_address_order(self):
        """REG-MODEL-042: Iterating space yields registers in address order."""
        addresses = [reg.address for reg in self.space]
        self.assertEqual(addresses, sorted(addresses))


# ---------------------------------------------------------------------------
# TestAxionHDLIntegration — REG-MODEL-050..055
# ---------------------------------------------------------------------------

class TestAxionHDLIntegration(unittest.TestCase):

    def setUp(self):
        self.output_dir = tempfile.mkdtemp(prefix='axion_regmodel_test_')

    def tearDown(self):
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def _make_axion_with_yaml(self, yaml_filename='sensor_controller.yaml'):
        from axion_hdl import AxionHDL
        axion = AxionHDL(output_dir=self.output_dir)
        yaml_path = os.path.join(YAML_DIR, yaml_filename)
        if os.path.exists(yaml_path):
            axion.add_source(yaml_path)
            axion.analyze()
        return axion

    def test_register_model_050_get_model_before_analyze_raises(self):
        """REG-MODEL-050: get_model() before analyze() raises RuntimeError."""
        from axion_hdl import AxionHDL
        axion = AxionHDL(output_dir=self.output_dir)
        with self.assertRaises(RuntimeError):
            axion.get_model('something')

    def test_register_model_051_get_model_unknown_name_raises(self):
        """REG-MODEL-051: get_model() for unknown module name raises KeyError."""
        axion = self._make_axion_with_yaml()
        if not axion.is_analyzed:
            self.skipTest("No YAML test file available")
        with self.assertRaises(KeyError):
            axion.get_model('__nonexistent_module__')

    def test_register_model_052_get_model_returns_space(self):
        """REG-MODEL-052: get_model() returns RegisterSpaceModel with correct name."""
        from axion_hdl.register_model import RegisterSpaceModel
        axion = self._make_axion_with_yaml()
        if not axion.is_analyzed or not axion.analyzed_modules:
            self.skipTest("No YAML test file available")
        module_name = axion.analyzed_modules[0].get('name') or axion.analyzed_modules[0].get('entity_name')
        space = axion.get_model(module_name)
        self.assertIsInstance(space, RegisterSpaceModel)
        self.assertEqual(space.name, module_name)

    def test_register_model_053_get_models_returns_dict(self):
        """REG-MODEL-053: get_models() returns dict of all modules as RegisterSpaceModel."""
        from axion_hdl.register_model import RegisterSpaceModel
        axion = self._make_axion_with_yaml()
        if not axion.is_analyzed or not axion.analyzed_modules:
            self.skipTest("No YAML test file available")
        models = axion.get_models()
        self.assertIsInstance(models, dict)
        self.assertEqual(len(models), len(axion.analyzed_modules))
        for space in models.values():
            self.assertIsInstance(space, RegisterSpaceModel)

    def test_register_model_054_yaml_round_trip(self):
        """REG-MODEL-054: YAML → analyze → model → write → read returns correct value."""
        axion = self._make_axion_with_yaml()
        if not axion.is_analyzed or not axion.analyzed_modules:
            self.skipTest("No YAML test file available")
        module_name = axion.analyzed_modules[0].get('name') or axion.analyzed_modules[0].get('entity_name')
        space = axion.get_model(module_name)
        # Find first RW register
        rw_reg = next((r for r in space if r.access_mode == 'RW'), None)
        if rw_reg is None:
            self.skipTest("No RW register in test module")
        test_val = 0x5A5A5A5A & ((1 << rw_reg.width) - 1)
        space.write(rw_reg.address, test_val)
        self.assertEqual(space.read(rw_reg.address), test_val)

    def test_register_model_055_get_model_by_entity_name(self):
        """REG-MODEL-055: get_model() finds module by entity_name fallback."""
        from axion_hdl import AxionHDL
        from axion_hdl.register_model import RegisterSpaceModel
        axion = AxionHDL(output_dir=self.output_dir)
        # Manually inject a module with entity_name but no 'name' key
        axion.analyzed_modules = [{
            'entity_name': 'manual_mod',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'use_axion_types': False,
            'registers': [],
            'packed_registers': [],
        }]
        axion.is_analyzed = True
        space = axion.get_model('manual_mod')
        self.assertIsInstance(space, RegisterSpaceModel)


# ---------------------------------------------------------------------------
# TestPythonGenerator — REG-MODEL-060..065
# ---------------------------------------------------------------------------

class TestPythonGenerator(unittest.TestCase):

    def setUp(self):
        self.output_dir = tempfile.mkdtemp(prefix='axion_pygen_test_')

    def tearDown(self):
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def _generate(self):
        from axion_hdl.python_generator import PythonGenerator
        gen = PythonGenerator(self.output_dir)
        return gen.generate(SAMPLE_MODULE)

    def test_register_model_060_generator_creates_file(self):
        """REG-MODEL-060: PythonGenerator creates *_regs.py file in output directory."""
        path = self._generate()
        self.assertTrue(os.path.exists(path))
        self.assertTrue(path.endswith('_regs.py'))

    def test_register_model_061_generated_file_importable(self):
        """REG-MODEL-061: Generated *_regs.py can be successfully imported."""
        path = self._generate()
        spec = importlib.util.spec_from_file_location('test_regs', path)
        mod = importlib.util.module_from_spec(spec)
        # Should not raise
        spec.loader.exec_module(mod)

    def test_register_model_062_generated_module_symbol(self):
        """REG-MODEL-062: Generated file exposes uppercase symbol = RegisterSpaceModel."""
        from axion_hdl.register_model import RegisterSpaceModel
        path = self._generate()
        spec = importlib.util.spec_from_file_location('test_regs', path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        symbol = getattr(mod, 'TEST_MOD', None)
        self.assertIsNotNone(symbol, "Expected TEST_MOD symbol in generated file")
        self.assertIsInstance(symbol, RegisterSpaceModel)

    def test_register_model_063_generated_model_functional(self):
        """REG-MODEL-063: Generated model supports write/read and returns correct values."""
        path = self._generate()
        spec = importlib.util.spec_from_file_location('test_regs', path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        space = mod.TEST_MOD
        space.write(0x1000, 0xDEAD)
        self.assertEqual(space.read(0x1000), 0xDEAD)

    def test_register_model_064_cli_python_flag(self):
        """REG-MODEL-064: generate_python() via AxionHDL API produces *_regs.py."""
        from axion_hdl import AxionHDL
        axion = AxionHDL(output_dir=self.output_dir)
        axion.analyzed_modules = [SAMPLE_MODULE]
        axion.is_analyzed = True
        result = axion.generate_python()
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) >= 1)
        for path in result:
            self.assertTrue(os.path.exists(path))
            self.assertTrue(path.endswith('_regs.py'))

    def test_register_model_065_packed_register_generation(self):
        """REG-MODEL-065: Generated model correctly represents packed registers with fields."""
        from axion_hdl.register_model import FieldModel
        path = self._generate()
        spec = importlib.util.spec_from_file_location('test_regs', path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        space = mod.TEST_MOD
        # 'status' is packed with 'ready' field
        status = space.get_register('status')
        self.assertTrue(status.is_packed)
        self.assertIn('ready', status.fields)
        self.assertIsInstance(status.fields['ready'], FieldModel)


if __name__ == '__main__':
    unittest.main()
