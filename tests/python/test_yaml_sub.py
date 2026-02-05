#!/usr/bin/env python3
"""
test_yaml_sub.py - YAML Subregister (Packed Register) Tests

Tests that YAML parser correctly handles packed registers (subregisters)
with bit_offset, width, and default values.

Maps to requirements:
- SUB-001 to SUB-010
- YAML-INPUT-001 to YAML-INPUT-016
"""

import unittest
import os
from pathlib import Path
from axion_hdl.yaml_input_parser import YAMLInputParser


class TestYAMLSubregisters(unittest.TestCase):
    """SUB-001 to SUB-010: YAML packed register parsing and field validation."""

    def setUp(self):
        self.parser = YAMLInputParser()
        yaml_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../yaml/subregister_test.yaml')
        )
        self.module = self.parser.parse_file(yaml_path)
        self.assertIsNotNone(self.module, "Module should parse successfully")

    def test_sub_001_module_metadata(self):
        """SUB-001: Module name and base address parsed correctly"""
        self.assertEqual(self.module['entity_name'], 'subregister_test_yaml')
        self.assertEqual(self.module['base_address'], 0x4000)

    def test_sub_002_packed_registers_present(self):
        """SUB-002: Packed registers are identified and separated"""
        self.assertIn('packed_registers', self.module)
        self.assertEqual(len(self.module['packed_registers']), 2,
                         "Should have 2 packed registers: status_reg, control_reg")

    def test_sub_003_standard_register_preserved(self):
        """SUB-003: Standard (non-packed) registers still work correctly"""
        config_reg = next((r for r in self.module['registers']
                          if r['signal_name'] == 'config_reg' and not r.get('is_packed')), None)
        self.assertIsNotNone(config_reg, "config_reg should exist as standard register")
        self.assertEqual(config_reg['width'], 32)
        self.assertEqual(config_reg['access_mode'], 'RW')
        self.assertEqual(config_reg['default_value'], 0xCAFEBABE)

    def test_sub_004_status_reg_structure(self):
        """SUB-004: status_reg packed register structure (RO, 5 fields)"""
        status_reg = next((r for r in self.module['packed_registers']
                          if r['name'] == 'status_reg'), None)
        self.assertIsNotNone(status_reg, "status_reg should exist")
        self.assertEqual(status_reg['access_mode'], 'RO')
        self.assertEqual(len(status_reg['fields']), 5)
        self.assertEqual(status_reg['relative_address_int'], 0x04)

    def test_sub_005_status_reg_field_ready(self):
        """SUB-005: status_reg.ready field (bit 0, width 1)"""
        status_reg = next(r for r in self.module['packed_registers'] if r['name'] == 'status_reg')
        ready = next((f for f in status_reg['fields'] if f['name'] == 'ready'), None)
        self.assertIsNotNone(ready)
        self.assertEqual(ready['bit_low'], 0)
        self.assertEqual(ready['bit_high'], 0)
        self.assertEqual(ready['width'], 1)
        self.assertEqual(ready['access_mode'], 'RO')

    def test_sub_006_status_reg_field_state(self):
        """SUB-006: status_reg.state field (bits 7:4, width 4)"""
        status_reg = next(r for r in self.module['packed_registers'] if r['name'] == 'status_reg')
        state = next((f for f in status_reg['fields'] if f['name'] == 'state'), None)
        self.assertIsNotNone(state)
        self.assertEqual(state['bit_low'], 4)
        self.assertEqual(state['bit_high'], 7)
        self.assertEqual(state['width'], 4)

    def test_sub_007_status_reg_field_count(self):
        """SUB-007: status_reg.count field (bits 15:8, width 8)"""
        status_reg = next(r for r in self.module['packed_registers'] if r['name'] == 'status_reg')
        count = next((f for f in status_reg['fields'] if f['name'] == 'count'), None)
        self.assertIsNotNone(count)
        self.assertEqual(count['bit_low'], 8)
        self.assertEqual(count['bit_high'], 15)
        self.assertEqual(count['width'], 8)

    def test_sub_008_control_reg_structure(self):
        """SUB-008: control_reg packed register structure (RW, 4 fields, defaults)"""
        control_reg = next((r for r in self.module['packed_registers']
                           if r['name'] == 'control_reg'), None)
        self.assertIsNotNone(control_reg, "control_reg should exist")
        self.assertEqual(control_reg['access_mode'], 'RW')
        self.assertEqual(len(control_reg['fields']), 4)
        self.assertEqual(control_reg['relative_address_int'], 0x10)

    def test_sub_009_control_reg_field_defaults(self):
        """SUB-009: control_reg fields have correct default values"""
        control_reg = next(r for r in self.module['packed_registers'] if r['name'] == 'control_reg')

        enable = next(f for f in control_reg['fields'] if f['name'] == 'enable')
        self.assertEqual(enable['default_value'], 1)

        mode = next(f for f in control_reg['fields'] if f['name'] == 'mode')
        self.assertEqual(mode['default_value'], 0)

        irq_mask = next(f for f in control_reg['fields'] if f['name'] == 'irq_mask')
        self.assertEqual(irq_mask['default_value'], 0xF)

        timeout = next(f for f in control_reg['fields'] if f['name'] == 'timeout')
        self.assertEqual(timeout['default_value'], 100)

    def test_sub_010_control_reg_combined_default(self):
        """SUB-010: control_reg combined default value calculation

        Combined default should be:
        enable(1)<<0 | mode(0)<<1 | irq_mask(15)<<4 | timeout(100)<<8 = 0x64F1
        """
        control_reg = next(r for r in self.module['packed_registers'] if r['name'] == 'control_reg')
        self.assertEqual(control_reg['default_value'], 0x64F1,
                        "Combined default: (1<<0) | (0<<1) | (15<<4) | (100<<8) = 0x64F1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
