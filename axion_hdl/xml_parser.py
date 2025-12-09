"""
XML Parser Module for Axion HDL

This module parses XML files (Custom format and IP-XACT) to extract register definitions.
"""

import os
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple

from axion_hdl.address_manager import AddressManager
from axion_hdl.vhdl_utils import VHDLUtils


class XMLParseError(Exception):
    """Exception raised for XML parsing errors."""
    pass

class XMLValidationError(Exception):
    """Exception raised for invalid XML content."""
    pass


class XMLParser:
    """Parser for extracting register definitions from XML files."""

    def __init__(self):
        self.vhdl_utils = VHDLUtils()

    def parse_xml_file(self, filepath: str) -> Optional[Dict]:
        """
        Parse a single XML file and return structured data.
        Detects if format is Custom or IP-XACT.

        Args:
            filepath: Path to the XML file

        Returns:
            Dictionary with parsed data or None if no valid data found.

        Raises:
            XMLParseError: If XML file cannot be parsed
            XMLValidationError: If XML content is invalid
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"XML file not found: {filepath}")

        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
        except ET.ParseError as e:
            raise XMLParseError(f"Error parsing XML file {filepath}: {e}")
        except Exception as e:
            raise XMLParseError(f"Error reading {filepath}: {e}")

        # Detect format based on root tag
        if 'axion_registers' in root.tag:
            return self._parse_custom_xml(root, filepath)
        elif 'component' in root.tag:
            return self._parse_ipxact_xml(root, filepath)
        else:
            raise XMLValidationError(f"Unknown XML format in {filepath}. Root tag: {root.tag}")

    def _parse_custom_xml(self, root: ET.Element, filepath: str) -> Optional[Dict]:
        """Parse Axion custom XML format."""

        module_name = root.get('module', 'unknown_module')
        base_addr_str = root.get('base_address', '0x0000')
        base_address = self._parse_int(base_addr_str)

        # CDC Configuration
        cdc_enabled = False
        cdc_stages = 2
        config_node = root.find('config')
        if config_node is not None:
            cdc_node = config_node.find('cdc')
            if cdc_node is not None:
                cdc_enabled = self._parse_bool(cdc_node.get('enabled', 'false'))
                cdc_stages = int(cdc_node.get('stages', '2'))

        # Registers
        registers = []
        registers_node = root.find('registers')
        if registers_node is not None:
            registers = self._parse_custom_registers(registers_node, base_address, module_name)

        if not registers:
            print(f"Warning: No registers found in {filepath}")

        return {
            'name': module_name,
            'file': filepath,
            'cdc_enabled': cdc_enabled,
            'cdc_stages': cdc_stages,
            'base_address': base_address,
            'registers': registers
        }

    def _parse_custom_registers(self, registers_node: ET.Element, base_address: int, module_name: str) -> List[Dict]:
        """Parse registers from custom XML node."""
        registers = []
        addr_mgr = AddressManager(start_addr=0x00, alignment=4, module_name=module_name)

        for reg_node in registers_node.findall('register'):
            name = reg_node.get('name')
            if not name:
                raise XMLValidationError(f"Register missing 'name' attribute in {module_name}")

            try:
                width = int(reg_node.get('width', '32'))
            except ValueError:
                raise XMLValidationError(f"Invalid width for register '{name}'")

            access = reg_node.get('access', 'RW')
            if access not in ['RO', 'WO', 'RW']:
                 raise XMLValidationError(f"Invalid access mode '{access}' for register '{name}'")
            desc = reg_node.get('description', '')

            # Strobes
            r_strobe = self._parse_bool(reg_node.get('read_strobe', 'false'))
            w_strobe = self._parse_bool(reg_node.get('write_strobe', 'false'))

            # Address
            addr_str = reg_node.get('address')

            # Allocate address
            if addr_str:
                try:
                    addr_val = self._parse_int(addr_str)
                except ValueError:
                     raise XMLValidationError(f"Invalid address '{addr_str}' for register '{name}'")
                relative_addr = addr_mgr.allocate_address(addr_val, width, name)
            else:
                relative_addr = addr_mgr.allocate_address(signal_width=width, signal_name=name)

            absolute_addr = base_address + relative_addr

            # Construct VHDL type string
            if width == 1:
                signal_type = "std_logic"
            else:
                signal_type = f"std_logic_vector({width-1} downto 0)"

            registers.append({
                'signal_name': name,
                'signal_type': signal_type,
                'address': addr_mgr.format_address(absolute_addr),
                'address_int': absolute_addr,
                'relative_address': addr_mgr.format_address(relative_addr),
                'relative_address_int': relative_addr,
                'access_mode': access,
                'read_strobe': r_strobe,
                'write_strobe': w_strobe,
                'description': desc
            })

        return registers

    def _parse_ipxact_xml(self, root: ET.Element, filepath: str) -> Optional[Dict]:
        """Parse basic IP-XACT XML format."""

        # XML Namespace handling for IP-XACT
        # IP-XACT usually has namespaces like {http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009}
        # We'll use a helper to find elements ignoring namespace for simplicity/robustness

        name_node = self._find_any_ns(root, 'name')
        module_name = name_node.text if name_node is not None else 'unknown_module'

        # Memory Maps
        memory_maps = self._find_any_ns(root, 'memoryMaps')
        if memory_maps is None:
            return None

        # Assume first memory map and first address block for now
        memory_map = self._find_any_ns(memory_maps, 'memoryMap')
        if memory_map is None:
            return None

        addr_block = self._find_any_ns(memory_map, 'addressBlock')
        if addr_block is None:
            return None

        base_addr_node = self._find_any_ns(addr_block, 'baseAddress')
        base_address = self._parse_int(base_addr_node.text) if base_addr_node is not None else 0

        # Registers
        registers = []
        addr_mgr = AddressManager(start_addr=0x00, alignment=4, module_name=module_name)

        for reg_node in self._findall_any_ns(addr_block, 'register'):
            name_node = self._find_any_ns(reg_node, 'name')
            name = name_node.text if name_node is not None else 'unknown'

            desc_node = self._find_any_ns(reg_node, 'description')
            desc = desc_node.text if desc_node is not None else ''

            addr_offset_node = self._find_any_ns(reg_node, 'addressOffset')
            addr_offset = self._parse_int(addr_offset_node.text) if addr_offset_node is not None else 0

            size_node = self._find_any_ns(reg_node, 'size')
            width = int(size_node.text) if size_node is not None else 32

            access_node = self._find_any_ns(reg_node, 'access')
            access_str = access_node.text if access_node is not None else 'read-write'

            # Map IP-XACT access to Axion modes
            access_map = {
                'read-write': 'RW',
                'read-only': 'RO',
                'write-only': 'WO',
                'read-writeT': 'RW', # With strobe? Not standard IP-XACT but maybe useful
            }
            access = access_map.get(access_str, 'RW')

            # IP-XACT doesn't standardly define strobes, so default to False
            # Or check vendor extensions if needed. For now, False.
            r_strobe = False
            w_strobe = False

            # Use AddressManager to validate/track address
            relative_addr = addr_mgr.allocate_address(addr_offset, width, name)
            absolute_addr = base_address + relative_addr

            # Construct VHDL type string
            if width == 1:
                signal_type = "std_logic"
            else:
                signal_type = f"std_logic_vector({width-1} downto 0)"

            registers.append({
                'signal_name': name,
                'signal_type': signal_type,
                'address': addr_mgr.format_address(absolute_addr),
                'address_int': absolute_addr,
                'relative_address': addr_mgr.format_address(relative_addr),
                'relative_address_int': relative_addr,
                'access_mode': access,
                'read_strobe': r_strobe,
                'write_strobe': w_strobe,
                'description': desc
            })

        return {
            'name': module_name,
            'file': filepath,
            'cdc_enabled': False, # IP-XACT doesn't standardly define CDC
            'cdc_stages': 2,
            'base_address': base_address,
            'registers': registers
        }

    def _parse_int(self, value: str) -> int:
        """Parse integer from string (hex or decimal)."""
        value = value.strip()
        if value.lower().startswith('0x'):
            return int(value, 16)
        return int(value)

    def _parse_bool(self, value: str) -> bool:
        """Parse boolean from string."""
        return value.lower() in ('true', 'yes', '1')

    def _find_any_ns(self, element: ET.Element, tag: str) -> Optional[ET.Element]:
        """Find child element matching tag, ignoring namespace."""
        for child in element:
            if child.tag.endswith('}' + tag) or child.tag == tag:
                return child
        return None

    def _findall_any_ns(self, element: ET.Element, tag: str) -> List[ET.Element]:
        """Find all children matching tag, ignoring namespace."""
        results = []
        for child in element:
            if child.tag.endswith('}' + tag) or child.tag == tag:
                results.append(child)
        return results
