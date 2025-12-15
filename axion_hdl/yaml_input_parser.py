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
    
    def _parse_yaml_data(self, data: Dict, filepath: str) -> Optional[Dict]:
        """Parse YAML data structure."""
        module_name = data.get('module')
        if not module_name:
            msg = f"Missing 'module' field in {filepath}"
            print(f"Error: {msg}")
            self.errors.append({'file': filepath, 'msg': msg})
            return None
        
        base_addr_val = data.get('base_addr', '0x0000')
        base_addr = self._parse_address(base_addr_val)
        
        # Parse config
        config = data.get('config', {})
        cdc_en = config.get('cdc_en', False)
        if isinstance(cdc_en, str):
            cdc_en = cdc_en.lower() == 'true'
        cdc_stage = config.get('cdc_stage', 2)
        if isinstance(cdc_stage, str):
            try:
                cdc_stage = int(cdc_stage)
            except ValueError:
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
                    width = 32
            
            # Packed register attributes
            packed_reg_name = reg_data.get('reg_name')
            bit_offset = reg_data.get('bit_offset')
            if bit_offset is not None:
                if isinstance(bit_offset, str):
                    try:
                        bit_offset = int(bit_offset)
                    except ValueError:
                        bit_offset = None
            
            # Default value
            default_val = 0
            default_str = reg_data.get('default')
            if default_str is not None:
                default_val = self._parse_address(default_str)
            
            # If REG_NAME is present, handle packed registers
            if packed_reg_name:
                addr_val = reg_data.get('addr')
                if addr_val is not None:
                    addr = self._parse_address(addr_val)
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
                        default_value=default_val
                    )
                    
                    if addr >= next_auto_addr:
                        next_auto_addr = addr + 4
                        
                except Exception as e:
                    print(f"  Error processing packed register {reg_name}: {e}")
                
                continue
            
            # Standard register
            addr_val = reg_data.get('addr')
            if addr_val is not None:
                addr = self._parse_address(addr_val)
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
                'default_value_hex': f"0x{default_val:X}"
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
                'address': f"0x{packed.address:02X}",
                'address_int': base_addr + packed.address,
                'relative_address': f"0x{packed.address:02X}",
                'reg_name': packed.name,
                'relative_address_int': packed.address,
                'width': 32,
                'signal_type': "std_logic_vector(31 downto 0)",
                'r_strobe': False,
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
            packed_regs_data.append(packed_reg_entry)
        
        # Sort registers by address
        registers.sort(key=lambda x: x['relative_address_int'])
        
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
            'source_file': filepath
        }
    
    def _parse_address(self, addr_val) -> int:
        """Parse address value (hex string, decimal string, or integer)."""
        if isinstance(addr_val, int):
            return addr_val
        
        addr_str = str(addr_val).strip()
        try:
            if addr_str.lower().startswith('0x'):
                return int(addr_str, 16)
            else:
                return int(addr_str)
        except ValueError:
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
