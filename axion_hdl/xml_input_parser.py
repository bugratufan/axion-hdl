"""
XML Input Parser Module for Axion HDL

This module parses XML register definition files as an alternative input format
to VHDL files with @axion annotations. It supports both:
1. Simple custom format: <register_map> with <register> elements
2. SPIRIT/IP-XACT format: <spirit:component> with <spirit:register> elements

The parser produces the same module dictionary format as VHDLParser for
seamless integration with the rest of Axion-HDL.
"""

import os
import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Set
from pathlib import Path

# Import from axion_hdl
from axion_hdl.address_manager import AddressManager


class XMLInputParser:
    """Parser for XML register definition files.
    
    Supports two XML formats:
    1. Simple custom format (recommended for new projects)
    2. SPIRIT/IP-XACT format (for compatibility with XMLGenerator output)
    
    Example simple format:
        <register_map module="my_module" base_addr="0x0000">
            <config cdc_en="true" cdc_stage="2"/>
            <register name="status" addr="0x00" access="RO" width="32"/>
        </register_map>
    """
    
    # SPIRIT namespace
    SPIRIT_NS = {'spirit': 'http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5'}
    
    def __init__(self):
        self.address_manager = AddressManager()
        self._exclude_patterns: Set[str] = set()
        self.errors = []
    
    def add_exclude(self, pattern: str):
        """Add an exclusion pattern for files/directories."""
        self._exclude_patterns.add(pattern)
    
    def remove_exclude(self, pattern: str):
        """Remove an exclusion pattern."""
        self._exclude_patterns.discard(pattern)
    
    def clear_excludes(self):
        """Clear all exclusion patterns."""
        self._exclude_patterns.clear()
    
    def list_excludes(self) -> List[str]:
        """Return list of exclusion patterns."""
        return list(self._exclude_patterns)
    
    def _is_excluded(self, filepath: str) -> bool:
        """Check if a file path matches any exclusion pattern."""
        import fnmatch
        filename = os.path.basename(filepath)
        
        for pattern in self._exclude_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True
            if fnmatch.fnmatch(filepath, f"*/{pattern}/*"):
                return True
            if fnmatch.fnmatch(filepath, f"*/{pattern}"):
                return True
        return False
    
    def parse_file(self, filepath: str) -> Optional[Dict]:
        """
        Parse a single XML file and return structured module data.
        
        Args:
            filepath: Path to the XML file
            
        Returns:
            Dictionary with module data or None if parsing fails
        """
        print(f"Parsing XML file: {filepath}")
        if not os.path.exists(filepath):
            msg = f"XML file not found: {filepath}"
            print(f"  Warning: {msg}")
            self.errors.append({'file': filepath, 'msg': msg})
            return None
        
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            # Detect format and parse accordingly
            if root.tag.startswith('{http://www.spiritconsortium.org'):
                return self._parse_spirit_format(root, filepath)
            elif root.tag == 'spirit:component' or 'spirit' in root.tag:
                return self._parse_spirit_format(root, filepath)
            elif root.tag == 'register_map':
                return self._parse_simple_format(root, filepath)
            else:
                print(f"  Warning: Unknown XML format in {filepath}: {root.tag}")
                return None
                
        except ET.ParseError as e:
            msg = f"Error parsing XML file {filepath}: {e}"
            print(f"  {msg}")
            self.errors.append({'file': filepath, 'msg': msg})
            return None
        except Exception as e:
            msg = f"Error processing XML file {filepath}: {e}"
            print(f"  {msg}")
            self.errors.append({'file': filepath, 'msg': msg})
            return None
    
    def _parse_simple_format(self, root: ET.Element, filepath: str) -> Optional[Dict]:
        """Parse simple custom XML format."""
        module_name = root.get('module')
        if not module_name:
            msg = f"Missing 'module' attribute in {filepath}"
            print(f"  Error: {msg}")
            self.errors.append({'file': filepath, 'msg': msg})
            return None
        
        base_addr_str = root.get('base_addr', '0x0000')
        base_addr = self._parse_address(base_addr_str)
        
        # Parse config element
        cdc_en = False
        cdc_stage = 2
        config_elem = root.find('config')
        if config_elem is not None:
            cdc_en = config_elem.get('cdc_en', '').lower() == 'true'
            cdc_stage_str = config_elem.get('cdc_stage', '2')
            try:
                cdc_stage = int(cdc_stage_str)
            except ValueError:
                cdc_stage = 2
        
        # Parse registers
        registers = []
        next_auto_addr = 0
        
        # Import from axion_hdl
        from axion_hdl.bit_field_manager import BitFieldManager, BitOverlapError

        bit_field_manager = BitFieldManager()
        
        for reg_elem in root.findall('register'):
            reg_name = reg_elem.get('name')
            if not reg_name:
                continue
            
            # Use 'access' attribute first, fallback to 'mode' if needed
            access = reg_elem.get('access', reg_elem.get('mode', 'RW')).upper()
            if access not in ('RO', 'RW', 'WO'):
                print(f"  Warning: Invalid access mode '{access}' for {reg_name}, using RW")
                access = 'RW'
            
            width_str = reg_elem.get('width', '32')
            try:
                width = int(width_str)
            except ValueError:
                width = 32
            
            # Parse packed register attributes
            packed_reg_name = reg_elem.get('reg_name')  # Grouping name
            bit_offset_str = reg_elem.get('bit_offset')
            bit_offset = None
            if bit_offset_str is not None:
                try:
                    bit_offset = int(bit_offset_str)
                except ValueError:
                    bit_offset = None

            # Parse default value
            default_str = reg_elem.get('default')
            default_val = 0
            if default_str:
                try:
                    if default_str.lower().startswith('0x'):
                        default_val = int(default_str, 16)
                    else:
                        default_val = int(default_str)
                except ValueError:
                    print(f"  Warning: Invalid default value '{default_str}' for {reg_name}, using 0")
            
            # If REG_NAME is present, logic for packed registers
            if packed_reg_name:
                # Get or calculate address for packed register
                addr_str = reg_elem.get('addr')
                if addr_str:
                    addr = self._parse_address(addr_str)
                else:
                    # If this packed register already exists, use its address
                    existing_reg = bit_field_manager.get_register(packed_reg_name)
                    if existing_reg:
                        addr = existing_reg.address
                    else:
                        # New packed register, assign new address
                        # Align to 32-bit (4 byte) boundary
                        addr = (next_auto_addr + 3) & ~3
                
                # Signal type creation (Internal format)
                if width > 1:
                    sig_type = f"[{width-1}:0]"
                else:
                    sig_type = "[0:0]"
                
                try:
                    bit_field_manager.add_field(
                        reg_name=packed_reg_name,
                        address=addr,
                        field_name=reg_name,
                        width=width,
                        access_mode=access,
                        signal_type=sig_type,
                        bit_offset=bit_offset,
                        description=reg_elem.get('description', ''),
                        source_file=filepath,
                        default_value=default_val
                    )
                    
                    # Update next address only if this is a new register at a higher address
                    if addr >= next_auto_addr:
                        next_auto_addr = addr + 4
                        
                except Exception as e:
                     print(f"  Error processing packed register {reg_name}: {e}")
                
                continue  # Skip adding to standard registers list
            
            # Standard Register Logic
            addr_str = reg_elem.get('addr')
            if addr_str:
                addr = self._parse_address(addr_str)
            else:
                addr = next_auto_addr
            
            # Calculate next auto address
            num_regs = (width + 31) // 32
            next_auto_addr = addr + (num_regs * 4)
            
            r_strobe = reg_elem.get('r_strobe', '').lower() == 'true'
            w_strobe = reg_elem.get('w_strobe', '').lower() == 'true'
            description = reg_elem.get('description', '')
            
            register = {
                'signal_name': reg_name,
                'name': reg_name,
                'access_mode': access,
                'access': access,
                'address': f"0x{addr:02X}",
                'address_int': base_addr + addr,
                'relative_address': f"0x{addr:02X}",
                'relative_address_int': addr,
                'width': width,
                'signal_type': f"std_logic_vector({width-1} downto 0)" if width > 1 else "std_logic",
                'r_strobe': r_strobe,
                'w_strobe': w_strobe,
                'read_strobe': r_strobe,
                'write_strobe': w_strobe,
                'description': description,
                'default_value': default_val,
                'default_value_hex': f"0x{default_val:X}",
                'manual_address': bool(addr_str)  # Mark as manual if explicitly defined
            }
            registers.append(register)

        # Process packed registers from BitFieldManager and add them to the list
        packed_regs_data = [] # To store in module data if needed
        
        for packed in bit_field_manager.get_all_registers():
            # Calculate combined default value
            combined_default = 0
            for field in packed.fields:
                mask = ((1 << field.width) - 1)
                field_val = (field.default_value & mask) << field.bit_low
                combined_default |= field_val

            packed_reg_entry = {
                'signal_name': packed.name,
                'name': packed.name,
                'access_mode': packed.access_mode,
                'access': packed.access_mode,
                'address': f"0x{packed.address:02X}",
                'address_int': base_addr + packed.address,
                'relative_address': f"0x{packed.address:02X}",
                'reg_name': packed.name,
                'signal_name': packed.name,     # For consistency
                'name': packed.name,            # For consistency
                'relative_address': f"0x{packed.address:02X}",
                'relative_address_int': packed.address,
                'width': 32, # Packed registers are always 32-bit
                'signal_type': "std_logic_vector(31 downto 0)",
                'r_strobe': False, # Strobe not supported on packed container yet
                'w_strobe': False,
                'read_strobe': False,
                'write_strobe': False,
                'description': f"Packed register: {packed.name}",
                'default_value': combined_default,
                'default_value_hex': f"0x{combined_default:X}",
                'is_packed': True,
                'fields': [
                    {
                        'name': f.name,
                        'bit_low': f.bit_low,
                        'bit_high': f.bit_high,
                        'width': f.width,
                        'access_mode': f.access_mode,
                        'signal_type': f.signal_type,
                        'default_value': f.default_value
                    } for f in packed.fields
                ]
            }
            registers.append(packed_reg_entry)
            packed_regs_data.append(packed_reg_entry) # Track for potential verification

        # Sort registers by address
        registers.sort(key=lambda x: x['relative_address_int'])
        
        return {
            'entity_name': module_name,
            'name': module_name,
            'file': filepath,  # For compatibility with VHDLParser
            'base_address': base_addr,
            'base_addr': base_addr,
            'cdc_enabled': cdc_en,
            'cdc_en': cdc_en,
            'cdc_stages': cdc_stage,
            'cdc_stage': cdc_stage,
            'registers': registers,
            'packed_registers': packed_regs_data,
            'source_file': filepath
        }
    
    def _parse_spirit_format(self, root: ET.Element, filepath: str) -> Optional[Dict]:
        """Parse SPIRIT/IP-XACT XML format (generated by XMLGenerator)."""
        # Handle namespace
        ns = self.SPIRIT_NS
        
        # Try to find module name
        name_elem = root.find('.//spirit:name', ns)
        if name_elem is None:
            # Try without namespace
            name_elem = root.find('.//name')
        
        module_name = name_elem.text if name_elem is not None else None
        if not module_name:
            print(f"  Error: Cannot find module name in SPIRIT format: {filepath}")
            return None
        
        # Find base address
        base_addr_elem = root.find('.//spirit:baseAddress', ns)
        if base_addr_elem is None:
            base_addr_elem = root.find('.//baseAddress')
        
        base_addr = 0
        if base_addr_elem is not None and base_addr_elem.text:
            base_addr = self._parse_address(base_addr_elem.text)
        
        # Parse registers
        registers = []
        reg_elems = root.findall('.//spirit:register', ns)
        if not reg_elems:
            reg_elems = root.findall('.//register')
        
        for reg_elem in reg_elems:
            reg_name_elem = reg_elem.find('spirit:name', ns)
            if reg_name_elem is None:
                reg_name_elem = reg_elem.find('name')
            
            if reg_name_elem is None or not reg_name_elem.text:
                continue
            
            reg_name = reg_name_elem.text
            
            # Get address offset
            offset_elem = reg_elem.find('spirit:addressOffset', ns)
            if offset_elem is None:
                offset_elem = reg_elem.find('addressOffset')
            
            addr = 0
            has_explicit_addr = False
            if offset_elem is not None and offset_elem.text:
                addr = self._parse_address(offset_elem.text)
                has_explicit_addr = True
            
            # Get access mode
            access_elem = reg_elem.find('spirit:access', ns)
            if access_elem is None:
                access_elem = reg_elem.find('access')
            
            access = 'RW'
            if access_elem is not None and access_elem.text:
                access_map = {
                    'read-only': 'RO',
                    'write-only': 'WO',
                    'read-write': 'RW'
                }
                access = access_map.get(access_elem.text.lower(), 'RW')
            
            # Get size/width
            size_elem = reg_elem.find('spirit:size', ns)
            if size_elem is None:
                size_elem = reg_elem.find('size')
            
            width = 32
            if size_elem is not None and size_elem.text:
                try:
                    width = int(size_elem.text)
                except ValueError:
                    width = 32
            
            # Get description
            desc_elem = reg_elem.find('spirit:description', ns)
            if desc_elem is None:
                desc_elem = reg_elem.find('description')
            
            description = desc_elem.text if desc_elem is not None else ''
            
            # Get strobe attributes (custom extension)
            r_strobe = reg_elem.get('r_strobe', '').lower() == 'true'
            w_strobe = reg_elem.get('w_strobe', '').lower() == 'true'
            
            register = {
                'signal_name': reg_name,
                'name': reg_name,
                'access_mode': access,
                'access': access,
                'address': f"0x{addr:02X}",
                'address_int': base_addr + addr,
                'relative_address': f"0x{addr:02X}",
                'relative_address_int': addr,
                'width': width,
                'signal_type': f"std_logic_vector({width-1} downto 0)" if width > 1 else "std_logic",
                'r_strobe': r_strobe,
                'w_strobe': w_strobe,
                'read_strobe': r_strobe,   # Alias for VHDLParser compatibility
                'write_strobe': w_strobe,  # Alias for VHDLParser compatibility
                'description': description or '',
                'manual_address': has_explicit_addr
            }
            registers.append(register)
        
        # CDC is not typically in SPIRIT format, check for custom extension
        cdc_en = False
        cdc_stage = 2
        
        return {
            'entity_name': module_name,
            'name': module_name,
            'file': filepath,  # For compatibility with VHDLParser
            'base_address': base_addr,
            'base_addr': base_addr,
            'cdc_enabled': cdc_en,
            'cdc_en': cdc_en,
            'cdc_stages': cdc_stage,
            'cdc_stage': cdc_stage,
            'registers': registers,
            'source_file': filepath
        }
    
    def _parse_address(self, addr_str: str) -> int:
        """Parse address string (hex or decimal)."""
        addr_str = addr_str.strip()
        try:
            if addr_str.lower().startswith('0x'):
                return int(addr_str, 16)
            else:
                return int(addr_str)
        except ValueError:
            return 0
    
    def parse_xml_files(self, source_dirs: List[str]) -> List[Dict]:
        """
        Parse all XML files in source directories.
        
        Args:
            source_dirs: List of source directory paths
            
        Returns:
            List of parsed module dictionaries
        """
        modules = []
        
        for src_dir in source_dirs:
            if not os.path.isdir(src_dir):
                print(f"  Warning: XML source directory not found: {src_dir}")
                continue
            
            xml_files = self._find_xml_files(src_dir)
            
            for xml_file in xml_files:
                if self._is_excluded(xml_file):
                    print(f"  Skipping excluded: {xml_file}")
                    continue
                
                module = self.parse_file(xml_file)
                if module:
                    modules.append(module)
        
        return modules
    
    def _find_xml_files(self, directory: str) -> List[str]:
        """Find all XML files in directory (recursive)."""
        xml_files = []
        
        for root, dirs, files in os.walk(directory):
            for filename in files:
                if filename.lower().endswith('.xml'):
                    xml_files.append(os.path.join(root, filename))
        
        return sorted(xml_files)
