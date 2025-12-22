import re
import json
from typing import List, Dict, Any, Tuple
from collections import defaultdict

class RuleChecker:
    """
    Centralized validation logic for Axion HDL modules.
    Performs checks on address integrity, naming conventions, and logical consistency.
    """

    # VHDL Reserved words
    RESERVED_WORDS = {
        'abs', 'access', 'after', 'alias', 'all', 'and', 'architecture', 'array', 'assert', 'attribute', 
        'begin', 'block', 'body', 'buffer', 'bus', 'case', 'component', 'configuration', 'constant', 
        'disconnect', 'downto', 'else', 'elsif', 'end', 'entity', 'exit', 'file', 'for', 'function', 
        'generate', 'generic', 'group', 'guarded', 'if', 'impure', 'in', 'inertial', 'inout', 'is', 
        'label', 'library', 'linkage', 'literal', 'loop', 'map', 'mod', 'nand', 'new', 'next', 'nor', 
        'not', 'null', 'of', 'on', 'open', 'or', 'others', 'out', 'package', 'port', 'postponed', 
        'procedure', 'process', 'pure', 'range', 'record', 'register', 'reject', 'rem', 'report', 
        'return', 'rol', 'ror', 'select', 'severity', 'signal', 'shared', 'sla', 'sll', 'sra', 'srl', 
        'subtype', 'then', 'to', 'transport', 'type', 'unaffected', 'units', 'until', 'use', 'variable', 
        'wait', 'when', 'while', 'with', 'xnor', 'xor'
    }

    def __init__(self):
        # Format: [{'type': str, 'module': str, 'msg': str}]
        self.errors = []
        self.warnings = []

    def _add_error(self, rule_type: str, module_name: str, message: str):
        self.errors.append({
            'type': rule_type,
            'module': module_name,
            'msg': message
        })

    def _add_warning(self, rule_type: str, module_name: str, message: str):
        self.warnings.append({
            'type': rule_type,
            'module': module_name,
            'msg': message
        })

    def check_address_overlaps(self, modules: List[Dict]) -> None:
        """Check for overlapping address ranges between modules."""
        module_ranges = []
        for module in modules:
            base_addr = module.get('base_address', 0x00)
            registers = module.get('registers', [])
            
            if registers:
                max_addr = base_addr
                for reg in registers:
                    reg_addr = reg.get('address_int', 0) 
                    width = int(reg.get('width', 32)) if reg.get('width') else 32
                    byte_width = (width + 7) // 8
                    # reg_addr is absolute address (base + offset)
                    # So end address is just start + size
                    reg_end = reg_addr + max(4, byte_width)
                    max_addr = max(max_addr, reg_end)
                
                module_ranges.append({
                    'name': module['name'],
                    'start': base_addr,
                    'end': max_addr - 1
                })

        # Find overlaps
        overlaps = defaultdict(list)
        for i, m1 in enumerate(module_ranges):
            for m2 in module_ranges[i+1:]:
                # Check intersection: max(start1, start2) <= min(end1, end2)
                overlap_start = max(m1['start'], m2['start'])
                overlap_end = min(m1['end'], m2['end'])
                
                if overlap_start <= overlap_end:
                    # Found overlap
                    msg = f"Address region 0x{m1['start']:X}-0x{m1['end']:X} overlaps with {m2['name']} (0x{m2['start']:X}-0x{m2['end']:X})"
                    overlaps[m1['name']].append(msg)
                    
                    msg2 = f"Address region 0x{m2['start']:X}-0x{m2['end']:X} overlaps with {m1['name']} (0x{m1['start']:X}-0x{m1['end']:X})"
                    overlaps[m2['name']].append(msg2)
        
        # Report errors per module
        for mod_name, messages in overlaps.items():
            for msg in messages:
                self._add_error("Address Overlap", mod_name, msg)

    def check_default_values(self, modules: List[Dict]) -> None:
        """Check if default values fit within register width."""
        for module in modules:
            for reg in module['registers']:
                try:
                    width = int(reg.get('width', 32))
                    default_v = reg.get('default_value', 0)
                    
                    val_int = 0
                    if isinstance(default_v, int):
                        val_int = default_v
                    elif isinstance(default_v, str):
                        if default_v.startswith(('0x', '0X')):
                            val_int = int(default_v, 16)
                        elif default_v.isdigit():
                            val_int = int(default_v)
                    
                    max_val = (1 << width) - 1
                    if val_int > max_val:
                        rname = reg.get('reg_name', reg.get('signal_name', 'unknown_reg'))
                        self._add_error(
                            "Invalid Default Value",
                            module['name'],
                            f"Register '{rname}': 0x{val_int:X} exceeds {width}-bit range (max 0x{max_val:X})"
                        )
                except:
                    pass

    def check_naming_conventions(self, modules: List[Dict]) -> None:
        """Validate VHDL identifier rules and reserved keywords."""
        vhdl_id_pattern = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]*$')
        
        for module in modules:
            if not vhdl_id_pattern.match(module['name']):
                self._add_error("Naming Convention", module['name'], f"Invalid entity name: '{module['name']}'")
            
            if module['name'].lower() in self.RESERVED_WORDS:
                self._add_error("Reserved Keyword", module['name'], f"Module name is reserved keyword")

            for reg in module['registers']:
                rname = reg.get('reg_name', reg.get('signal_name', 'unknown_reg'))
                if not vhdl_id_pattern.match(rname):
                    self._add_error("Naming Convention", module['name'], f"Register '{rname}' invalid identifier")
                if rname.lower() in self.RESERVED_WORDS:
                    self._add_error("Reserved Keyword", module['name'], f"Register '{rname}' is reserved keyword")
                if '__' in rname:
                     self._add_warning("Style Guide", module['name'], f"Register '{rname}' has double underscore")
                if rname.endswith('_'):
                     self._add_warning("Style Guide", module['name'], f"Register '{rname}' has trailing underscore")

    def check_address_alignment(self, modules: List[Dict]) -> None:
        """Check if registers are 4-byte aligned."""
        for module in modules:
            for reg in module['registers']:
                addr = reg.get('address_int')
                if addr is None: 
                    try:
                        raw = reg.get('address', '0')
                        if isinstance(raw, int): addr = raw
                        elif isinstance(raw, str) and raw.startswith('0x'): addr = int(raw, 16)
                        else: addr = int(raw)
                    except: continue

                if addr % 4 != 0:
                    rname = reg.get('reg_name', reg.get('signal_name', 'unknown_reg'))
                    self._add_warning(
                        "Address Alignment",
                        module['name'],
                        f"Register '{rname}' (0x{addr:X}) not 4-byte aligned"
                    )

    def check_duplicate_names(self, modules: List[Dict]) -> None:
        """Check for duplicate register names within a module."""
        for module in modules:
            seen = set()
            for reg in module['registers']:
                name = reg.get('reg_name', reg.get('signal_name', 'unknown_reg'))
                if name in seen:
                    self._add_error("Duplicate Name", module['name'], f"Register '{name}' defined multiple times")
                seen.add(name)

    def check_unique_module_names(self, modules: List[Dict]) -> None:
        """Check for duplicate module names across the project."""
        seen = set()
        duplicates = set()
        for module in modules:
            name = module.get('name')
            if name:
                if name in seen:
                    duplicates.add(name)
                seen.add(name)
        
        for name in duplicates:
            self._add_error("Duplicate Module", name, f"Module name '{name}' is used by multiple files/definitions")

    def _check_single_file(self, filepath: str, exclude_patterns: List[str] = None) -> None:
        """Check a single source file for format issues."""
        import os
        import fnmatch
        import json
        
        exclude_patterns = exclude_patterns or []
        filename = os.path.basename(filepath)
        
        # Check exclusion
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return
            if pattern in filepath:
                return

        # Common field name mistakes and their corrections
        field_suggestions = {
            'name': ('module', "Did you mean 'module' instead of 'name'?"),
            'base_address': ('base_addr', "Did you mean 'base_addr' instead of 'base_address'?"),
            'cdc_enabled': ('config.cdc_en', "Use 'config: { cdc_en: ... }' instead of 'cdc_enabled'"),
            'cdc_stages': ('config.cdc_stage', "Use 'config: { cdc_stage: ... }' instead of 'cdc_stages'"),
        }
        
        register_field_suggestions = {
            'mode': ('access', "Did you mean 'access' instead of 'mode'?"),
            'address': ('addr', "Did you mean 'addr' instead of 'address'?"),
            'r_strobe': None,  # Valid field, no suggestion
            'w_strobe': None,  # Valid field, no suggestion
        }

        ext = os.path.splitext(filename)[1].lower()

        if ext == '.json':
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Check for missing 'module' field
                if 'module' not in data:
                    if 'name' in data:
                        self._add_warning(
                            "Format Issue",
                            filename,
                            f"Missing 'module' field. Did you mean 'module' instead of 'name'?"
                        )
                    else:
                        self._add_warning(
                            "Format Issue",
                            filename,
                            "Missing required 'module' field"
                        )
                
                # Check for wrong field names at root level
                for wrong_field, suggestion in field_suggestions.items():
                    if wrong_field in data and wrong_field != 'name':  # name already checked
                        self._add_warning(
                            "Format Issue",
                            filename,
                            suggestion[1]
                        )
                
                # Check if 'config' section is missing but cdc fields are at root
                if 'config' not in data:
                    if 'cdc_enabled' in data or 'cdc_stages' in data:
                        self._add_warning(
                            "Format Issue",
                            filename,
                            "CDC settings should be in 'config' section: { config: { cdc_en: ..., cdc_stage: ... } }"
                        )
                
                # Check registers format
                if 'registers' in data:
                    for i, reg in enumerate(data['registers']):
                        if 'mode' in reg and 'access' not in reg:
                            self._add_warning(
                                "Format Issue",
                                filename,
                                f"Register {i+1}: Use 'access' instead of 'mode'"
                            )
                        if 'address' in reg and 'addr' not in reg:
                            self._add_warning(
                                "Format Issue",
                                filename,
                                f"Register {i+1}: Use 'addr' instead of 'address'"
                            )
                            
            except json.JSONDecodeError as e:
                self._add_error("Parse Error", filename, f"Invalid JSON: {e}")
            except Exception:
                pass

        elif ext in ['.yaml', '.yml']:
            try:
                import yaml
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                if isinstance(data, dict):
                    if 'module' not in data:
                        if 'name' in data:
                            self._add_warning(
                                "Format Issue",
                                filename,
                                f"Missing 'module' field. Did you mean 'module' instead of 'name'?"
                            )
                        else:
                            self._add_warning(
                                "Format Issue",
                                filename,
                                "Missing required 'module' field"
                            )
                    
                    for wrong_field, suggestion in field_suggestions.items():
                        if wrong_field in data and wrong_field != 'name':
                            self._add_warning(
                                "Format Issue",
                                filename,
                                suggestion[1]
                            )
                    
                    if 'config' not in data:
                        if 'cdc_enabled' in data or 'cdc_stages' in data:
                            self._add_warning(
                                "Format Issue",
                                filename,
                                "CDC settings should be in 'config' section"
                            )
                    
                    if 'registers' in data and isinstance(data['registers'], list):
                        for i, reg in enumerate(data['registers']):
                            if isinstance(reg, dict):
                                if 'mode' in reg and 'access' not in reg:
                                    self._add_warning(
                                        "Format Issue",
                                        filename,
                                        f"Register {i+1}: Use 'access' instead of 'mode'"
                                    )
            except ImportError:
                pass  # PyYAML not installed
            except Exception as e:
                self._add_error("Parse Error", filename, f"Invalid YAML: {e}")

        elif ext == '.xml':
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(filepath)
                root = tree.getroot()
                
                # Check for correct root element
                if root.tag not in ['register_map', 'spirit:component'] and not root.tag.startswith('{'):
                    if root.tag == 'module':
                        self._add_warning(
                            "Format Issue",
                            filename,
                            "Use '<register_map module=\"...\">' as root element instead of '<module>'"
                        )
                    else:
                        self._add_warning(
                            "Format Issue",
                            filename,
                            f"Unknown root element '{root.tag}'. Expected 'register_map'"
                        )
                
                # Check for 'module' attribute in register_map
                if root.tag == 'register_map':
                    if root.get('module') is None:
                        if root.get('name'):
                            self._add_warning(
                                "Format Issue",
                                filename,
                                "Use 'module' attribute instead of 'name' in <register_map>"
                            )
                        else:
                            self._add_warning(
                                "Format Issue",
                                filename,
                                "Missing 'module' attribute in <register_map>"
                            )
            except Exception as e:
                self._add_error("Parse Error", filename, f"Invalid XML: {e}")

    def check_source_file_formats(self, source_dirs: List[str], exclude_patterns: List[str] = None) -> None:
        """
        Check source files for format issues and suggest corrections.
        Scans JSON, YAML, and XML files for common mistakes.
        """
        import os
        import fnmatch
        
        exclude_patterns = exclude_patterns or []
        
        # Scan all source directories
        for src_dir in source_dirs:
            if not os.path.isdir(src_dir):
                continue
            
            for root, dirs, files in os.walk(src_dir):
                # Skip excluded directories
                dirs[:] = [d for d in dirs if not any(fnmatch.fnmatch(d, p) for p in exclude_patterns)]
                
                for filename in files:
                    filepath = os.path.join(root, filename)
                    self._check_single_file(filepath, exclude_patterns)



    def check_documentation(self, modules: List[Dict]) -> None:
        """Check for missing documentation/descriptions."""
        for module in modules:
            name = module.get('name', 'unknown')
            registers = module.get('registers', [])
            undocumented_count = 0
            
            for reg in registers:
                desc = reg.get('description', '').strip()
                if not desc:
                    undocumented_count += 1
            
            if undocumented_count > 0:
                self._add_warning(
                    "Missing Documentation",
                    name,
                    f"{undocumented_count} registers are missing descriptions."
                )

    def check_logical_integrity(self, modules: List[Dict]) -> None:
        """VAL-003: Check logical integrity of modules (e.g., non-empty register lists)."""
        for module in modules:
            name = module.get('name', 'unknown')
            registers = module.get('registers', [])
            
            # Check for empty register list
            if len(registers) == 0:
                self._add_warning(
                    "Logical Integrity",
                    name,
                    "Module has no registers defined."
                )

    def run_all_checks(self, modules: List[Dict]) -> Dict[str, List]:
        self.errors = []
        self.warnings = []
        
        self.check_logical_integrity(modules)
        self.check_documentation(modules)
        self.check_address_overlaps(modules)
        self.check_default_values(modules)
        self.check_naming_conventions(modules)
        self.check_address_alignment(modules)
        self.check_duplicate_names(modules)
        self.check_unique_module_names(modules)
        
        return {
            'errors': self.errors,
            'warnings': self.warnings
        }

    def generate_report(self) -> str:
        """Generate a structured text report."""
        lines = []
        lines.append("\n" + "="*80)
        lines.append(f"{'AXION HDL RULE CHECK REPORT':^80}")
        lines.append("="*80 + "\n")
        
        if not self.errors and not self.warnings:
            lines.append("✅  All checks passed! System is healthy.")
            lines.append("="*80)
            return "\n".join(lines)

        # Helper to print grouped items
        def print_group(title, items, icon):
            if not items: return
            lines.append(f"{icon}  {title} ({len(items)})")
            lines.append("-" * 80)
            
            # Group by Error Type
            by_type = defaultdict(list)
            for item in items:
                by_type[item['type']].append(item)
            
            for rtype, issue_list in by_type.items():
                lines.append(f"  [{rtype}]")
                for issue in issue_list:
                    lines.append(f"    • {issue['module']}: {issue['msg']}")
                lines.append("")
        
        print_group("ERRORS", self.errors, "❌")
        print_group("WARNINGS", self.warnings, "⚠️ ")
            
        lines.append("="*80)
        return "\n".join(lines)

    def generate_json(self) -> str:
        """Generate a JSON report string."""
        report = {
            'errors': self.errors,
            'warnings': self.warnings,
            'summary': {
                'total_errors': len(self.errors),
                'total_warnings': len(self.warnings),
                'passed': len(self.errors) == 0
            }
        }
        return json.dumps(report, indent=4)
