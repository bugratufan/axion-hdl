"""
YAML Input Parser Module for Axion HDL

This module parses YAML register definition files as an alternative input format
to VHDL files with @axion annotations or XML files.

The parser produces the same module dictionary format as VHDLParser and XMLInputParser
for seamless integration with the rest of Axion-HDL.
"""

import os
import fnmatch
from typing import Dict, List, Optional, Set

try:
    import yaml
except ImportError:
    yaml = None

# Import from axion_hdl
from axion_hdl.address_manager import AddressManager


class YAMLInputParser:
    """Parser for YAML register definition files.
    
    Supports YAML format matching the XML simple format structure:
    
    Example format:
        module: my_module
        base_addr: "0x0000"
        config:
          cdc_en: true
          cdc_stage: 2
        registers:
          - name: status
            addr: "0x00"
            access: RO
            width: 32
            description: Status register
    """
    
    def __init__(self):
        self.address_manager = AddressManager()
        self._exclude_patterns: Set[str] = set()
        self.errors = []  # Track parsing errors
        
        if yaml is None:
            raise ImportError("PyYAML is required for YAML input support. Install with: pip install PyYAML")

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
        Parse a single YAML file and return structured module data.
        
        Args:
            filepath: Path to the YAML file
            
        Returns:
            Dictionary with module data or None if parsing fails
        """
        print(f"Parsing YAML file: {filepath}")
        if not os.path.exists(filepath):
            msg = f"YAML file not found: {filepath}"
            print(f"  Warning: {msg}")
            self.errors.append({'file': filepath, 'msg': msg})
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                print(f"  Warning: Empty YAML file: {filepath}")
                return None
            
            return self._parse_yaml_data(data, filepath)
            
        except yaml.YAMLError as e:
            msg = f"YAML syntax error: {e}"
            print(f"  Error parsing YAML file {filepath}: {msg}")
            self.errors.append({'file': filepath, 'msg': msg})
            return None
        except Exception as e:
            msg = str(e)
            print(f"  Error processing YAML file {filepath}: {msg}")
            self.errors.append({'file': filepath, 'msg': msg})
            return None
    
    def parse_data(self, data: Dict, filepath: str) -> Optional[Dict]:
        """
        Parse a dictionary data structure (from YAML, JSON, or converted XML).
        
        This is the public API for parsing already-loaded data structures.
        Use this method when you have data loaded from any format that matches
        the expected YAML structure.
        
        Args:
            data: Dictionary with module, registers, etc.
            filepath: Source file path for error reporting
            
        Returns:
            Dictionary with module data or None if parsing fails
        """
        return self._parse_yaml_data(data, filepath)
    
    def _parse_yaml_data(self, data: Dict, filepath: str) -> Optional[Dict]:
        """Parse YAML data structure (internal implementation)."""
        # Store current file for _parse_address error reporting
        self._current_file = filepath
        
        module_name = data.get('module')
        if not module_name:
            msg = f"Missing 'module' field in {filepath}"
            print(f"Error: {msg}")
            self.errors.append({'file': filepath, 'msg': msg})
            return None
        
        base_addr_val = data.get('base_addr', '0x0000')
        base_addr = self._parse_address(base_addr_val, context=f"module '{module_name}' base_addr")
        
        # Parse config
        config = data.get('config', {})
        
        # Check config block first, then top-level
        cdc_en = config.get('cdc_en')
        if cdc_en is None:
            cdc_en = config.get('cdc_enabled')
        if cdc_en is None:
            cdc_en = data.get('cdc_en')
        if cdc_en is None:
            cdc_en = data.get('cdc_enabled', False)
        if isinstance(cdc_en, str):
            cdc_en = cdc_en.lower() == 'true'
            
        # Check config block first, then top-level for stages
        cdc_stage = config.get('cdc_stage')
        if cdc_stage is None:
            cdc_stage = config.get('cdc_stages')
        if cdc_stage is None:
            cdc_stage = data.get('cdc_stage')
        if cdc_stage is None:
            cdc_stage = data.get('cdc_stages', 2)
            
        if isinstance(cdc_stage, str):
            try:
                cdc_stage = int(cdc_stage)
            except ValueError:
                self.errors.append({'file': filepath, 'msg': f"Invalid cdc_stage value '{cdc_stage}' in module '{module_name}', using default 2"})
                cdc_stage = 2
        
        # Parse registers
        registers = []
        next_auto_addr = 0
        
        # Import BitFieldManager for packed registers
        from axion_hdl.bit_field_manager import BitFieldManager
        bit_field_manager = BitFieldManager()
        
        for reg_data in data.get('registers', []):
            reg_name = reg_data.get('name')
            if not reg_name:
                continue
            
            # Access mode
            access = str(reg_data.get('access', 'RW')).upper()
            if access not in ('RO', 'RW', 'WO'):
                print(f"  Warning: Invalid access mode '{access}' for {reg_name}, using RW")
                access = 'RW'
            
            # Width
            width = reg_data.get('width', 32)
            if isinstance(width, str):
                try:
                    width = int(width)
                except ValueError:
                    self.errors.append({'file': filepath, 'msg': f"Invalid width value '{width}' for register '{reg_name}', using default 32"})
                    width = 32

            # Check if this register has packed fields (fields: array format)
            fields_list = reg_data.get('fields')
            if fields_list:
                # Process packed register with fields array
                addr_val = reg_data.get('addr')
                if addr_val is not None:
                    addr = self._parse_address(addr_val, context=f"register '{reg_name}' addr")
                else:
                    addr = next_auto_addr

                # Process each field
                for field_data in fields_list:
                    field_name = field_data.get('name')
                    if not field_name:
                        continue

                    field_width = field_data.get('width', 1)
                    if isinstance(field_width, str):
                        try:
                            field_width = int(field_width)
                        except ValueError:
                            self.errors.append({'file': filepath, 'msg': f"Invalid width value '{field_width}' for field '{field_name}' in register '{reg_name}', using default 1"})
                            field_width = 1

                    field_access = str(field_data.get('access', access)).upper()
                    if field_access not in ('RO', 'RW', 'WO'):
                        field_access = access

                    field_bit_offset = field_data.get('bit_offset')
                    if field_bit_offset is not None:
                        if isinstance(field_bit_offset, str):
                            try:
                                field_bit_offset = int(field_bit_offset)
                            except ValueError:
                                self.errors.append({'file': filepath, 'msg': f"Invalid bit_offset value '{field_bit_offset}' for field '{field_name}' in register '{reg_name}'"})
                                field_bit_offset = None

                    field_default_val = 0
                    field_default_str = field_data.get('default')
                    if field_default_str is not None:
                        field_default_val = self._parse_address(field_default_str, context=f"field '{field_name}' default value")

                    if field_width > 1:
                        sig_type = f"[{field_width-1}:0]"
                    else:
                        sig_type = "[0:0]"

                    # Parse enum_values: YAML may deliver int keys directly or str keys
                    raw_enum = field_data.get('enum_values')
                    parsed_enum = None
                    if isinstance(raw_enum, dict) and raw_enum:
                        parsed_enum = {}
                        for k, v in raw_enum.items():
                            try:
                                if isinstance(k, int):
                                    parsed_enum[k] = str(v)
                                else:
                                    parsed_enum[int(str(k), 0)] = str(v)
                            except (ValueError, TypeError):
                                pass
                        if not parsed_enum:
                            parsed_enum = None

                    try:
                        bit_field_manager.add_field(
                            reg_name=reg_name,
                            address=addr,
                            field_name=field_name,
                            width=field_width,
                            access_mode=field_access,
                            signal_type=sig_type,
                            bit_offset=field_bit_offset,
                            description=field_data.get('description', ''),
                            source_file=filepath,
                            default_value=field_default_val,
                            read_strobe=field_data.get('r_strobe', False),
                            write_strobe=field_data.get('w_strobe', False),
                            allow_overlap=True,
                            enum_values=parsed_enum
                        )
                    except Exception as e:
                        msg = f"Error processing field {field_name} in {reg_name}: {e}"
                        print(f"  {msg}")
                        self.errors.append({'file': filepath, 'msg': msg})

                if addr >= next_auto_addr:
                    next_auto_addr = addr + 4

                continue

            # Packed register attributes (legacy reg_name format)
            packed_reg_name = reg_data.get('reg_name')
            bit_offset = reg_data.get('bit_offset')
            if bit_offset is not None:
                if isinstance(bit_offset, str):
                    try:
                        bit_offset = int(bit_offset)
                    except ValueError:
                        self.errors.append({'file': filepath, 'msg': f"Invalid bit_offset value '{bit_offset}' for register '{reg_name}'"})
                        bit_offset = None
            
            # Default value
            default_val = 0
            default_str = reg_data.get('default')
            if default_str is not None:
                default_val = self._parse_address(default_str, context=f"register '{reg_name}' default value")
            
            # If REG_NAME is present, handle packed registers
            if packed_reg_name:
                addr_val = reg_data.get('addr')
                if addr_val is not None:
                    addr = self._parse_address(addr_val, context=f"register '{reg_name}' addr")
                else:
                    existing_reg = bit_field_manager.get_register(packed_reg_name)
                    if existing_reg:
                        addr = existing_reg.address
                    else:
                        addr = (next_auto_addr + 3) & ~3
                
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
                        description=reg_data.get('description', ''),
                        source_file=filepath,
                        default_value=default_val,
                        read_strobe=reg_data.get('r_strobe', False),
                        write_strobe=reg_data.get('w_strobe', False),
                        allow_overlap=True  # Allow overlaps, RuleChecker will validate
                    )
                    
                    if addr >= next_auto_addr:
                        next_auto_addr = addr + 4
                        
                except Exception as e:
                    msg = f"Error processing packed register {reg_name}: {e}"
                    print(f"  {msg}")
                    self.errors.append({'file': filepath, 'msg': msg})
                
                continue
            
            # Standard register
            addr_val = reg_data.get('addr')
            if addr_val is not None:
                addr = self._parse_address(addr_val, context=f"register '{reg_name}' addr")
            else:
                addr = next_auto_addr
            
            # Calculate next auto address
            num_regs = (width + 31) // 32
            next_auto_addr = addr + (num_regs * 4)
            
            r_strobe = reg_data.get('r_strobe', False)
            w_strobe = reg_data.get('w_strobe', False)
            if isinstance(r_strobe, str):
                r_strobe = r_strobe.lower() == 'true'
            if isinstance(w_strobe, str):
                w_strobe = w_strobe.lower() == 'true'
            description = reg_data.get('description', '')
            
            # Parse enum_values for standalone registers (flat XML or direct YAML)
            raw_enum = reg_data.get('enum_values')
            parsed_enum = None
            if isinstance(raw_enum, dict) and raw_enum:
                parsed_enum = {}
                for k, v in raw_enum.items():
                    try:
                        if isinstance(k, int):
                            parsed_enum[k] = str(v)
                        else:
                            parsed_enum[int(str(k), 0)] = str(v)
                    except (ValueError, TypeError):
                        pass
                if not parsed_enum:
                    parsed_enum = None

            register = {
                'signal_name': reg_name,
                'name': reg_name,
                'access_mode': access,
                'access': access,
                'address': f"0x{base_addr + addr:02X}",
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
                'enum_values': parsed_enum
            }
            registers.append(register)
        
        # Process packed registers
        packed_regs_data = []
        
        for packed in bit_field_manager.get_all_registers():
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
                'address': f"0x{base_addr + packed.address:02X}",
                'address_int': base_addr + packed.address,
                'relative_address': f"0x{packed.address:02X}",
                'reg_name': packed.name,
                'relative_address_int': packed.address,
                'width': 32,
                'signal_type': "std_logic_vector(31 downto 0)",
                'r_strobe': any(f.read_strobe for f in packed.fields),
                'w_strobe': any(f.write_strobe for f in packed.fields),
                'read_strobe': any(f.read_strobe for f in packed.fields),
                'write_strobe': any(f.write_strobe for f in packed.fields),
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
                        'default_value': f.default_value,
                        'read_strobe': f.read_strobe,
                        'write_strobe': f.write_strobe,
                        'description': f.description,
                        'enum_values': f.enum_values
                    } for f in packed.fields
                ]
            }
            registers.append(packed_reg_entry)
            packed_regs_data.append(packed_reg_entry)
        
        # Sort registers by address
        registers.sort(key=lambda x: x['relative_address_int'])
        
        # Collect errors for this module
        module_errors = [e for e in self.errors if e.get('file') == filepath]
        
        return {
            'entity_name': module_name,
            'name': module_name,
            'file': filepath,
            'base_address': base_addr,
            'base_addr': base_addr,
            'cdc_enabled': cdc_en,
            'cdc_en': cdc_en,
            'cdc_stages': cdc_stage,
            'cdc_stage': cdc_stage,
            'registers': registers,
            'packed_registers': packed_regs_data,
            'source_file': filepath,
            'parsing_errors': module_errors
        }
    
    def _parse_address(self, addr_val, context: str = "") -> int:
        """
        Parse address value (hex string, decimal string, or integer).
        
        Args:
            addr_val: Value to parse
            context: Context for error reporting (e.g., register name)
            
        Returns:
            Parsed integer or 0 if parsing fails (after recording error)
        """
        if isinstance(addr_val, int):
            return addr_val
        
        addr_str = str(addr_val).strip()
        try:
            if addr_str.lower().startswith('0x'):
                return int(addr_str, 16)
            else:
                return int(addr_str)
        except ValueError:
            msg = f"Invalid numeric value '{addr_val}'"
            if context:
                msg += f" in {context}"
            # We still return 0 to allow parsing to continue, 
            # but we've recorded the error
            self.errors.append({'file': getattr(self, '_current_file', 'Unknown'), 'msg': msg})
            return 0
    
    def parse_yaml_files(self, source_dirs: List[str]) -> List[Dict]:
        """
        Parse all YAML files in source directories.
        
        Args:
            source_dirs: List of source directory paths
            
        Returns:
            List of parsed module dictionaries
        """
        modules = []
        
        for src_dir in source_dirs:
            if not os.path.isdir(src_dir):
                print(f"  Warning: YAML source directory not found: {src_dir}")
                continue
            
            yaml_files = self._find_yaml_files(src_dir)
            
            for yaml_file in yaml_files:
                if self._is_excluded(yaml_file):
                    print(f"  Skipping excluded: {yaml_file}")
                    continue
                
                module = self.parse_file(yaml_file)
                if module:
                    modules.append(module)
        
        return modules
    
    def _find_yaml_files(self, directory: str) -> List[str]:
        """Find all YAML files in directory (recursive)."""
        yaml_files = []
        
        for root, dirs, files in os.walk(directory):
            for filename in files:
                if filename.lower().endswith(('.yaml', '.yml')):
                    yaml_files.append(os.path.join(root, filename))
        
        return sorted(yaml_files)
