"""
VHDL Parser Module for Axion HDL

This module parses VHDL files and extracts @axion annotations.
Uses axion_hdl for reusable utilities.
"""

import os
import re
from typing import Dict, List, Optional, Tuple

# Import from axion_hdl (unified package)
from axion_hdl.address_manager import AddressManager
from axion_hdl.vhdl_utils import VHDLUtils
from axion_hdl.annotation_parser import AnnotationParser


class VHDLParser:
    """Parser for extracting @axion annotations from VHDL files."""
    
    def __init__(self):
        self.annotation_parser = AnnotationParser(annotation_prefix='@axion')
        self.vhdl_utils = VHDLUtils()
        self.axion_signal_pattern = re.compile(
            r'signal\s+(\w+)\s*:\s*([^;]+);\s*--\s*@axion\s+(.+)'
        )
        
    def parse_vhdl_files(self, source_dirs: List[str]) -> List[Dict]:
        """
        Parse all VHDL files in source directories.
        
        Args:
            source_dirs: List of source directory paths
            
        Returns:
            List of parsed module dictionaries
        """
        modules = []
        
        for src_dir in source_dirs:
            vhdl_files = self._find_vhdl_files(src_dir)
            
            for vhdl_file in vhdl_files:
                module_data = self._parse_vhdl_file(vhdl_file)
                if module_data and module_data['registers']:
                    modules.append(module_data)
                    
        return modules
    
    def _find_vhdl_files(self, directory: str) -> List[str]:
        """Find all VHDL files in directory."""
        vhdl_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.vhd', '.vhdl')):
                    vhdl_files.append(os.path.join(root, file))
        return vhdl_files
    
    def _parse_vhdl_file(self, filepath: str) -> Optional[Dict]:
        """Parse a single VHDL file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Warning: Could not read {filepath}: {e}")
            return None
        
        # Extract entity name using common utilities
        entity_name = self.vhdl_utils.extract_entity_name(content)
        if not entity_name:
            return None
        
        # Parse @axion_def using annotation parser
        cdc_enabled, cdc_stages, base_address = self._parse_axion_def(content)
        
        # Parse signal annotations with base_address offset
        registers = self._parse_signal_annotations(content, base_address)
        
        if not registers:
            return None
            
        return {
            'name': entity_name,
            'file': filepath,
            'cdc_enabled': cdc_enabled,
            'cdc_stages': cdc_stages,
            'base_address': base_address,
            'registers': registers
        }
    
    def _parse_axion_def(self, content: str) -> Tuple[bool, int, int]:
        """Parse @axion_def annotation using common library."""
        attrs = self.annotation_parser.parse_def_annotation(content)
        
        if not attrs:
            return False, 2, 0x00
        
        cdc_enabled = attrs.get('cdc_enabled', False)
        cdc_stages = attrs.get('cdc_stages', 2)
        base_address = attrs.get('base_address', 0x00)
        
        # Ensure base_address is an integer
        if isinstance(base_address, str):
            if base_address.startswith('0x') or base_address.startswith('0X'):
                base_address = int(base_address, 16)
            else:
                base_address = int(base_address)
            
        return cdc_enabled, cdc_stages, base_address
    
    def _parse_signal_annotations(self, content: str, base_address: int = 0x00) -> List[Dict]:
        """
        Parse all @axion signal annotations.
        
        Args:
            content: VHDL file content
            base_address: Base address offset to add to all register addresses
        """
        registers = []
        addr_mgr = AddressManager(start_addr=0x00, alignment=4)
        
        for match in self.axion_signal_pattern.finditer(content):
            signal_name = match.group(1)
            signal_type_str = match.group(2).strip()
            attrs_str = match.group(3).strip()
            
            # Parse signal type using common utilities
            type_name, high_bit, low_bit = self.vhdl_utils.parse_signal_type(signal_type_str)
            signal_type = self.vhdl_utils.format_signal_type(high_bit, low_bit)
            signal_width = high_bit - low_bit + 1
            
            # Info for signals wider than 32 bits
            if signal_width > 32:
                num_regs = (signal_width + 31) // 32
                print(f"INFO: Signal '{signal_name}' is {signal_width} bits wide -> {num_regs} AXI registers allocated.")
            
            # Parse attributes using annotation parser
            attrs = self.annotation_parser.parse_attributes(attrs_str)
            
            # Allocate relative address (with signal width for proper spacing)
            manual_addr = attrs.get('address')
            if manual_addr is not None:
                relative_addr = addr_mgr.allocate_address(manual_addr, signal_width)
            else:
                relative_addr = addr_mgr.allocate_address(signal_width=signal_width)
            
            # Add base address offset to get absolute address
            absolute_addr = base_address + relative_addr
            
            # Build register data
            reg_data = {
                'signal_name': signal_name,
                'signal_type': signal_type,
                'address': addr_mgr.format_address(absolute_addr),
                'address_int': absolute_addr,
                'relative_address': addr_mgr.format_address(relative_addr),
                'relative_address_int': relative_addr,
                'access_mode': attrs.get('access_mode', 'RW'),
                'read_strobe': attrs.get('read_strobe', False),
                'write_strobe': attrs.get('write_strobe', False)
            }
            
            registers.append(reg_data)
                
        return registers
