import os
import re
import difflib
from typing import List, Dict, Tuple, Optional

class SourceModifier:
    def __init__(self, axion_instance):
        self.axion = axion_instance

    def _generate_vhdl_signal(self, reg: Dict) -> str:
        """Generate VHDL signal declaration for a new register."""
        name = reg['name']
        sig_type = reg['type']  # 'std_logic' or 'std_logic_vector'
        
        # Add attributes if description exists? 
        # -- @axion: reg_name=...
        
        lines = []
        if reg.get('description'):
            lines.append(f"    -- {reg['description']}")
            
        width_suffix = "(31 downto 0)" if 'vector' in sig_type.lower() else ""
        default_val = " := (others => '0')" if 'vector' in sig_type.lower() else " := '0'"
        
        # Axion attributes
        # attribute axion_reg : string;
        # attribute axion_reg of name : signal is "access=RW";
        
        # For simplicity, we just add the signal declaration currently.
        # Users might need to add attributes manually or we inject comments that Axion parses?
        # Axion parses comments! -- @axion: access=RW
        
        access = reg.get('access', 'RW')
        lines.append(f"    signal {name} : {sig_type}{width_suffix}{default_val}; -- @axion: access={access}")
        
        return "\n".join(lines)

    def get_modified_content(self, module_name: str, new_registers: List[Dict]) -> Tuple[str, str]:
        """
        Generates the new content for the file associated with the module.
        Only handles adding NEW registers (signals).
        """
        module = next((m for m in self.axion.analyzed_modules if m['name'] == module_name), None)
        if not module:
            raise ValueError(f"Module {module_name} not found")

        filepath = module['file']
        with open(filepath, 'r') as f:
            content = f.read()

        # Identify existing signals to avoid duplicates
        existing_names = set()
        for r in module['registers']:
            existing_names.add(r.get('reg_name'))
            existing_names.add(r.get('signal_name'))
            if r.get('is_packed') and r.get('fields'):
                for f in r['fields']:
                    existing_names.add(f.get('signal_name'))
        
        lines_to_inject = []
        
        for reg in new_registers:
            # Check if this register name is new
            # Comparison is simple name check
            if reg['name'] not in existing_names:
                lines_to_inject.append(self._generate_vhdl_signal(reg))
        
        if not lines_to_inject:
            return content, filepath # No changes needed

        # Injection Strategy:
        # Find 'architecture ... is' 
        # Then find the 'begin' keyword that starts the body.
        # Insert signals before 'begin'.
        
        # Regex to find architecture start
        arch_pattern = r'architecture\s+\w+\s+of\s+\w+\s+is'
        arch_match = re.search(arch_pattern, content, re.IGNORECASE)
        
        if not arch_match:
            # Fallback or error? Return unchanged for safety
            return content, filepath
            
        search_start_idx = arch_match.end()
        
        # Find the first 'begin' after architecture declaration
        # Use word boundary \b to avoid matching inside words
        begin_match = re.search(r'\bbegin\b', content[search_start_idx:], re.IGNORECASE)
        
        if begin_match:
            insert_pos = search_start_idx + begin_match.start()
            
            # Create injection block
            injection = "\n    -- Axion-HDL Auto-Injected Signals\n"
            injection += "\n".join(lines_to_inject)
            injection += "\n"
            
            new_content = content[:insert_pos] + injection + content[insert_pos:]
            return new_content, filepath
            
        return content, filepath

    def compute_diff(self, module_name: str, new_registers: List[Dict]) -> Optional[str]:
        """Returns the unified diff between original and modified content."""
        try:
            new_content, filepath = self.get_modified_content(module_name, new_registers)
            original_content = open(filepath, 'r').read()
            
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

    def save_changes(self, module_name: str, new_registers: List[Dict]) -> bool:
        """Writes the modified content to disk."""
        new_content, filepath = self.get_modified_content(module_name, new_registers)
        with open(filepath, 'w') as f:
            f.write(new_content)
        return True
