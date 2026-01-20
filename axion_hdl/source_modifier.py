import os
import re
import difflib
from typing import List, Dict, Tuple, Optional
from .annotation_parser import AnnotationParser

class SourceModifier:
    def __init__(self, axion_instance):
        self.axion = axion_instance
        self.annotation_parser = AnnotationParser()

    def _generate_axion_tag(self, reg: Dict, existing_tag_content: str = None) -> str:
        """
        Generate the @axion attribute string (comment content).
        Preserves attribute order from existing tag if provided.
        """
        # 1. Collect all current values
        current_values = {}
        
        # Access
        current_values['ACCESS'] = reg.get('access', 'RW')
        
        # Address
        addr_val = reg.get('address')
        if addr_val:
            if isinstance(addr_val, str) and not addr_val.lower().startswith('0x'):
                 try:
                     val_int = int(addr_val)
                     current_values['ADDR'] = f"0x{val_int:X}"
                 except ValueError:
                     current_values['ADDR'] = addr_val
            else:
                 current_values['ADDR'] = addr_val
        elif existing_tag_content:
             addr_match = re.search(r'ADDR=(0x[0-9A-F]+)', existing_tag_content, re.IGNORECASE)
             if addr_match:
                 current_values['ADDR'] = addr_match.group(1)

        # Default
        default_val = reg.get('default_value')
        if default_val is not None:
             if isinstance(default_val, str) and default_val.strip().isdigit():
                 default_val = int(default_val.strip())
        
        if default_val and default_val != '0' and default_val != 0 and default_val != '0x0':
            if isinstance(default_val, int):
                width = int(reg.get('width', 32))
                nibbles = (width + 3) // 4
                current_values['DEFAULT'] = f"0x{default_val:0{nibbles}X}"
            else:
                 current_values['DEFAULT'] = default_val
        elif (default_val == 0 or default_val == '0') and existing_tag_content:
             if re.search(r'\bDEFAULT=(0|0x0)\b', existing_tag_content, re.IGNORECASE):
                  current_values['DEFAULT'] = "0"

        # Description
        desc = reg.get('description')
        if desc:
            current_values['DESC'] = f'"{desc}"'

        # Strobes (Flags)
        if reg.get('read_strobe') or reg.get('r_strobe'):
            current_values['R_STROBE'] = True
        if reg.get('write_strobe') or reg.get('w_strobe'):
            current_values['W_STROBE'] = True

        # Reg Name & Bit Offset
        reg_name = reg.get('reg_name')
        if reg_name and reg.get('is_packed_field'):
            current_values['REG_NAME'] = reg_name
        elif existing_tag_content:
            match = re.search(r'REG_NAME=(\w+)', existing_tag_content, re.IGNORECASE)
            if match: current_values['REG_NAME'] = match.group(1)
            
        bit_offset = reg.get('bit_offset')
        if bit_offset is not None and reg.get('is_packed_field'):
            current_values['BIT_OFFSET'] = bit_offset
        elif existing_tag_content:
            match = re.search(r'BIT_OFFSET=(\d+)', existing_tag_content, re.IGNORECASE)
            if match: current_values['BIT_OFFSET'] = match.group(1)

        # 2. Parse existing tag to find ORDER and CUSTOM attributes
        ordered_keys = []
        custom_attrs = {}
        
        if existing_tag_content:
            # Tokenize by splitting on spaces, but respect quotes
            # A simple regex to find keys: valid_key(=value)?
            # We want to find the sequence of keys
            
            # Helper to normalize key
            def normalize(k): return k.upper()

            # Parse the content using AnnotationParser to get all raw keys
            dummy_line = f"-- @axion {existing_tag_content}" if not existing_tag_content.strip().startswith("--") else existing_tag_content
            parsed = self.annotation_parser.parse_annotation(dummy_line)
            
            # Re-scan invalid string to find approximate position of each key
            # This is complex because python dict is unordered in older versions and parser might change case
            # Better approach: Scan the string for known keys + collected custom keys
            
            found_indices = []
            
            # Standard known keys mapping
            std_map = {
                'RO': 'ACCESS', 'RW': 'ACCESS', 'WO': 'ACCESS',
                'ADDR': 'ADDR', 'DEFAULT': 'DEFAULT', 'DESC': 'DESC',
                'R_STROBE': 'R_STROBE', 'W_STROBE': 'W_STROBE',
                'REG_NAME': 'REG_NAME', 'BIT_OFFSET': 'BIT_OFFSET'
            }
            
            # Find positions of standard keys
            for key_in_text, canonical_key in std_map.items():
                # For ACCESS modes (RO/RW/WO), they are values but act like keys
                matches = list(re.finditer(r'\b' + re.escape(key_in_text) + r'\b', existing_tag_content, re.IGNORECASE))
                for m in matches:
                    found_indices.append((m.start(), canonical_key, key_in_text)) # Use key_in_text to check if it matches value type

            # Find positions of other keys (Custom)
            # Look for ANY_KEY=...
            for m in re.finditer(r'([a-zA-Z0-9_]+)=', existing_tag_content):
                k = m.group(1).upper()
                if k not in ['ADDR', 'DEFAULT', 'DESC', 'REG_NAME', 'BIT_OFFSET']:
                    # It's a custom key
                    found_indices.append((m.start(), k, m.group(1)))
                    # Also capture its value from 'parsed' if possible, or extract it simpler
                    if parsed:
                         # key might be lower in parsed
                         val = parsed.get(k.lower()) or parsed.get(k)
                         if val is not None:
                             custom_attrs[k] = val
                             current_values[k] = val # Add to current values

            # Sort by position
            found_indices.sort(key=lambda x: x[0])
            
            # Extract unique ordered keys
            seen = set()
            for _, canonical, original in found_indices:
                if canonical not in seen:
                    ordered_keys.append(canonical)
                    seen.add(canonical)
                
                # Special handling for Access mode which might appear as RO/RW/WO
                if canonical == 'ACCESS':
                     # Check if we should update access form based on text? No, use reg data.
                     pass

        # 3. Construct final list
        final_parts = []
        processed_keys = set()
        
        # Helper to format value
        def format_attr(key, val):
            if key == 'ACCESS': return val # RW, RO etc
            if key in ['R_STROBE', 'W_STROBE']: return key if val else None
            if val is True: return key # Custom flag
            return f'{key}={val}'

        # Add collected keys in order
        for key in ordered_keys:
            if key in current_values:
                val = current_values[key]
                s = format_attr(key, val)
                if s: final_parts.append(s)
                processed_keys.add(key)
        
        # Add remaining standard keys (new ones) in default order
        default_order = ['ACCESS', 'ADDR', 'REG_NAME', 'BIT_OFFSET', 'DEFAULT', 'DESC', 'R_STROBE', 'W_STROBE']
        for key in default_order:
            if key not in processed_keys and key in current_values:
                val = current_values[key]
                s = format_attr(key, val)
                if s: final_parts.append(s)
                processed_keys.add(key)
                
        # Add remaining custom keys
        for key, val in current_values.items():
            if key not in processed_keys:
                 s = format_attr(key, val)
                 if s: final_parts.append(s)
        
        return f"-- @axion { ' '.join(final_parts) }"

    def _generate_vhdl_signal(self, reg: Dict, include_description: bool = True, existing_tag: str = None, delimiter: str = " ") -> str:
        """Generate VHDL signal declaration for a new register."""
        name = reg['name']
        try:
            width = int(reg.get('width', 32))
        except (ValueError, TypeError):
            width = 32
            
        default_val_raw = reg.get('default_value', '')
        
        # Determine type
        if width == 1:
            sig_type = "std_logic"
            width_suffix = ""
            default_str = ""
        else:
            sig_type = "std_logic_vector"
            width_suffix = f"({width-1} downto 0)"
            default_str = ""

        # Default value handling:
        # User requested NOT to generate VHDL initialization (:= ...).
        # We only keep the DEFAULT attribute in the @axion tag.
        default_str = ""

        lines = []
        if include_description and reg.get('description'):
            lines.append(f"    -- {reg['description']}")
            
        axion_tag = self._generate_axion_tag(reg, existing_tag)
        # Use captured delimiter (e.g. "  ") instead of hardcoded space
        lines.append(f"    signal {name} : {sig_type}{width_suffix}{default_str};{delimiter}{axion_tag}")
        
        return "\n".join(lines)

    def _update_generics(self, content: str, properties: Dict) -> str:
        """Updates VHDL generics based on provided properties."""
        if not properties:
            return content
            
        # Update CDC Enable
        if 'cdc_enabled' in properties:
            val = 'true' if properties['cdc_enabled'] else 'false'
            # Look for C_CDC_ENABLE or CDC_ENABLED or similar
            # Pattern: (Name) : (Type) := (Value)
            pattern = r'(?i)((?:C_)?CDC_EN(?:ABLE|ABLED))\s*:\s*boolean\s*:=\s*(\w+)'
            
            def replace_bool(match):
                return f"{match.group(1)} : boolean := {val}"
                
            content = re.sub(pattern, replace_bool, content)
            
        # Update CDC Stages
        if 'cdc_stages' in properties:
            val = str(properties['cdc_stages'])
            pattern = r'(?i)((?:C_)?CDC_STAGES?)\s*:\s*integer\s*:=\s*(\d+)'
            
            def replace_int(match):
                return f"{match.group(1)} : integer := {val}"
                
            content = re.sub(pattern, replace_int, content)
            
        # Update Base Address (if it exists as generic C_BASEADDR)
        if 'base_address' in properties:
            val = properties['base_address']
            # Only update if it looks like a hex string
            if val and val.startswith('0x'):
                 # Pattern: C_BASEADDR : std_logic_vector... := X"..."
                 pass # Base address usually hex, complicated to match generic type easily without destroying formatting
                 # Skipping base addr as it is often a top-level param, not local default.
        
        return content

    def get_modified_content(self, module_name: str, new_registers: List[Dict], properties: Dict = None, file_path: str = None) -> Tuple[str, str]:
        """
        Generates the new content for the file associated with the module.
        Handles both adding NEW registers and UPDATING existing ones used Smart Preservation.
        
        Args:
            module_name: Name of the module
            new_registers: List of register dictionaries
            properties: Optional properties dict
            file_path: Optional file path for disambiguation when multiple modules have same name
        """
        # Find module - use file_path if provided for disambiguation
        if file_path:
            module = next((m for m in self.axion.analyzed_modules 
                          if m['name'] == module_name and m['file'] == file_path), None)
        else:
            module = next((m for m in self.axion.analyzed_modules if m['name'] == module_name), None)
            
        if not module:
            raise ValueError(f"Module {module_name} not found")

        filepath = module['file']
        
        # Route to appropriate handler based on file type
        if filepath.endswith(('.yaml', '.yml')):
            return self._modify_yaml_content(module, new_registers, properties)
        elif filepath.endswith('.json'):
            return self._modify_json_content(module, new_registers, properties)
        elif filepath.endswith('.xml'):
            return self._modify_xml_content(module, new_registers, properties)
        
        # VHDL files - original logic
        with open(filepath, 'r') as f:
            content = f.read()

        # Update Generics first
        content = self._update_generics(content, properties)
        
        # Update Module Definitions (@axion_def)
        content = self._update_module_definition(content, properties)

        # Identify existing signals
        existing_names = set()
        for r in module['registers']:
            existing_names.add(r.get('reg_name'))
            existing_names.add(r.get('signal_name'))
            if r.get('is_packed') and r.get('fields'):
                for f in r['fields']:
                    existing_names.add(f.get('signal_name'))
                    existing_names.add(f.get('name'))  # Also check 'name' key (used by VHDL parser)
        
        # Regex to find architecture start
        arch_pattern = r'architecture\s+\w+\s+of\s+\w+\s+is'
        arch_match = re.search(arch_pattern, content, re.IGNORECASE)
        
        if not arch_match:
            return content, filepath
            
        search_start_idx = arch_match.end()
        is_vhdl = filepath.endswith(('.vhd', '.vhdl'))
        
        to_add = []
        
        for reg in new_registers:
            if reg['name'] in existing_names:
                # UPDATE existing register
                pattern = r'(\s*)signal\s+' + re.escape(reg['name']) + r'\s*:\s*[^;]+;.*'
                match = re.search(pattern, content, re.IGNORECASE)
                
                if match:
                    line_content = match.group(0)
                    existing_tag_content = None
                    
                    # Capture original line spacing pattern for reconstruction
                    # Capture spacing: signal NAME<spaces>:<spaces>TYPE<spaces>;
                    orig_fmt_match = re.search(
                        r'signal\s+' + re.escape(reg['name']) + r'(\s*):\s*([^;]+);(\s*)(--.*)?$',
                        line_content,
                        re.IGNORECASE
                    )
                    spacing_after_name = orig_fmt_match.group(1) if orig_fmt_match else " "
                    orig_type_part = orig_fmt_match.group(2).strip() if orig_fmt_match else ""
                    spacing_after_semi = orig_fmt_match.group(3) if orig_fmt_match else " "
                    
                    # Capture existing delimiter (whitespace before --)
                    # Look for ;<detected_whitespace>--
                    delimiter_match = re.search(r';(\s*)--', line_content)
                    detected_delimiter = delimiter_match.group(1) if delimiter_match else " "
                    
                    # Extract existing tag content for preservation
                    # Look for -- @axion ...
                    tag_match = re.search(r'--\s*@axion\s*:?(.+)$', line_content, re.IGNORECASE)
                    if tag_match:
                        existing_tag_content = tag_match.group(1).strip()
                    elif '--' in line_content: # Maybe just -- RW etc without @axion explicitly if loose?
                        # Parser expects @axion usually. If missing, maybe standard comments?
                        pass
                        
                    
                    # Smart Preservation Logic (VHDL Only)
                    structure_changed = True
                    original_reg = next((r for r in module['registers'] if r.get('reg_name') == reg['name'] or r.get('signal_name') == reg['name']), None)
                    
                    if is_vhdl and original_reg:
                        # Compare fields to see if line regeneration is even needed
                        if self._are_registers_identical(original_reg, reg):
                            structure_changed = False
                    
                    indent = match.group(1)
                    
                    if not structure_changed:
                         # Skip regeneration entirely - preserve exact line content
                         pass 
                    else:
                        # Generate new signal line preserving original spacing
                        axion_tag = self._generate_axion_tag(reg, existing_tag_content)
                        
                        try:
                            width = int(reg.get('width', 32))
                        except (ValueError, TypeError):
                            width = 32
                        
                        if width == 1:
                            sig_type_str = "std_logic"
                        else:
                            sig_type_str = f"std_logic_vector({width-1} downto 0)"
                        
                        # Reconstruct line with original spacing
                        new_line_content = f"signal {reg['name']}{spacing_after_name}: {sig_type_str};{detected_delimiter}{axion_tag}"
                        full_new_line = f"{indent}{new_line_content}"
                        content = re.sub(pattern, full_new_line, content, count=1)
            else:
                to_add.append(reg)
                
        if not to_add:
            return content, filepath

        # Logic for ADDING new registers
        lines_to_inject = []
        for reg in to_add:
             lines_to_inject.append(self._generate_vhdl_signal(reg))
             
        if not lines_to_inject:
             return content, filepath
            
        # Find position to insert new registers
        begin_match = re.search(r'\bbegin\b', content[search_start_idx:], re.IGNORECASE)
        
        if begin_match:
            insert_pos = search_start_idx + begin_match.start()
            injection = "\n    -- Axion-HDL Auto-Injected Signals\n"
            injection += "\n".join(lines_to_inject)
            injection += "\n"
            new_content = content[:insert_pos] + injection + content[insert_pos:]
            return new_content, filepath
            
        return content, filepath

    def compute_diff(self, module_name: str, new_registers: List[Dict], properties: Dict = None, file_path: str = None) -> Optional[str]:
        """Returns the unified diff between original and modified content.
        
        Args:
            module_name: Name of the module
            new_registers: List of register dictionaries
            properties: Optional properties dict
            file_path: Optional file path for disambiguation when multiple modules have same name
        """
        try:
            new_content, filepath = self.get_modified_content(module_name, new_registers, properties, file_path=file_path)
            with open(filepath, 'r') as f:
                original_content = f.read()
            
            if new_content == original_content:
                return None
            
            diff = difflib.unified_diff(
                original_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{os.path.basename(filepath)}",
                tofile=f"b/{os.path.basename(filepath)}"
            )
            return "".join(diff)
        except Exception as e:
            return f"Error generating diff: {str(e)}"

    def save_changes(self, module_name: str, new_registers: List[Dict], properties: Dict = None, file_path: str = None) -> bool:
        """Writes the modified content to disk."""
        new_content, filepath = self.get_modified_content(module_name, new_registers, properties, file_path=file_path)
        with open(filepath, 'w') as f:
            f.write(new_content)
        return True

    def _modify_yaml_content(self, module: Dict, new_registers: List[Dict], properties: Dict = None) -> Tuple[str, str]:
        """Modify YAML content preserving original structure using text-based replacement."""
        import re
        
        filepath = module['file']
        
        # Read original file as text to preserve comments and formatting
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Build register lookup by name - only include registers that actually changed
        original_regs = {r.get('reg_name', r.get('signal_name', r.get('name'))): r for r in module.get('registers', [])}
        
        # Update base_addr if it changed
        if properties and properties.get('base_address'):
            new_base = properties.get('base_address')
            orig_base = module.get('base_address_raw', module.get('base_address', '0'))
            try:
                # Helper for flexible hex parsing
                def parse_hex_safe(val):
                    if isinstance(val, int): return val
                    val = str(val).strip()
                    if val.lower().startswith('0x'): return int(val, 16)
                    try: return int(val, 16)
                    except ValueError: return int(val)

                orig_base_int = parse_hex_safe(orig_base)
                new_base_int = parse_hex_safe(new_base)

                if new_base_int != orig_base_int:
                    # Replace base_addr in YAML
                    content = re.sub(r'(base_addr:\s*)([^\n]+)', rf'\g<1>0x{new_base_int:04X}', content)
            except (ValueError, TypeError):
                pass
        
        # Update CDC config if changed
        if properties:
            cdc_enabled = properties.get('cdc_enabled')
            cdc_stages = properties.get('cdc_stages')
            
            # Update cdc_en in config section
            if cdc_enabled is not None:
                cdc_val = 'true' if cdc_enabled else 'false'
                if re.search(r'cdc_en\s*:', content):
                    # Robust replacement handling quotes or no quotes
                    content = re.sub(r'(cdc_en\s*:\s*)(\S+)', rf'\g<1>{cdc_val}', content)
                else:
                    # Try to add cdc_en after config: line
                    if re.search(r'config:\s*\n', content):
                        content = re.sub(r'(config:\s*\n)', rf'\1  cdc_en: {cdc_val}\n', content)
                    else:
                        # Append to end if no config section (fallback)
                        content += f"\nconfig:\n  cdc_en: {cdc_val}\n"
            
            # Update cdc_stage in config section
            if cdc_stages is not None:
                stage_val = str(int(cdc_stages))
                if re.search(r'cdc_stage\s*:', content):
                    content = re.sub(r'(cdc_stage\s*:\s*)(\d+)', rf'\g<1>{stage_val}', content)
                else:
                    # Try to add cdc_stage after config: line
                    if re.search(r'config:\s*\n', content):
                        content = re.sub(r'(config:\s*\n)', rf'\1  cdc_stage: {stage_val}\n', content)
                    else:
                         # Append to end if no config section (fallback - but unlikely if cdc_en added config)
                         if 'config:' not in content:
                             content += f"\nconfig:\n  cdc_stage: {stage_val}\n"
                         else:
                             content = re.sub(r'(config:\s*\n)', rf'\1  cdc_stage: {stage_val}\n', content)
        
        # Build new register name set for deletion detection
        new_reg_names = {r.get('name') for r in new_registers}
        
        # Remove registers that are no longer in the new list
        for orig_name in list(original_regs.keys()):
            if orig_name not in new_reg_names:
                # Remove the entire register block from YAML
                # Match: "  - name: reg_name\n    ...until next register or end of registers section"
                pattern = rf'^\s*-\s*name:\s*{re.escape(orig_name)}\b[^\n]*\n(?:\s+[^\n]+\n)*?(?=\s*-\s*name:|\s*$)'
                content = re.sub(pattern, '', content, flags=re.MULTILINE)
        
        for new_reg in new_registers:
            reg_name = new_reg.get('name')
            orig_reg = original_regs.get(reg_name)
            
            if not orig_reg:
                continue
            
            # Check if access actually changed
            if new_reg.get('access') != orig_reg.get('access'):
                # Find and replace access for this register's block
                pattern = rf'(- name:\s*{re.escape(reg_name)}\b.*?access:\s*)[A-Z]+(\s)'
                replacement = rf'\g<1>{new_reg.get("access", "RW")}\2'
                content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            
            # Check if width actually changed (compare as integers)
            orig_width = orig_reg.get('signal_width', orig_reg.get('width', 32))
            new_width = new_reg.get('width')
            try:
                orig_width_int = int(orig_width) if orig_width else 32
                new_width_int = int(new_width) if new_width else 32
            except (ValueError, TypeError):
                orig_width_int = 32
                new_width_int = 32
                
            if new_width_int != orig_width_int:
                pattern = rf'(- name:\s*{re.escape(reg_name)}\b.*?width:\s*)\d+(\s)'
                replacement = rf'\g<1>{new_width_int}\2'
                content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            
            # Helper to insert field if missing
            def update_or_insert_yaml_field(content, reg_name, field_name, new_value, anchor_field='width'):
                # Try replacing first
                pattern = rf'(- name:\s*{re.escape(reg_name)}\b.*?{field_name}:\s*)([^\n]+)(\n)'
                match = re.search(pattern, content, flags=re.DOTALL | re.IGNORECASE)
                
                if match:
                    # Field exists, update it
                    replacement = rf'\g<1>{new_value}\3'
                    return re.sub(pattern, replacement, content, flags=re.DOTALL | re.IGNORECASE)
                else:
                    # Field missing, insert it after anchor
                    anchor_pattern = rf'(- name:\s*{re.escape(reg_name)}\b.*?{anchor_field}:\s*[^\n]+\n)'
                    anchor_match = re.search(anchor_pattern, content, flags=re.DOTALL)
                    if anchor_match:
                        # Find indentation of the anchor line
                        indent = re.match(r'\s*', anchor_match.group(0).split('\n')[-2]).group(0)
                        # Use same indentation for new field
                        insertion = f'{indent}{field_name}: {new_value}\n'
                        return content[:anchor_match.end()] + insertion + content[anchor_match.end():]
                return content

            # Check if address changed
            new_addr = new_reg.get('address')
            if new_addr:
                 try: 
                     val = int(str(new_addr), 16) if str(new_addr).startswith('0x') else int(str(new_addr))
                     formatted = f"0x{val:X}"
                     # Only update if manual address requested or it changed significantly?
                     # For now, if passed in new_reg, assume we want it
                     content = update_or_insert_yaml_field(content, reg_name, 'addr', formatted)
                 except: pass

            # Check if description changed
            new_desc = new_reg.get('description')
            if new_desc and new_desc != orig_reg.get('description'):
                content = update_or_insert_yaml_field(content, reg_name, 'description', f'"{new_desc}"')

            # Check if default_value changed
            new_default = new_reg.get('default_value')
            if new_default and new_default not in (0, '0', '0x0', ''):
                if new_default != orig_reg.get('default_value'):
                    content = update_or_insert_yaml_field(content, reg_name, 'default_value', new_default)
            elif not new_default:
                # Remove if exists and new value is empty
                pattern = rf'(- name:\s*{re.escape(reg_name)}\b.*?)\s+default_value:\s*[^\n]+\n'
                content = re.sub(pattern, r'\1', content, flags=re.DOTALL)

            # Check if r_strobe changed
            new_r_strobe = new_reg.get('r_strobe', False)
            orig_r_strobe = orig_reg.get('rd_strobe')
            if orig_r_strobe is None:
                orig_r_strobe = orig_reg.get('r_strobe', False)
            
            if new_r_strobe != orig_r_strobe:
                if new_r_strobe: # True
                    content = update_or_insert_yaml_field(content, reg_name, 'r_strobe', 'true')
                else: # False -> remove
                    pattern = rf'(- name:\s*{re.escape(reg_name)}\b.*?)\s+r_strobe:\s*[^\n]+\n'
                    content = re.sub(pattern, r'\1', content, flags=re.DOTALL | re.IGNORECASE)
            
            # Check if w_strobe changed
            new_w_strobe = new_reg.get('w_strobe', False)
            orig_w_strobe = orig_reg.get('wr_strobe')
            if orig_w_strobe is None:
                orig_w_strobe = orig_reg.get('w_strobe', False)
            
            if new_w_strobe != orig_w_strobe:
                if new_w_strobe: # True
                    content = update_or_insert_yaml_field(content, reg_name, 'w_strobe', 'true')
                else: # False -> remove
                    pattern = rf'(- name:\s*{re.escape(reg_name)}\b.*?)\s+w_strobe:\s*[^\n]+\n'
                    content = re.sub(pattern, r'\1', content, flags=re.DOTALL | re.IGNORECASE)
        
        return content, filepath

    def _modify_json_content(self, module: Dict, new_registers: List[Dict], properties: Dict = None) -> Tuple[str, str]:
        """Modify JSON content preserving original structure, only updating changed registers."""
        import json
        
        filepath = module['file']
        
        # Read original file
        with open(filepath, 'r') as f:
            original_data = json.load(f)
        
        if not original_data:
            original_data = {}
        
        # Build lookup maps
        new_reg_map = {r.get('name'): r for r in new_registers}
        original_regs = {r.get('reg_name', r.get('signal_name', r.get('name'))): r for r in module.get('registers', [])}
        
        # Update module-level properties (base_addr, cdc, etc.) if they changed
        if properties:
            new_base = properties.get('base_address')
            # Use 'base_addr' key for JSON files
            if new_base and 'base_addr' in original_data:
                # Compare as normalized hex strings or integers
                try:
                    orig_base = original_data.get('base_addr', 0)
                except (ValueError, TypeError):
                    pass
            
            # Handle base address hex parsing (safe)
            def parse_hex_safe(val):
                if isinstance(val, int): return val
                val = str(val).strip()
                if val.lower().startswith('0x'): return int(val, 16)
                try: return int(val, 16)
                except ValueError: return int(val)

            orig_base = original_data.get('base_addr', 0)
            try:
                orig_base_int = parse_hex_safe(orig_base)
                new_base_int = parse_hex_safe(new_base) if new_base else orig_base_int
                
                if new_base and new_base_int != orig_base_int:
                     original_data['base_addr'] = f"0x{new_base_int:04X}"
            except: pass
            
            # Update CDC settings - handle both top-level and nested config structure
            cdc_enabled = properties.get('cdc_enabled')
            cdc_stages = properties.get('cdc_stages')
            
            if cdc_enabled is not None:
                # Check nested config structure first (matches sensor_controller.json)
                # Check nested config structure first (matches sensor_controller.json)
                if 'config' in original_data:
                    original_data['config']['cdc_en'] = cdc_enabled
                elif 'cdc' in original_data:
                    original_data['cdc'] = cdc_enabled
                elif 'cdc_enabled' in original_data:
                    original_data['cdc_enabled'] = cdc_enabled
                elif 'cdc_en' in original_data:
                    original_data['cdc_en'] = cdc_enabled
                else:
                    # Case: no cdc props exist. Add to config if exists, else create config
                    if 'config' not in original_data:
                        original_data['config'] = {}
                    original_data['config']['cdc_en'] = cdc_enabled
            
            if cdc_stages is not None:
                stage_val = int(cdc_stages)
                # Check nested config structure first
                if 'config' in original_data:
                    original_data['config']['cdc_stage'] = stage_val
                elif 'cdc_stages' in original_data:
                    original_data['cdc_stages'] = stage_val
                elif 'cdc_stage' in original_data:
                    original_data['cdc_stage'] = stage_val
                else:
                    if 'config' not in original_data:
                        original_data['config'] = {}
                    original_data['config']['cdc_stage'] = stage_val
        
        # Update registers in place - only if actually changed
        if 'registers' in original_data:
            # First, remove any registers that are no longer in the new list
            original_data['registers'] = [
                reg for reg in original_data['registers'] 
                if reg.get('name') in new_reg_map
            ]
            
            for i, file_reg in enumerate(original_data['registers']):
                reg_name = file_reg.get('name')
                if reg_name not in new_reg_map:
                    continue
                    
                new_reg = new_reg_map[reg_name]
                orig_reg = original_regs.get(reg_name, {})
                
                # Only update fields that actually changed AND exist in original
                if new_reg.get('access') != orig_reg.get('access') and 'access' in file_reg:
                    original_data['registers'][i]['access'] = new_reg.get('access')
                    
                # Compare width as integers to avoid false positives from type differences
                orig_width = orig_reg.get('signal_width', orig_reg.get('width', 32))
                new_width = new_reg.get('width')
                try:
                    orig_width_int = int(orig_width) if orig_width else 32
                    new_width_int = int(new_width) if new_width else 32
                except (ValueError, TypeError):
                    orig_width_int = 32
                    new_width_int = 32
                    
                if new_width_int != orig_width_int and 'width' in file_reg:
                    # Preserve original type (int or str)
                    if isinstance(file_reg['width'], int):
                        original_data['registers'][i]['width'] = new_width_int
                    else:

                        original_data['registers'][i]['width'] = str(new_width_int)
                
                # Update or ADD address
                new_addr = new_reg.get('address')
                if new_addr:
                    try:
                        val = int(str(new_addr), 16) if str(new_addr).startswith('0x') else int(str(new_addr))
                        original_data['registers'][i]['addr'] = f"0x{val:X}"
                        # Remove 'address' if mistakenly used
                        if 'address' in original_data['registers'][i]:
                            del original_data['registers'][i]['address']
                    except: pass
                    
                # Update or ADD description
                new_desc = new_reg.get('description')
                if new_desc and new_desc != orig_reg.get('description'):
                    original_data['registers'][i]['description'] = new_desc
                    
                # Update or ADD default_value (add if non-zero/non-empty)
                new_default = new_reg.get('default_value')
                if new_default and new_default not in (0, '0', '0x0', ''):
                    if new_default != orig_reg.get('default_value'):
                        original_data['registers'][i]['default_value'] = new_default
                elif 'default_value' in file_reg and not new_default:
                    # Remove if set to empty/zero and was present
                    del original_data['registers'][i]['default_value']
                
                # Update or ADD r_strobe
                new_r_strobe = new_reg.get('r_strobe', False)
                orig_r_strobe = orig_reg.get('rd_strobe')
                if orig_r_strobe is None:
                    orig_r_strobe = orig_reg.get('r_strobe', False)
                if new_r_strobe != orig_r_strobe:
                    if new_r_strobe:  # Add or update if True
                        original_data['registers'][i]['r_strobe'] = True
                    elif 'r_strobe' in file_reg:  # Remove if False and was present
                        del original_data['registers'][i]['r_strobe']
                
                # Update or ADD w_strobe
                new_w_strobe = new_reg.get('w_strobe', False)
                orig_w_strobe = orig_reg.get('wr_strobe')
                if orig_w_strobe is None:
                    orig_w_strobe = orig_reg.get('w_strobe', False)
                if new_w_strobe != orig_w_strobe:
                    if new_w_strobe:  # Add or update if True
                        original_data['registers'][i]['w_strobe'] = True
                    elif 'w_strobe' in file_reg:  # Remove if False and was present
                        del original_data['registers'][i]['w_strobe']
        
        new_content = json.dumps(original_data, indent=2)
        return new_content, filepath

    def _modify_xml_content(self, module: Dict, new_registers: List[Dict], properties: Dict = None) -> Tuple[str, str]:
        """Modify XML content preserving original structure, only updating changed register attributes."""
        import re
        
        filepath = module['file']
        
        # Read original file - preserve all structure including comments
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Build lookup maps
        # For subregister fields, 'name' is the field name (e.g., 'enable')
        # For standard registers, 'name' is also the register name
        new_reg_map = {r.get('name'): r for r in new_registers}
        
        # Build set of ALL names that should be kept (both subregister field names and standard register names)
        new_reg_names = {r.get('name') for r in new_registers}
        
        # Also track parent container names that are represented by subregister fields
        # These should NOT be deleted from the file
        parent_names_with_fields = set()
        for r in new_registers:
            if r.get('is_packed_field') and r.get('reg_name'):
                parent_names_with_fields.add(r.get('reg_name'))
        
        # Original registers from parsed module
        original_regs = {}
        for r in module.get('registers', []):
            # For packed registers, also track the fields
            if r.get('is_packed') and r.get('fields'):
                for field in r.get('fields', []):
                    original_regs[field.get('name')] = field
            else:
                name = r.get('reg_name', r.get('signal_name', r.get('name')))
                original_regs[name] = r
        
        # Update base_addr if it changed
        if properties and properties.get('base_address'):
            new_base = properties.get('base_address')
            orig_base = module.get('base_address_raw', module.get('base_address', '0'))
            try:
                # Handle base address hex parsing (even without 0x prefix if valid hex)
                def parse_hex_safe(val):
                    if isinstance(val, int): return val
                    val = str(val).strip()
                    if val.lower().startswith('0x'): return int(val, 16)
                    # Try treating as hex first if it looks like it
                    try:
                        return int(val, 16)
                    except ValueError:
                        return int(val) # Fallback to decimal

                orig_base = module.get('base_address_raw', module.get('base_address', '0'))
                orig_base_int = parse_hex_safe(orig_base)
                new_base_int = parse_hex_safe(new_base)
                
                if new_base_int != orig_base_int:
                    # Replace base_addr attribute in module tag
                    content = re.sub(r'(base_addr\s*=\s*["\'])([^"\']+)(["\'])', rf'\g<1>0x{new_base_int:04X}\3', content)
            except (ValueError, TypeError):
                pass
        
        # Update CDC config if changed
        if properties:
            cdc_enabled = properties.get('cdc_enabled')
            cdc_stages = properties.get('cdc_stages')
            
            # Check if <config> tag exists
            has_config_tag = re.search(r'<config\b', content) is not None
            
            # Update cdc_en in <config> tag
            if cdc_enabled is not None:
                cdc_val = 'true' if cdc_enabled else 'false'
                if re.search(r'<config[^>]*cdc_en\s*=', content):
                    content = re.sub(r'(cdc_en\s*=\s*["\'])([^"\']+)(["\'])', rf'\g<1>{cdc_val}\3', content)
                elif has_config_tag:
                    # Add cdc_en to existing config tag
                    content = re.sub(r'(<config\s+)', rf'\1cdc_en="{cdc_val}" ', content)
                else:
                    # Create new config tag after register_map opening tag
                    stage_attr = f' cdc_stage="{cdc_stages}"' if cdc_stages else ''
                    config_tag = f'\n    <config cdc_en="{cdc_val}"{stage_attr}/>'
                    content = re.sub(r'(<register_map[^>]*>)', rf'\1{config_tag}', content)
                    has_config_tag = True  # Mark as added
            
            # Update cdc_stage in <config> tag
            if cdc_stages is not None:
                stage_val = str(int(cdc_stages))
                if re.search(r'<config[^>]*cdc_stage\s*=', content):
                    content = re.sub(r'(cdc_stage\s*=\s*["\'])(\d+)(["\'])', rf'\g<1>{stage_val}\3', content)
                elif has_config_tag:
                    # Add cdc_stage to existing config tag (might have been added above)
                    content = re.sub(r'(<config\s+[^>]*?)(\s*/>)', rf'\1 cdc_stage="{stage_val}"\2', content)

        
        # Remove registers that are no longer in the new list
        # IMPORTANT: Don't delete parent container names that have subregister fields
        for orig_name in list(original_regs.keys()):
            # Skip if this name is in the new list OR if it's a parent with fields
            if orig_name in new_reg_names or orig_name in parent_names_with_fields:
                continue
            # Remove the entire register tag
            # Match: <register ... name="orig_name" ... /> or <register ... name="orig_name" ...>...</register>
            pattern = rf'<register\s+[^>]*name=["\']{ re.escape(orig_name)}["\'][^>]*(?:/>|>[^<]*</register>)'
            content = re.sub(pattern, '', content, flags=re.DOTALL)

        def update_register_tag(match):
            """Update a single register tag only for fields that actually changed."""
            tag = match.group(0)
            
            # Extract current name
            name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', tag)
            if not name_match:
                return tag  # Keep original if no name found
                
            reg_name = name_match.group(1)
            if reg_name not in new_reg_map:
                return tag  # Keep original if not in new map (shouldn't delete here)
            
            new_reg = new_reg_map[reg_name]
            orig_reg = original_regs.get(reg_name, {})
            
            # Helper to insert attribute if missing
            def insert_attr(tag_str, attr_name, attr_value):
                if attr_value is None: return tag_str
                # Insert before closing /> or >
                if '/>' in tag_str:
                    return tag_str.replace('/>', f' {attr_name}="{attr_value}"/>')
                elif '>' in tag_str:
                    # Find the first > that closes the opening tag
                    first_close = tag_str.find('>')
                    return tag_str[:first_close] + f' {attr_name}="{attr_value}"' + tag_str[first_close:]
                return tag_str

            # Only update attributes that actually changed
            if new_reg.get('access') and new_reg.get('access') != orig_reg.get('access'):
                if re.search(r'access\s*=', tag):
                    tag = re.sub(r'access\s*=\s*["\'][^"\']*["\']', f'access="{new_reg.get("access")}"', tag)
                else:
                    tag = insert_attr(tag, 'access', new_reg.get('access'))
            
            # Compare width as integers to avoid type mismatch
            orig_width = orig_reg.get('signal_width', orig_reg.get('width', 32))
            new_width = new_reg.get('width')
            try:
                orig_width_int = int(orig_width) if orig_width else 32
                new_width_int = int(new_width) if new_width else 32
            except (ValueError, TypeError):
                orig_width_int = 32
                new_width_int = 32
                
            if new_width_int != orig_width_int:
                if re.search(r'width\s*=', tag):
                    tag = re.sub(r'width\s*=\s*["\'][^"\']*["\']', f'width="{new_width_int}"', tag)
                else:
                    tag = insert_attr(tag, 'width', new_width_int)
            
            # bit_offset update for subregister fields
            new_bit_offset = new_reg.get('bit_offset')
            orig_bit_offset = orig_reg.get('bit_offset', orig_reg.get('bit_low'))
            if new_bit_offset is not None:
                try:
                    new_offset_int = int(new_bit_offset) if new_bit_offset else 0
                    orig_offset_int = int(orig_bit_offset) if orig_bit_offset else 0
                    if new_offset_int != orig_offset_int:
                        if re.search(r'bit_offset\s*=', tag):
                            tag = re.sub(r'bit_offset\s*=\s*["\'][^"\']*["\']', f'bit_offset="{new_offset_int}"', tag)
                        else:
                            tag = insert_attr(tag, 'bit_offset', new_offset_int)
                except (ValueError, TypeError):
                    pass
            
            # Description update/add
            new_desc = new_reg.get('description')
            if new_desc and new_desc != orig_reg.get('description'):
                desc = new_desc.replace('&', '&amp;').replace('"', '&quot;')
                if re.search(r'description\s*=', tag):
                    tag = re.sub(r'description\s*=\s*["\'][^"\']*["\']', f'description="{desc}"', tag)
                else:
                    tag = insert_attr(tag, 'description', desc)
            
            # Default value update/add/remove
            new_default = new_reg.get('default_value')
            if new_default and new_default not in (0, '0', '0x0', ''):
                if new_default != orig_reg.get('default_value'):
                    if re.search(r'default\s*=', tag):
                        tag = re.sub(r'default\s*=\s*["\'][^"\']*["\']', f'default="{new_default}"', tag)
                    else:
                        tag = insert_attr(tag, 'default', new_default)
            elif re.search(r'default\s*=', tag) and not new_default:
                # Remove if exists and new value is empty
                tag = re.sub(r'\s+default\s*=\s*["\'][^"\']*["\']', '', tag)
            
            # r_strobe update/add/remove
            new_r_strobe = new_reg.get('r_strobe', False)
            orig_r_strobe = orig_reg.get('rd_strobe')
            if orig_r_strobe is None:
                orig_r_strobe = orig_reg.get('r_strobe', False)
            
            if new_r_strobe != orig_r_strobe:
                if new_r_strobe: # True
                    if re.search(r'r_strobe\s*=', tag):
                        tag = re.sub(r'r_strobe\s*=\s*["\'][^"\']*["\']', f'r_strobe="true"', tag)
                    else:
                        tag = insert_attr(tag, 'r_strobe', 'true')
                elif re.search(r'r_strobe\s*=', tag): # False and exists -> remove
                    tag = re.sub(r'\s+r_strobe\s*=\s*["\'][^"\']*["\']', '', tag)
            
            # w_strobe update/add/remove
            new_w_strobe = new_reg.get('w_strobe', False)
            orig_w_strobe = orig_reg.get('wr_strobe')
            if orig_w_strobe is None:
                orig_w_strobe = orig_reg.get('w_strobe', False)
                
            if new_w_strobe != orig_w_strobe:
                if new_w_strobe: # True
                    if re.search(r'w_strobe\s*=', tag):
                        tag = re.sub(r'w_strobe\s*=\s*["\'][^"\']*["\']', f'w_strobe="true"', tag)
                    else:
                        tag = insert_attr(tag, 'w_strobe', 'true')
                elif re.search(r'w_strobe\s*=', tag): # False and exists -> remove
                    tag = re.sub(r'\s+w_strobe\s*=\s*["\'][^"\']*["\']', '', tag)
            
            # Address update/add
            new_addr = new_reg.get('address')
            # normalize address
            try:
                if new_addr:
                    new_addr_int = int(str(new_addr), 16) if str(new_addr).startswith('0x') else int(str(new_addr))
                    # Check if address explicit attribute exists or if we need to add/update it
                    # Only if it differs from auto-calc or is explicitly manual?
                    # For XML, usually we want to persist it if it's there.
                    
                    if re.search(r'\b(addr|address)\s*=', tag):
                        # Update existing
                        tag = re.sub(r'\b(addr|address)\s*=\s*["\'][^"\']*["\']', f'addr="0x{new_addr_int:X}"', tag)
                    elif new_reg.get('manual_address'):
                        # Insert if manual
                        tag = insert_attr(tag, 'addr', f"0x{new_addr_int:X}")
            except:
                pass

            return tag
        
        # Match <register ... /> or <register ...>...</register> tags
        new_content = re.sub(
            r'<register\s+[^>]*(?:/>|>[^<]*</register>)', 
            update_register_tag, 
            content, 
            flags=re.DOTALL
        )
        
        return new_content, filepath

    def _are_registers_identical(self, old_reg: Dict, new_reg: Dict) -> bool:
        """Compare register properties to check if any change occurred."""
        # 1. Access Mode (normalize key names: parser uses access_mode, source uses access)
        old_access = old_reg.get('access') or old_reg.get('access_mode')
        new_access = new_reg.get('access') or new_reg.get('access_mode')
        if old_access != new_access:
            return False
            
        # 2. Width (Integer comparison)
        try:
            # Check for signal_width first in both (parser artifact)
            old_w = int(old_reg.get('signal_width', old_reg.get('width', 32)))
            new_w = int(new_reg.get('signal_width', new_reg.get('width', 32)))
            if old_w != new_w: return False
        except:
            return False # Assume changed on error
            
        # 3. Description
        # Normalize None -> empty string for safe comparison
        old_desc = old_reg.get('description') or ''
        new_desc = new_reg.get('description') or ''
        if old_desc.strip() != new_desc.strip():
             return False
             
        # 4. Strobes
        # Normalize none/false
        old_r = bool(old_reg.get('read_strobe') or old_reg.get('r_strobe'))
        new_r = bool(new_reg.get('r_strobe'))
        if old_r != new_r: return False
        
        old_ws = bool(old_reg.get('write_strobe') or old_reg.get('w_strobe'))
        new_ws = bool(new_reg.get('w_strobe'))
        if old_ws != new_ws: return False
        
        # 5. Default Value (Smart Compare)
        def parse_val(v):
            try:
                if isinstance(v, int): return v
                if isinstance(v, str):
                    if v.startswith('0x') or v.startswith('0X'): return int(v, 16)
                    return int(v)
                return 0
            except: return 0
        
        def parse_hex(v):
            """Parse hex address value."""
            try:
                if v is None: return None
                if isinstance(v, int): return v
                if isinstance(v, str):
                    v = v.strip().upper()
                    if v.startswith('0X'): return int(v, 16)
                    return int(v, 16) if v else None
                return None
            except: return None
        
        def get_address_value(reg):
            """Get address value from register, handling all possible field names."""
            # Try all possible address field names
            for field in ['address', 'addr', 'relative_address', 'relative_address_int']:
                val = reg.get(field)
                if val is not None:
                    return parse_hex(val)
            return None
            
        if parse_val(old_reg.get('default_value')) != parse_val(new_reg.get('default_value')):
            return False
        
        # 6. Address (compare if manual_address is set in new_reg)
        if new_reg.get('manual_address'):
            old_addr = get_address_value(old_reg)
            new_addr = parse_hex(new_reg.get('address'))
            if old_addr is not None and new_addr is not None and old_addr != new_addr:
                return False
            
        return True

    def _update_module_definition(self, content: str, properties: Dict) -> str:
        """Updates or injects @axion_def annotation for module properties."""
        if not properties:
            return content
            
        def_pattern = r'(--\s*@axion_def\s+)(.+)'
        match = re.search(def_pattern, content, re.IGNORECASE)
        
        cdc_en = properties.get('cdc_enabled')
        cdc_stages = properties.get('cdc_stages')
        base_address = properties.get('base_address')
        
        if match:
            # Update existing
            prefix = match.group(1)
            attrs_str = match.group(2)
            
            # Standardized CDC Logic: Use KV pairs (CDC_EN=true/false)
            # Find existing CDC_EN token (flag or KV)
            # Pattern matches: CDC_EN, CDC_EN=true, CDC_EN=false, CDC_EN=1, etc.
            cdc_pattern = r'\bCDC_EN(?:=(?:true|false|yes|no|1|0))?\b'
            
            if cdc_en is True:
                if re.search(cdc_pattern, attrs_str, re.IGNORECASE):
                    # Replace existing with explicit true
                    attrs_str = re.sub(cdc_pattern, 'CDC_EN=true', attrs_str, flags=re.IGNORECASE)
                else:
                    # Append if missing
                    attrs_str += " CDC_EN=true"
            elif cdc_en is False:
                if re.search(cdc_pattern, attrs_str, re.IGNORECASE):
                    # Replace existing with explicit false (if it was there)
                    attrs_str = re.sub(cdc_pattern, 'CDC_EN=false', attrs_str, flags=re.IGNORECASE)
                # If explicit false was NOT there, we generally don't add it to keep it clean,
                # UNLESS the user explicitly requested it in properties? 
                # For now, if we are disabling, we overwrite existing to =false.
                
            # 2. CDC Stages
            if cdc_stages:
                if re.search(r'\bCDC_STAGE=\d+', attrs_str):
                     attrs_str = re.sub(r'\bCDC_STAGE=\d+', f'CDC_STAGE={cdc_stages}', attrs_str)
                elif cdc_en is True:
                     attrs_str += f" CDC_STAGE={cdc_stages}"
            
            # 3. Base Address
            if base_address:
                # Normalize base address to hex format
                try:
                    if isinstance(base_address, str):
                        base_int = int(base_address.replace('0x', '').replace('0X', ''), 16)
                    else:
                        base_int = int(base_address)
                    base_hex = f"0x{base_int:04X}"
                    
                    if re.search(r'\bBASE_ADDR=0x[0-9A-Fa-f]+', attrs_str):
                        attrs_str = re.sub(r'\bBASE_ADDR=0x[0-9A-Fa-f]+', f'BASE_ADDR={base_hex}', attrs_str)
                    else:
                        attrs_str += f" BASE_ADDR={base_hex}"
                except (ValueError, TypeError):
                    pass
                     
            updated_line = f"{prefix}{attrs_str.strip()}"
            return re.sub(def_pattern, updated_line, content, count=1)
            
        else:
            # Inject new if CDC enabled OR base_address is being set
            if cdc_en or base_address:
                new_attrs = []
                if cdc_en:
                    new_attrs.append("CDC_EN=true")
                    if cdc_stages:
                        new_attrs.append(f"CDC_STAGE={cdc_stages}")
                
                if base_address:
                    try:
                        if isinstance(base_address, str):
                            base_int = int(base_address.replace('0x', '').replace('0X', ''), 16)
                        else:
                            base_int = int(base_address)
                        new_attrs.append(f"BASE_ADDR=0x{base_int:04X}")
                    except (ValueError, TypeError):
                        pass
                
                if new_attrs:
                    new_line = f"-- @axion_def {' '.join(new_attrs)}"
                    
                    # Insert before entity
                    entity_match = re.search(r'entity\s+(\w+)\s+is', content, re.IGNORECASE)
                    if entity_match:
                        start = entity_match.start()
                        return content[:start] + new_line + "\n" + content[start:]
                    else:
                        # Fallback: Top of file
                        return new_line + "\n" + content
                    
        return content
