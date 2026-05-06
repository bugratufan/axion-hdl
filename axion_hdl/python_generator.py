"""
Python Register Model Generator

Generates *_regs.py files from analyzed module dictionaries.
The generated files can be imported directly in golden models without
re-parsing YAML/VHDL sources. The only runtime dependency is
axion_hdl.register_model.
"""

import os
import pprint
from typing import List


class PythonGenerator:
    """
    Generates importable Python register model files (*_regs.py).

    Each generated file contains a frozen copy of the module dictionary
    and a ready-to-use RegisterSpaceModel instance.
    """

    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def generate(self, module_data: dict, output_dir: str = None) -> str:
        """
        Generate a *_regs.py file for a single module.

        Args:
            module_data: Module dictionary produced by an axion-hdl parser.
            output_dir:  Override output directory. Uses self.output_dir if None.

        Returns:
            Absolute path to the generated file.
        """
        out_dir = output_dir or self.output_dir
        os.makedirs(out_dir, exist_ok=True)

        entity_name = module_data.get('name') or module_data.get('entity_name', 'unknown')
        filename = f"{entity_name}_regs.py"
        output_path = os.path.join(out_dir, filename)

        # Build a clean, serialisable copy of the module dict
        clean_dict = self._clean_module_dict(module_data)

        # Pretty-print the dict so the generated file is human-readable
        dict_repr = pprint.pformat(clean_dict, indent=4, width=100)

        # Construct the symbol name: MY_MODULE (upper-snake of entity_name)
        symbol_name = entity_name.upper()

        content = self._render(entity_name, symbol_name, dict_repr)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return output_path

    def generate_all(self, modules: List[dict]) -> List[str]:
        """Generate *_regs.py files for every module in the list."""
        return [self.generate(m) for m in modules]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _clean_module_dict(self, module_data: dict) -> dict:
        """Return a serialisable subset of the module dict suitable for embedding."""
        clean = {
            'name': module_data.get('name') or module_data.get('entity_name', ''),
            'entity_name': module_data.get('entity_name') or module_data.get('name', ''),
            'base_address': int(module_data.get('base_address') or module_data.get('base_addr', 0)),
            'cdc_enabled': bool(module_data.get('cdc_enabled') or module_data.get('cdc_en', False)),
            'cdc_stages': int(module_data.get('cdc_stages') or module_data.get('cdc_stage', 2)),
            'use_axion_types': bool(module_data.get('use_axion_types', False)),
            'registers': [],
        }

        for reg in module_data.get('registers', []):
            clean['registers'].append(self._clean_register(reg))

        return clean

    def _clean_register(self, reg: dict) -> dict:
        """Return a serialisable register dict."""
        clean = {
            'name': reg.get('signal_name') or reg.get('name', ''),
            'signal_name': reg.get('signal_name') or reg.get('name', ''),
            'address_int': int(reg.get('address_int', 0)),
            'relative_address_int': int(reg.get('relative_address_int', 0)),
            'access_mode': reg.get('access_mode') or reg.get('access', 'RW'),
            'width': int(reg.get('width', 32)),
            'default_value': int(reg.get('default_value', 0)),
            'read_strobe': bool(reg.get('read_strobe') or reg.get('r_strobe', False)),
            'write_strobe': bool(reg.get('write_strobe') or reg.get('w_strobe', False)),
            'is_packed': bool(reg.get('is_packed', False)),
            'description': str(reg.get('description', '')),
            'enum_values': self._clean_enum(reg.get('enum_values')),
            'fields': [],
        }

        for field in reg.get('fields', []):
            clean['fields'].append(self._clean_field(field))

        return clean

    def _clean_field(self, field: dict) -> dict:
        """Return a serialisable field dict."""
        return {
            'name': field.get('name', ''),
            'bit_low': int(field.get('bit_low', 0)),
            'bit_high': int(field.get('bit_high', 0)),
            'width': int(field.get('width', 1)),
            'access_mode': field.get('access_mode', 'RW'),
            'default_value': int(field.get('default_value', 0)),
            'read_strobe': bool(field.get('read_strobe', False)),
            'write_strobe': bool(field.get('write_strobe', False)),
            'description': str(field.get('description', '')),
            'enum_values': self._clean_enum(field.get('enum_values')),
        }

    @staticmethod
    def _clean_enum(enum_values) -> dict:
        """Normalise enum_values to {int: str} or empty dict."""
        if not enum_values:
            return {}
        return {int(k): str(v) for k, v in enum_values.items()}

    @staticmethod
    def _render(entity_name: str, symbol_name: str, dict_repr: str) -> str:
        return f'''\
# {entity_name}_regs.py — generated by axion-hdl
# DO NOT EDIT — regenerate with: axion-hdl --python
#
# Import this file in your golden model to get a ready-to-use
# Python register space model without re-parsing source files.
#
# Usage:
#   from {entity_name}_regs import {symbol_name}
#   {symbol_name}.write(0x0000, 0x1)
#   print({symbol_name}.dump())

from axion_hdl.register_model import RegisterSpaceModel

_MODULE_DICT = {dict_repr}

{symbol_name} = RegisterSpaceModel.from_module_dict(_MODULE_DICT)
'''
