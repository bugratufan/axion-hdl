"""
SystemVerilog Parser Module for Axion HDL

This module parses SystemVerilog files and extracts @axion annotations.
Equivalent to parser.py but for SystemVerilog syntax.
"""

import os
import re
import fnmatch
from typing import Dict, List, Optional, Tuple, Any, Set

# Import from axion_hdl (unified package)
from .address_manager import AddressManager, AddressConflictError
from .systemverilog_utils import SystemVerilogUtils
from .annotation_parser import AnnotationParser
from .bit_field_manager import BitFieldManager, BitOverlapError


class SystemVerilogParser:
    """Parser for extracting @axion annotations from SystemVerilog files."""

    def __init__(self):
        self.annotation_parser = AnnotationParser(annotation_prefix='@axion')
        self.sv_utils = SystemVerilogUtils()

        # Pattern for signal with annotation
        # Matches: logic [31:0] status; // @axion RO DESC="Status register"
        self.axion_signal_pattern = re.compile(
            r'(logic|reg|wire)\s*(\[[^\]]+\])?\s+(\w+)\s*;\s*//\s*@axion(?::?)(?:\s+(.*))?',
            re.IGNORECASE
        )

        # Exclusion patterns (files, directories, or glob patterns)
        self.exclude_patterns: Set[str] = set()
        self.errors = []  # Track parsing errors

    def parse_file(self, filepath: str) -> Optional[Dict]:
        """
        Parse a single SystemVerilog file and return structured data.

        Public API for parsing individual files.

        Args:
            filepath: Path to the SystemVerilog file

        Returns:
            Optional[Dict]: Dictionary with parsed data or None if no valid data found.
            
            The dictionary keys include:
            - name: Name of the SystemVerilog module
            - file: Path to source file
            - signals: List of signal dictionaries
            - registers: List of register dictionaries
            - base_address: Base address for the module
            - cdc_enabled: CDC enabled flag
            - cdc_stages: CDC stage count
        """
        result = self._parse_sv_file(filepath)
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
                'description': reg.get('description', ''),
                'is_packed': reg.get('is_packed', False)
            }
            signals.append(sig)

        return {
            'name': result.get('name'),
            'file': result.get('file'),
            'signals': signals,
            'registers': result.get('registers', []),
            'base_address': result.get('base_address', 0),  # Use full name for tests
            'base_addr': result.get('base_address', 0),      # Keep for compatibility
            'cdc_enabled': result.get('cdc_enabled', False), # Use full name for tests
            'cdc_en': result.get('cdc_enabled', False),      # Keep for compatibility
            'cdc_stages': result.get('cdc_stages', 2),       # Use full name for tests
            'cdc_stage': result.get('cdc_stages', 2),        # Keep for compatibility
            'packed_registers': result.get('packed_registers', [])
        }

    def _extract_width(self, signal_type: str) -> int:
        """Extract bit width from signal type string."""
        if not signal_type or signal_type in ['logic', 'reg', 'wire', '[0:0]']:
            return 1
        # Match [high:low] format
        match = re.search(r'\[(\d+):(\d+)\]', signal_type)
        if match:
            high = int(match.group(1))
            low = int(match.group(2))
            return abs(high - low) + 1
        return 1

    def _parse_sv_file(self, filepath: str) -> Optional[Dict]:
        """
        Internal implementation of SystemVerilog file parsing.

        Args:
            filepath: Path to SystemVerilog file

        Returns:
            Parsed data dictionary or None
        """
        if not os.path.exists(filepath):
            self.errors.append(f"File not found: {filepath}")
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.errors.append(f"Error reading file {filepath}: {e}")
            return None

        # Extract module name
        module_name = self.sv_utils.extract_module_name(content)
        if not module_name:
            self.errors.append(f"No module declaration found in {filepath}")
            return None

        # Parse module-level definitions (@axion_def)
        module_config = self._parse_module_config(content)

        # Parse signal-level annotations
        registers = self._parse_signals(content, module_config)

        if not registers:
            # No annotated signals found
            return None

        return {
            'name': module_name,
            'file': filepath,
            'source_type': 'systemverilog',
            'base_address': module_config.get('base_address', 0),
            'cdc_enabled': module_config.get('cdc_enabled', False),
            'cdc_stages': module_config.get('cdc_stages', 2),
            'registers': registers,
            'packed_registers': module_config.get('packed_registers', [])
        }

    def _parse_module_config(self, content: str) -> Dict:
        """
        Parse module-level @axion_def configuration.

        Looks for lines like:
            // @axion_def BASE_ADDR=0x1000 CDC_EN CDC_STAGE=3

        Args:
            content: File content

        Returns:
            Configuration dictionary with keys:
                - base_address: Base address (int)
                - cdc_enabled: CDC enable flag (bool)
                - cdc_stages: CDC stages (int)
                - packed_registers: List of packed register definitions
        """
        config = {
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'packed_registers': []
        }

        # Pattern for @axion_def
        def_pattern = re.compile(
            r'//\s*@axion_def\s+(.+)',
            re.IGNORECASE
        )

        for line in content.split('\n'):
            match = def_pattern.search(line)
            if match:
                attrs_str = match.group(1).strip()
                attrs = self.annotation_parser.parse_attributes(attrs_str)

                # Process attributes (AnnotationParser already converts these to standardized names)
                if 'base_address' in attrs:
                    config['base_address'] = attrs['base_address']

                if 'cdc_enabled' in attrs:
                    config['cdc_enabled'] = attrs['cdc_enabled']

                if 'cdc_stages' in attrs:
                    config['cdc_stages'] = attrs['cdc_stages']

                # Check for packed register definitions (AnnotationParser normalizes to lowercase)
                if 'pack' in attrs or 'PACK' in attrs:
                    config['packed_registers'].append(attrs)

        return config

    def _parse_signals(self, content: str, module_config: Dict) -> List[Dict]:
        """
        Parse signal-level @axion annotations.

        Args:
            content: File content
            module_config: Module configuration from @axion_def

        Returns:
            List of register dictionaries
        """
        registers = []
        address_manager = AddressManager(start_addr=module_config['base_address'])
        bit_field_manager = BitFieldManager()

        # Find all annotated signals
        for match in self.axion_signal_pattern.finditer(content):
            signal_base_type = match.group(1)  # logic, reg, or wire
            signal_range = match.group(2)  # [31:0] or None
            signal_name = match.group(3)
            annotation_str = (match.group(4) or '').strip()

            # Parse annotation attributes
            attrs = self.annotation_parser.parse_attributes(annotation_str)

            # Determine signal type in internal format
            if signal_range:
                # Extract range [high:low]
                range_match = re.search(r'\[(\d+):(\d+)\]', signal_range)
                if range_match:
                    high = int(range_match.group(1))
                    low = int(range_match.group(2))
                    signal_type = f"[{high}:{low}]"
                    signal_width = abs(high - low) + 1
                else:
                    signal_type = "[0:0]"
                    signal_width = 1
            else:
                # Single-bit signal
                signal_type = "[0:0]"
                signal_width = 1

            # Parse access mode (default: RW)
            access_mode = attrs.get('access_mode', 'RW').upper()
            if access_mode not in ['RO', 'WO', 'RW']:
                self.errors.append(f"Invalid access mode '{access_mode}' for signal {signal_name}")
                access_mode = 'RW'

            # Parse strobes (AnnotationParser returns standardized names)
            read_strobe = attrs.get('read_strobe', False)
            write_strobe = attrs.get('write_strobe', False)

            # Parse description (AnnotationParser returns standardized name)
            description = attrs.get('description', '')

            # Handle address allocation (AnnotationParser returns standardized name and converts to int)
            if 'address' in attrs:
                # Manual address (already converted to int by AnnotationParser)
                try:
                    manual_addr = attrs['address']

                    try:
                        address_int = address_manager.allocate_address(manual_addr, signal_width, signal_name)
                    except AddressConflictError as e:
                        self.errors.append(str(e))
                        # Re-allocate so the address is properly tracked
                        try:
                            address_int = address_manager.allocate_address(
                                address_manager.get_next_available_address(),
                                signal_width,
                                signal_name
                            )
                        except AddressConflictError:
                            address_int = address_manager.get_next_available_address()
                except (ValueError, TypeError):
                    self.errors.append(f"Invalid address value: {attrs.get('address', attrs.get('ADDR', '?'))}")
                    continue
            else:
                # Auto-allocate address
                try:
                    address_int = address_manager.allocate_address(signal_width=signal_width, signal_name=signal_name)
                except AddressConflictError as e:
                    self.errors.append(str(e))
                    continue

            # Check for bit field (packed register) annotation
            is_packed = False
            bit_range = None
            parent_register = None

            if 'bits' in attrs or 'BITS' in attrs:
                is_packed = True
                # Parse bit range (AnnotationParser normalizes to lowercase)
                bits_str = attrs.get('bits', attrs.get('BITS', ''))
                bit_match = re.match(r'(\d+):(\d+)', bits_str)
                if bit_match:
                    bit_high = int(bit_match.group(1))
                    bit_low = int(bit_match.group(2))
                    bit_range = (bit_high, bit_low)

                    # Find parent register (normalized key is 'reg')
                    parent_register = attrs.get('reg', attrs.get('REG', signal_name))

                    try:
                        bit_field_manager.allocate_bits(
                            parent_register,
                            signal_name,
                            bit_high,
                            bit_low
                        )
                    except BitOverlapError as e:
                        self.errors.append(str(e))
                        continue

            # Build register dictionary
            register = {
                'signal_name': signal_name,
                'signal_type': signal_type,
                'signal_width': signal_width,
                'access_mode': access_mode,
                'read_strobe': read_strobe,
                'write_strobe': write_strobe,
                'description': description,
                'default_value': attrs.get('default_value'),
                'address': f"0x{address_int:08X}",
                'address_int': address_int,
                'relative_address_int': address_int - module_config['base_address'],
                'is_packed': is_packed,
                'bit_range': bit_range,
                'parent_register': parent_register,
                'width': signal_width
            }

            registers.append(register)

        return registers

    def add_exclude_pattern(self, pattern: str):
        """
        Add a file or directory pattern to exclude from parsing.

        Args:
            pattern: Glob pattern, directory path, or filename
        """
        self.exclude_patterns.add(pattern)

    def _is_excluded(self, filepath: str) -> bool:
        """
        Check if a file should be excluded from parsing.

        Args:
            filepath: Path to check

        Returns:
            True if excluded, False otherwise
        """
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(filepath, pattern):
                return True
            if os.path.isdir(pattern) and filepath.startswith(pattern):
                return True
        return False

    def get_errors(self) -> List[str]:
        """
        Get list of parsing errors.

        Returns:
            List of error messages
        """
        return self.errors.copy()

    def clear_errors(self):
        """Clear the error list."""
        self.errors.clear()
