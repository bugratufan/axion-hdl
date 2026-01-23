"""
XML Input Parser Module for Axion HDL

This module parses XML register definition files by first converting them to YAML format,
then using YAMLInputParser for processing. This provides a unified parsing pipeline.

Supports both:
1. Simple custom format: <register_map> with <register> elements
2. SPIRIT/IP-XACT format: <spirit:component> with <spirit:register> elements
"""

import os
import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Set
from pathlib import Path

# Import from axion_hdl
from axion_hdl.address_manager import AddressManager
from axion_hdl.yaml_input_parser import YAMLInputParser

try:
    import yaml
except ImportError:
    yaml = None


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
        self.yaml_parser = YAMLInputParser()
        
        if yaml is None:
            raise ImportError("PyYAML is required for XML input support. Install with: pip install PyYAML")
    
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
        Parse a single XML file by converting to YAML then using YAMLInputParser.
        
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
            
            # Convert XML to YAML structure
            yaml_data = self._xml_to_yaml(root, filepath)
            if not yaml_data:
                return None
            
            # Use YAML parser for processing
            result = self.yaml_parser._parse_yaml_data(yaml_data, filepath)
            
            # Merge errors from YAML parser
            if self.yaml_parser.errors:
                self.errors.extend(self.yaml_parser.errors)
                self.yaml_parser.errors = []
            
            return result
                
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
    
    def _xml_to_yaml(self, root: ET.Element, filepath: str) -> Optional[Dict]:
        """Convert XML structure to YAML dictionary."""
        # Detect format and convert accordingly
        if root.tag.startswith('{http://www.spiritconsortium.org'):
            return self._spirit_to_yaml(root, filepath)
        elif root.tag == 'spirit:component' or 'spirit' in root.tag:
            return self._spirit_to_yaml(root, filepath)
        elif root.tag == 'register_map':
            return self._simple_xml_to_yaml(root, filepath)
        else:
            print(f"  Warning: Unknown XML format in {filepath}: {root.tag}")
            return None
    
    def _simple_xml_to_yaml(self, root: ET.Element, filepath: str) -> Optional[Dict]:
        """Convert simple custom XML format to YAML dictionary."""
        module_name = root.get('module')
        if not module_name:
            msg = f"Missing 'module' attribute in {filepath}"
            print(f"  Error: {msg}")
            self.errors.append({'file': filepath, 'msg': msg})
            return None
        
        base_addr_str = root.get('base_addr', '0x0000')
        
        # Parse config element
        config = {}
        config_elem = root.find('config')
        if config_elem is not None:
            config['cdc_en'] = config_elem.get('cdc_en', '').lower() == 'true'
            cdc_stage_str = config_elem.get('cdc_stage', '2')
            try:
                config['cdc_stage'] = int(cdc_stage_str)
            except ValueError:
                config['cdc_stage'] = 2
        
        # Parse registers
        registers = []
        
        for reg_elem in root.findall('register'):
            reg_name = reg_elem.get('name')
            if not reg_name:
                continue
            
            reg_dict = {
                'name': reg_name,
                'access': reg_elem.get('access', reg_elem.get('mode', 'RW')),
                'description': reg_elem.get('description', '')
            }
            
            # Optional attributes
            if reg_elem.get('addr'):
                reg_dict['addr'] = reg_elem.get('addr')
            if reg_elem.get('width'):
                reg_dict['width'] = reg_elem.get('width')
            if reg_elem.get('reg_name'):
                reg_dict['reg_name'] = reg_elem.get('reg_name')
            if reg_elem.get('bit_offset'):
                reg_dict['bit_offset'] = reg_elem.get('bit_offset')
            if reg_elem.get('default'):
                reg_dict['default'] = reg_elem.get('default')
            if reg_elem.get('r_strobe', '').lower() == 'true':
                reg_dict['r_strobe'] = True
            if reg_elem.get('w_strobe', '').lower() == 'true':
                reg_dict['w_strobe'] = True
            
            registers.append(reg_dict)
        
        return {
            'module': module_name,
            'base_addr': base_addr_str,
            'config': config,
            'registers': registers
        }
    
    def _spirit_to_yaml(self, root: ET.Element, filepath: str) -> Optional[Dict]:
        """Convert SPIRIT/IP-XACT XML format to YAML dictionary."""
        # Handle namespace
        ns = self.SPIRIT_NS
        
        # Try to find module name
        name_elem = root.find('.//spirit:name', ns)
        if name_elem is None:
            name_elem = root.find('.//name')
        
        module_name = name_elem.text if name_elem is not None else None
        if not module_name:
            print(f"  Error: Cannot find module name in SPIRIT format: {filepath}")
            return None
        
        # Find base address
        base_addr_elem = root.find('.//spirit:baseAddress', ns)
        if base_addr_elem is None:
            base_addr_elem = root.find('.//baseAddress')
        
        base_addr_str = '0x0000'
        if base_addr_elem is not None and base_addr_elem.text:
            base_addr_str = base_addr_elem.text
        
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
            
            reg_dict = {'name': reg_name}
            
            if offset_elem is not None and offset_elem.text:
                reg_dict['addr'] = offset_elem.text
            
            # Get access mode
            access_elem = reg_elem.find('spirit:access', ns)
            if access_elem is None:
                access_elem = reg_elem.find('access')
            
            if access_elem is not None and access_elem.text:
                access_map = {
                    'read-only': 'RO',
                    'write-only': 'WO',
                    'read-write': 'RW'
                }
                reg_dict['access'] = access_map.get(access_elem.text.lower(), 'RW')
            
            # Get size/width
            size_elem = reg_elem.find('spirit:size', ns)
            if size_elem is None:
                size_elem = reg_elem.find('size')
            
            if size_elem is not None and size_elem.text:
                reg_dict['width'] = size_elem.text
            
            # Get description
            desc_elem = reg_elem.find('spirit:description', ns)
            if desc_elem is None:
                desc_elem = reg_elem.find('description')
            
            if desc_elem is not None and desc_elem.text:
                reg_dict['description'] = desc_elem.text
            
            # Get strobe attributes (custom extension)
            if reg_elem.get('r_strobe', '').lower() == 'true':
                reg_dict['r_strobe'] = True
            if reg_elem.get('w_strobe', '').lower() == 'true':
                reg_dict['w_strobe'] = True
            
            registers.append(reg_dict)
        
        return {
            'module': module_name,
            'base_addr': base_addr_str,
            'config': {},
            'registers': registers
        }
    
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
