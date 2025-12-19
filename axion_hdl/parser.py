"""
VHDL Parser Module for Axion HDL

This module parses VHDL files and extracts @axion annotations.
Uses axion_hdl for reusable utilities.
"""

import os
import re
import fnmatch
from typing import Dict, List, Optional, Tuple, Any, Set

# Import from axion_hdl (unified package)
from .address_manager import AddressManager, AddressConflictError # Import specific error
from .vhdl_utils import VHDLUtils
from .annotation_parser import AnnotationParser
from .bit_field_manager import BitFieldManager, BitOverlapError


class VHDLParser:
    """Parser for extracting @axion annotations from VHDL files."""
    
    def __init__(self):
        self.annotation_parser = AnnotationParser(annotation_prefix='@axion')
        self.vhdl_utils = VHDLUtils()
        self.axion_signal_pattern = re.compile(
            r'signal\s+(\w+)\s*:\s*([^;]+);\s*--\s*@axion(?::?)\s+(.+)'
        )
        # Exclusion patterns (files, directories, or glob patterns)
        self.exclude_patterns: Set[str] = set()
        self.errors = []  # Track parsing errors
    
    def parse_file(self, filepath: str) -> Optional[Dict]:
        """
        Parse a single VHDL file and return structured data.
        
        Public API for parsing individual files.
        
        Args:
            filepath: Path to the VHDL file
            
        Returns:
            Dictionary with parsed data or None if no valid data found.
            Keys:
                - entity_name: Name of the VHDL entity
                - signals: List of signal dictionaries with:
                    - name: Signal name
                    - width: Signal bit width  
                    - access: Access mode (RO, RW, WO)
                    - address: Integer address
                    - r_strobe: Read strobe flag
                    - w_strobe: Write strobe flag
                    - description: Signal description
                - base_addr: Base address for the module
                - cdc_en: CDC enabled flag
                - cdc_stage: CDC stage count
        """
        result = self._parse_vhdl_file(filepath)
        if result is None:
            return None
            
        # Convert internal format to test-friendly format
        signals = []
        for reg in result.get('registers', []):
            sig = {
                'name': reg.get('signal_name', ''),
                'width': self._extract_width(reg.get('signal_type', '')),
                'access': reg.get('access_mode', 'RW'),
                'address': reg.get('relative_address_int', 0),
                'r_strobe': reg.get('read_strobe', False),
                'w_strobe': reg.get('write_strobe', False),
                'description': reg.get('description', '')
            }
            signals.append(sig)
        
        return {
            'entity_name': result.get('name'),
            'signals': signals,
            'base_addr': result.get('base_address', 0),
            'cdc_en': result.get('cdc_enabled', False),
            'cdc_stage': result.get('cdc_stages', 2)
        }
    
    def _extract_width(self, signal_type: str) -> int:
        """Extract bit width from signal type string."""
        if signal_type == 'std_logic' or signal_type == '[0:0]':
            return 1
        # Match [high:low] format
        match = re.search(r'\[(\d+):(\d+)\]', signal_type)
        if match:
            high = int(match.group(1))
            low = int(match.group(2))
            return high - low + 1
        # Match (high downto low) format
        match = re.search(r'\((\d+)\s+downto\s+(\d+)\)', signal_type)
        if match:
            high = int(match.group(1))
            low = int(match.group(2))
            return high - low + 1
        return 32  # Default width
        
    def add_exclude(self, pattern: str):
        """
        Add an exclusion pattern.
        
        Patterns can be:
        - File names: "address_conflict_test.vhd"
        - Directory names: "error_cases"
        - Glob patterns: "test_*.vhd", "*_tb.vhd"
        - Path patterns: "tests/error_cases/*"
        
        Args:
            pattern: Pattern to exclude from parsing
        """
        self.exclude_patterns.add(pattern)
        
    def remove_exclude(self, pattern: str):
        """Remove an exclusion pattern."""
        self.exclude_patterns.discard(pattern)
        
    def clear_excludes(self):
        """Clear all exclusion patterns."""
        self.exclude_patterns.clear()
        
    def list_excludes(self) -> List[str]:
        """Return list of exclusion patterns."""
        return sorted(list(self.exclude_patterns))
        
    def _is_excluded(self, filepath: str) -> bool:
        """
        Check if a file path matches any exclusion pattern.
        
        Args:
            filepath: Full path to the file
            
        Returns:
            True if file should be excluded, False otherwise
        """
        if not self.exclude_patterns:
            return False
            
        # Get various forms of the path for matching
        filename = os.path.basename(filepath)
        dirname = os.path.dirname(filepath)
        dir_basename = os.path.basename(dirname)
        
        for pattern in self.exclude_patterns:
            # Check filename match
            if fnmatch.fnmatch(filename, pattern):
                return True
            # Check if pattern matches directory name
            if fnmatch.fnmatch(dir_basename, pattern):
                return True
            # Check if pattern is in the full path
            if pattern in filepath:
                return True
            # Check full path glob match
            if fnmatch.fnmatch(filepath, f"*{pattern}*"):
                return True
                
        return False
        
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
                # Check exclusions
                if self._is_excluded(vhdl_file):
                    continue
                
                try:
                    module_data = self._parse_vhdl_file(vhdl_file)
                    if module_data and module_data['registers']:
                        modules.append(module_data)
                except Exception as e:
                    # Log error but continue with other files
                    msg = f"Error parsing {vhdl_file}: {e}"
                    print(f"Warning: {msg}")
                    self.errors.append({'file': vhdl_file, 'msg': str(e)})
                    
        return modules
    
    def _find_vhdl_files(self, directory: str) -> List[str]:
        """Find all VHDL files in directory (recursive)."""
        vhdl_files = []
        for root, dirs, files in os.walk(directory):
            # Filter out excluded directories to prevent descending into them
            dirs[:] = [d for d in dirs if not self._is_excluded(os.path.join(root, d))]
            
            for file in files:
                if file.endswith(('.vhd', '.vhdl')):
                    vhdl_files.append(os.path.join(root, file))
        return vhdl_files
    
    def _parse_vhdl_file(self, filepath: str) -> Optional[Dict]:
        """Parse a single VHDL file."""
        print(f"Parsing VHDL file: {filepath}")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            msg = f"Could not read {filepath}: {e}"
            print(f"Warning: {msg}")
            self.errors.append({'file': filepath, 'msg': msg})
            return None
        
        # Extract entity name using common utilities
        entity_name = self.vhdl_utils.extract_entity_name(content)
        if not entity_name:
            return None
        
        # Parse @axion_def using annotation parser
        cdc_enabled, cdc_stages, base_address = self._parse_axion_def(content)
        
        # Parse signal annotations with base_address offset
        registers, packed_registers = self._parse_signal_annotations(
            content, base_address, entity_name, filepath
        )
        
        if not registers and not packed_registers:
            return None
            
        return {
            'name': entity_name,
            'file': filepath,
            'cdc_enabled': cdc_enabled,
            'cdc_stages': cdc_stages,
            'base_address': base_address,
            'registers': registers,

            'packed_registers': packed_registers,  # New: subregister groups
            'parsing_errors': self.errors  # Pass accumulated errors to module
        }
    
        return cdc_enabled, cdc_stages, base_address
    
    def _parse_axion_def(self, content: str) -> Tuple[bool, int, int]:
        """Parse @axion_def annotation using common library."""
        # Find ALL matches to handle split definitions
        matches = self.annotation_parser.def_pattern.finditer(content)
        
        attrs = {}
        found_any = False
        
        for match in matches:
            found_any = True
            attrs_str = match.group(1).strip()
            # Merge attributes from this line
            line_attrs = self.annotation_parser.parse_attributes(attrs_str)
            attrs.update(line_attrs)
        
        if not found_any:
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
    
    def _parse_signal_annotations(
        self, 
        content: str, 
        base_address: int = 0x00, 
        module_name: str = "",
        filepath: str = ""
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Parse all @axion signal annotations.
        
        Supports both standalone registers and packed subregisters.
        
        Args:
            content: VHDL file content
            base_address: Base address offset to add to all register addresses
            module_name: Name of the module (for error messages)
            filepath: Source file path (for error messages)
            
        Returns:
            Tuple of (regular_registers, packed_registers)
        """
        registers = []
        addr_mgr = AddressManager(start_addr=0x00, alignment=4, module_name=module_name)
        bit_field_mgr = BitFieldManager()
        
        # Track signals with REG_NAME for grouping
        grouped_signals = {}  # reg_name -> list of (signal_name, attrs, signal_type, width, line_num)
        
        # First pass: collect all signals and identify grouped ones
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            match = self.axion_signal_pattern.search(line)
            if not match:
                continue
                
            signal_name = match.group(1)
            signal_type_str = match.group(2).strip()
            attrs_str = match.group(3).strip()
            
            # Parse signal type using common utilities
            type_name, high_bit, low_bit = self.vhdl_utils.parse_signal_type(signal_type_str)
            signal_type = self.vhdl_utils.format_signal_type(high_bit, low_bit)
            signal_width = high_bit - low_bit + 1
            
            # Parse attributes using annotation parser
            attrs = self.annotation_parser.parse_attributes(attrs_str)
            
            # Check for REG_NAME (subregister grouping)
            reg_name = attrs.get('reg_name')
            
            if reg_name:
                # This signal belongs to a packed register
                if reg_name not in grouped_signals:
                    grouped_signals[reg_name] = []
                grouped_signals[reg_name].append({
                    'signal_name': signal_name,
                    'attrs': attrs,
                    'signal_type': signal_type,
                    'signal_width': signal_width,
                    'line_num': line_num
                })
            else:
                # Regular standalone register (backward compatible)
                # Info for signals wider than 32 bits
                if signal_width > 32:
                    num_regs = (signal_width + 31) // 32
                    print(f"INFO: Signal '{signal_name}' is {signal_width} bits wide -> {num_regs} AXI registers allocated.")
                
                # Allocate relative address (with signal width for proper spacing)
                manual_addr = attrs.get('address')
                if manual_addr is not None:
                    # If manual address is absolute (>= base_address), preserve it by converting to relative
                    # If it's small (offset), use it directly
                    if isinstance(manual_addr, str):
                         if manual_addr.startswith('0x'):
                             manual_addr_int = int(manual_addr, 16)
                         else:
                             manual_addr_int = int(manual_addr)
                    else:
                        manual_addr_int = manual_addr
                        
                    if manual_addr_int >= base_address and base_address > 0:
                        mapped_addr = manual_addr_int - base_address
                    else:
                        mapped_addr = manual_addr_int
                        
                    try:
                        relative_addr = addr_mgr.allocate_address(mapped_addr, signal_width, signal_name)
                    except AddressConflictError as e:
                        print(f"Warning: {e}")
                        self.errors.append({'file': filepath, 'line': line_num, 'msg': str(e)})
                        # Assign special error value or just continue with collision?
                        # Using mapped_addr ensures it appears in the list, even if conflicting
                        relative_addr = mapped_addr 
                else:
                    try:
                        relative_addr = addr_mgr.allocate_address(signal_width=signal_width, signal_name=signal_name)
                    except AddressConflictError as e:
                        print(f"Warning: {e}")
                        self.errors.append({'file': filepath, 'line': line_num, 'msg': str(e)})
                        relative_addr = addr_mgr.get_next_available_address() # Just take next speculative one?
                        # Or perhaps -1 to indicate error? But let's keep it usable for display
                
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
                    'write_strobe': attrs.get('write_strobe', False),
                    'r_strobe': attrs.get('read_strobe', False),
                    'w_strobe': attrs.get('write_strobe', False),
                    'description': attrs.get('description', ''),
                    'default_value': attrs.get('default_value', 0),
                    'manual_address': True if manual_addr is not None else False,
                    'signal_width': signal_width,
                    'width': signal_width  # Standardize on 'width' for modifiers
                }
                
                registers.append(reg_data)
        
        # Second pass: process grouped signals (subregisters)
        packed_registers = []
        
        for reg_name, signals in grouped_signals.items():
            # Get address from first signal
            first_signal = signals[0]
            manual_addr = first_signal['attrs'].get('address')
            
            if manual_addr is not None:
                # Handle absolute vs relative manual address for packed groups
                if isinstance(manual_addr, str):
                     if manual_addr.startswith('0x'):
                         manual_addr_int = int(manual_addr, 16)
                     else:
                         manual_addr_int = int(manual_addr)
                else:
                    manual_addr_int = manual_addr
                    
                if manual_addr_int >= base_address and base_address > 0:
                    mapped_addr = manual_addr_int - base_address
                else:
                    mapped_addr = manual_addr_int
                    
                try:
                    relative_addr = addr_mgr.allocate_address(mapped_addr, 32, reg_name)
                except AddressConflictError as e:
                    print(f"Warning: {e}")
                    self.errors.append({'file': filepath, 'msg': str(e)})
                    relative_addr = mapped_addr
            else:
                try:
                    relative_addr = addr_mgr.allocate_address(signal_width=32, signal_name=reg_name)
                except AddressConflictError as e:
                    print(f"Warning: {e}")
                    self.errors.append({'file': filepath, 'msg': str(e)})
                    relative_addr = addr_mgr.get_next_available_address()
            
            absolute_addr = base_address + relative_addr
            
            # Add each signal as a bit field
            fields = []
            access_mode = None
            
            for sig_info in signals:
                bit_offset = sig_info['attrs'].get('bit_offset')
                field_default = sig_info['attrs'].get('default_value', 0)
                
                try:
                    field = bit_field_mgr.add_field(
                        reg_name=reg_name,
                        address=absolute_addr,
                        field_name=sig_info['signal_name'],
                        width=sig_info['signal_width'],
                        access_mode=sig_info['attrs'].get('access_mode', 'RW'),
                        signal_type=sig_info['signal_type'],
                        bit_offset=bit_offset,
                        description=sig_info['attrs'].get('description', ''),
                        source_file=filepath,
                        source_line=sig_info['line_num'],
                        read_strobe=sig_info['attrs'].get('read_strobe', False),
                        write_strobe=sig_info['attrs'].get('write_strobe', False),
                        default_value=field_default
                    )
                    
                    fields.append({
                        'name': field.name,
                        'bit_low': field.bit_low,
                        'bit_high': field.bit_high,
                        'width': field.width,
                        'access_mode': field.access_mode,
                        'signal_type': field.signal_type,
                        'description': field.description,
                        'read_strobe': field.read_strobe,
                        'write_strobe': field.write_strobe,
                        'mask': field.mask,
                        'default_value': field.default_value
                    })
                    
                    # Use first field's access mode for register
                    if access_mode is None:
                        access_mode = field.access_mode
                        
                except BitOverlapError as e:
                    # Re-raise with context
                    raise e
            
            # Sort fields by bit position
            fields.sort(key=lambda f: f['bit_low'])
            
            # Calculate combined default value from all fields
            combined_default = 0
            for f in fields:
                # Shift field's default value to its bit position
                field_val = f['default_value'] & ((1 << f['width']) - 1)  # Mask to width
                combined_default |= (field_val << f['bit_low'])
            
            packed_reg = {
                'reg_name': reg_name,
                'signal_name': reg_name,  # For compatibility
                'signal_type': '[31:0]',
                'address': addr_mgr.format_address(absolute_addr),
                'address_int': absolute_addr,
                'relative_address': addr_mgr.format_address(relative_addr),
                'relative_address_int': relative_addr,
                'access_mode': access_mode or 'RW',
                'fields': fields,
                'is_packed': True,
                'default_value': combined_default,
                'signal_width': 32
            }
            
            packed_registers.append(packed_reg)
        
        return registers, packed_registers

