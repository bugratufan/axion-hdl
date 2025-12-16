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
        Preserves custom attributes from existing tag if provided.
        """
        attrs = []
        
        # 1. Access Mode (Short format preferred: RW, RO, WO)
        access = reg.get('access', 'RW')
        attrs.append(f"{access}") 
        # Note: AnnotationParser handles 'RW' as plain token which sets access_mode='RW'
        # We output it simply as 'RW' to be clean.
        
        # 2. Strobes
        if reg.get('read_strobe'):
            attrs.append("R_STROBE")
        if reg.get('write_strobe'):
            attrs.append("W_STROBE")
            
        # 3. Custom Attributes Preservation
        if existing_tag_content:
            # Parse existing tag to find "other" attributes
            # We assume existing_tag_content typically starts with "-- @axion " or similar
            # AnnotationParser expects "-- @axion attrs..." line
            
            # Helper to mock a full comment line for parser
            dummy_line = f"-- @axion {existing_tag_content}" if not existing_tag_content.strip().startswith("--") else existing_tag_content
            parsed = self.annotation_parser.parse_annotation(dummy_line)
            
            if parsed:
                # Filter out standard keys managed by GUI
                standard_keys = {
                    'access', 'access_mode', 
                    'read_strobe', 'write_strobe', 'r_strobe', 'w_strobe',
                    'width', 'default', 'default_value',
                    'addr', 'address', 'base_addr', # usually structural or auto
                    'reg_name', 'signal_name'
                }
                
                # Reconstruct "other" attributes
                # Note: parsed dict has normalized keys. We lose original casing/format (e.g. key=val vs KEY=VAL).
                # To support "smart preservation" fully, ideally we use what was parsed.
                
                for key, val in parsed.items():
                    if key not in standard_keys:
                        # Append non-standard attributes
                        # How to format? 
                        # If val is True, it was likely a flag. -> KEY
                        # If val is value, -> key=val
                        
                        if val is True:
                            # Try to restore some convention? or just UPPERCASE flags?
                            # Users often use UPPER for flags (e.g. CDC_EN).
                            attrs.append(key.upper())
                        else:
                            attrs.append(f"{key}={val}")

        return f"-- @axion: {' '.join(attrs)}"

    def _generate_vhdl_signal(self, reg: Dict, include_description: bool = True, existing_tag: str = None) -> str:
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
            default_str = " := '0'"
        else:
            sig_type = "std_logic_vector"
            width_suffix = f"({width-1} downto 0)"
            default_str = " := (others => '0')"

        # Handle explicit default value
        if default_val_raw and default_val_raw != '0x0' and default_val_raw != 0 and default_val_raw != '0':
            try:
                if isinstance(default_val_raw, str) and default_val_raw.startswith('0x'):
                    val_int = int(default_val_raw, 16)
                else:
                    val_int = int(default_val_raw)
                
                # Format for VHDL
                if width == 1:
                    bit = '1' if val_int else '0'
                    default_str = f" := '{bit}'"
                else:
                    # Ensure alignment to 4 bits
                    nibbles = (width + 3) // 4
                    hex_str = f"{val_int:0{nibbles}X}"
                    default_str = f' := X"{hex_str}"'
            except (ValueError, TypeError):
                pass

        lines = []
        if include_description and reg.get('description'):
            lines.append(f"    -- {reg['description']}")
            
        axion_tag = self._generate_axion_tag(reg, existing_tag)
        lines.append(f"    signal {name} : {sig_type}{width_suffix}{default_str}; {axion_tag}")
        
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

        # Identify existing signals
        existing_names = set()
        for r in module['registers']:
            existing_names.add(r.get('reg_name'))
            existing_names.add(r.get('signal_name'))
            if r.get('is_packed') and r.get('fields'):
                for f in r['fields']:
                    existing_names.add(f.get('signal_name'))
        
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
                        try:
                            old_width = int(original_reg.get('signal_width', 32) if 'signal_width' in original_reg else original_reg.get('width', 32))
                            new_width = int(reg.get('width', 32))
                            
                            def parse_val(v):
                                try:
                                    if isinstance(v, int): return v
                                    if isinstance(v, str):
                                        if v.startswith('0x'): return int(v, 16)
                                        return int(v)
                                    return 0
                                except: return 0
                                
                            old_def = parse_val(original_reg.get('default_value', 0))
                            new_def = parse_val(reg.get('default_value', 0))
                            
                            if old_width == new_width and old_def == new_def:
                                structure_changed = False
                        except:
                            pass # Assume changed if parse fails
                    
                    indent = match.group(1)
                    
                    if not structure_changed:
                        # Attempt to preserve signal declaration, replace only tag
                        # Regex to capture signal definition before the Axion tag
                        preserve_pattern = r'^(\s*signal\s+[^;]+;)(.*)$'
                        p_match = re.match(preserve_pattern, line_content, re.IGNORECASE)
                        
                        if p_match:
                            signal_part = p_match.group(1)
                            # Generate just the new tag (passing existing content for preservation)
                            new_tag = self._generate_axion_tag(reg, existing_tag_content)
                            # Combine: signal part + space + new tag
                            full_new_line = f"{signal_part} {new_tag}"
                        else:
                            # Fallback to full regen
                            new_line_content = self._generate_vhdl_signal(reg, include_description=False, existing_tag=existing_tag_content).strip()
                            full_new_line = f"{indent}{new_line_content}"
                    else:
                        # Full regeneration
                        new_line_content = self._generate_vhdl_signal(reg, include_description=False, existing_tag=existing_tag_content).strip()
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
        
        # Update base_address if it changed
        if properties and properties.get('base_address'):
            new_base = properties.get('base_address')
            orig_base = module.get('base_address_raw', module.get('base_address', '0'))
            try:
                orig_base_int = int(orig_base, 16) if isinstance(orig_base, str) and orig_base.startswith('0x') else int(orig_base)
                new_base_int = int(new_base, 16) if isinstance(new_base, str) and new_base.startswith('0x') else int(new_base)
                if new_base_int != orig_base_int:
                    # Replace base_address in YAML - support both hex and decimal formats
                    content = re.sub(r'(base_address:\s*)([^\n]+)', rf'\g<1>0x{new_base_int:04X}', content)
            except (ValueError, TypeError):
                pass
        
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
        
        # Update module-level properties (base_address, cdc, etc.) if they changed
        if properties:
            new_base = properties.get('base_address')
            if new_base and 'base_address' in original_data:
                # Compare as normalized hex strings or integers
                try:
                    orig_base = original_data.get('base_address', 0)
                    orig_base_int = int(orig_base, 16) if isinstance(orig_base, str) and orig_base.startswith('0x') else int(orig_base)
                    new_base_int = int(new_base, 16) if isinstance(new_base, str) and new_base.startswith('0x') else int(new_base)
                    if new_base_int != orig_base_int:
                        # Preserve original format (hex string vs int)
                        if isinstance(orig_base, str) and orig_base.startswith('0x'):
                            original_data['base_address'] = f"0x{new_base_int:04X}"
                        elif isinstance(orig_base, str):
                            original_data['base_address'] = str(new_base_int)
                        else:
                            original_data['base_address'] = new_base_int
                except (ValueError, TypeError):
                    pass
            
            # Update CDC settings if they exist in original
            if 'cdc' in original_data or 'cdc_enabled' in original_data:
                if properties.get('cdc_enabled') is not None:
                    cdc_key = 'cdc' if 'cdc' in original_data else 'cdc_enabled'
                    original_data[cdc_key] = properties.get('cdc_enabled')
                if 'cdc_stages' in original_data and properties.get('cdc_stages'):
                    original_data['cdc_stages'] = int(properties.get('cdc_stages', 2))
        
        # Update registers in place - only if actually changed
        if 'registers' in original_data:
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
                    
                # Only update description if it exists in original file
                if 'description' in file_reg and new_reg.get('description') and new_reg.get('description') != orig_reg.get('description'):
                    original_data['registers'][i]['description'] = new_reg.get('description')
                    
                # Only update default_value if it exists in original file
                if 'default_value' in file_reg and new_reg.get('default_value') != orig_reg.get('default_value'):
                    original_data['registers'][i]['default_value'] = new_reg.get('default_value')
        
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
        new_reg_map = {r.get('name'): r for r in new_registers}
        original_regs = {r.get('reg_name', r.get('signal_name', r.get('name'))): r for r in module.get('registers', [])}
        
        # Update base_address if it changed
        if properties and properties.get('base_address'):
            new_base = properties.get('base_address')
            orig_base = module.get('base_address_raw', module.get('base_address', '0'))
            try:
                orig_base_int = int(orig_base, 16) if isinstance(orig_base, str) and orig_base.startswith('0x') else int(orig_base)
                new_base_int = int(new_base, 16) if isinstance(new_base, str) and new_base.startswith('0x') else int(new_base)
                if new_base_int != orig_base_int:
                    # Replace base_address attribute in module tag
                    content = re.sub(r'(base_address\s*=\s*["\'])([^"\']+)(["\'])', rf'\g<1>0x{new_base_int:04X}\3', content)
            except (ValueError, TypeError):
                pass
        
        def update_register_tag(match):
            """Update a single register tag only for fields that actually changed."""
            tag = match.group(0)
            
            # Extract current name
            name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', tag)
            if not name_match:
                return tag  # Keep original if no name found
                
            reg_name = name_match.group(1)
            if reg_name not in new_reg_map:
                return tag  # Keep original if not being updated
            
            new_reg = new_reg_map[reg_name]
            orig_reg = original_regs.get(reg_name, {})
            
            # Only update attributes that actually changed
            if new_reg.get('access') and new_reg.get('access') != orig_reg.get('access') and re.search(r'access\s*=', tag):
                tag = re.sub(r'access\s*=\s*["\'][^"\']*["\']', f'access="{new_reg.get("access")}"', tag)
            
            # Compare width as integers to avoid type mismatch
            orig_width = orig_reg.get('signal_width', orig_reg.get('width', 32))
            new_width = new_reg.get('width')
            try:
                orig_width_int = int(orig_width) if orig_width else 32
                new_width_int = int(new_width) if new_width else 32
            except (ValueError, TypeError):
                orig_width_int = 32
                new_width_int = 32
                
            if new_width_int != orig_width_int and re.search(r'width\s*=', tag):
                tag = re.sub(r'width\s*=\s*["\'][^"\']*["\']', f'width="{new_width_int}"', tag)
            
            if new_reg.get('description') and new_reg.get('description') != orig_reg.get('description') and re.search(r'description\s*=', tag):
                desc = new_reg.get('description', '').replace('&', '&amp;').replace('"', '&quot;')
                tag = re.sub(r'description\s*=\s*["\'][^"\']*["\']', f'description="{desc}"', tag)
            
            if new_reg.get('default_value') is not None and new_reg.get('default_value') != orig_reg.get('default_value') and re.search(r'default\s*=', tag):
                tag = re.sub(r'default\s*=\s*["\'][^"\']*["\']', f'default="{new_reg.get("default_value")}"', tag)
            
            return tag
        
        # Match <register ... /> or <register ...>...</register> tags
        new_content = re.sub(
            r'<register\s+[^>]*(?:/>|>[^<]*</register>)', 
            update_register_tag, 
            content, 
            flags=re.DOTALL
        )
        
        return new_content, filepath
