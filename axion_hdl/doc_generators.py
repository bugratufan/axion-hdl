"""
Documentation Generator Module for Axion HDL

This module generates register documentation in various formats.
Uses axion_hdl for code formatting utilities.
"""

import html as _html
import os
import re
import sys
from typing import Dict, List

# Import from axion_hdl (unified package)
from axion_hdl.code_formatter import CodeFormatter


class DocGenerator:
    """Generator for creating register documentation."""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.formatter = CodeFormatter()
        
    def generate_markdown(self, modules: List[Dict]) -> str:
        """Generate Markdown documentation."""
        output_path = os.path.join(self.output_dir, "register_map.md")
        
        lines = [
            "# AXI Register Map Documentation",
            "",
            "---",
            ""
        ]
        
        for module in modules:
            lines.extend(self._generate_module_section(module))
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
            
        return output_path
    
    def _generate_module_section(self, module: Dict) -> List[str]:
        """Generate documentation section for one module."""
        base_addr = module.get('base_address', 0x00)
        base_addr_str = f"0x{base_addr:04X}" if base_addr != 0 else "0x0000"
        
        display_name = module.get('_effective_name', module['name'])
        lines = [
            f"## Module: {display_name}",
            "",
            f"**Source File:** `{os.path.basename(module['file'])}`  ",
            f"**Base Address:** {base_addr_str}  ",
            f"**CDC:** {'Enabled' if module['cdc_enabled'] else 'Disabled'}",
        ]
        
        if module['cdc_enabled']:
            lines.append(f"**CDC Stages:** {module['cdc_stages']}")
        
        lines.extend([
            "",
            "### Register Map",
            "",
            "| Address | Offset | Register Name | Type | Width | Access | Default | Description |",
            "|---------|--------|---------------|------|-------|--------|---------|-------------|"
        ])
        
        # Group registers: standalone vs packed
        # For packed registers, we want to show the main 32-bit register first
        # We need to detect which registers are packed (is_packed=True)
        # But for the register map table, we should list the ADDR/OFFSET only once for the whole register.
        
        # Helper to group registers by address/name
        grouped_regs = {}
        processed_packed_names = set()
        
        for reg in module['registers']:
            if reg.get('is_packed'):
                # Group by actual register name (reg_name)
                packed_name = reg['reg_name']
                if packed_name not in grouped_regs:
                    grouped_regs[packed_name] = {
                        'type': 'packed',
                        'fields': [],
                        'info': reg # Keep one reg as info source for address/access
                    }
                grouped_regs[packed_name]['fields'].append(reg)
            else:
                grouped_regs[reg['signal_name']] = {
                    'type': 'standalone',
                    'info': reg
                }
                
        # To maintain order, iterate original list but skip already processed packed groups
        shown_groups = set()
        
        for reg in module['registers']:
            name_key = reg['reg_name'] if reg.get('is_packed') else reg['signal_name']
            
            if name_key in shown_groups:
                continue
            shown_groups.add(name_key)
            
            group = grouped_regs[name_key]
            info = group['info']
            
            offset = info.get('relative_address', info['address'])
            # Use grouped reg_name for packed, otherwise signal_name
            display_name = name_key 
            
            # Access: mixed for packed? Usually RW or RO. Take from first field.
            access = info['access_mode']
            
            # Default: For standalone, take 'default'. For packed, show 'Mixed' or combined hex if possible?
            # Let's show the combined default if available processing, or just Listing
            # Actually, generator logic combines defaults into the main register default.
            # But here we might not have that easily. Let's just default to '-' for packed row, and details in description.
            default_val = info.get('default_value') or '-'
            if default_val != '-':
                 default_val = f"0x{int(default_val):X}"
            
            desc = info.get('description', '-')
            
            if group['type'] == 'packed':
                # Show main register row
                lines.append(
                    f"| {info['address']} | {offset} | `{display_name}` | | 32 | "
                    f"{access} | {default_val} | **Packed Register** (see below) |"
                )
            else:
                lines.append(
                    f"| {info['address']} | {offset} | `{display_name}` | {info['signal_type']} | {info.get('width', 32)} | "
                    f"{access} | {default_val} | {desc} |"
                )
        
        lines.extend([
            "",
            "### Port Descriptions",
            ""
        ])
        
        # Reset shown groups for port section
        shown_groups = set()
        
        for reg in module['registers']:
            name_key = reg['reg_name'] if reg.get('is_packed') else reg['signal_name']
            if name_key in shown_groups:
                continue
            shown_groups.add(name_key)
            
            group = grouped_regs[name_key]
            info = group['info']
            
            lines.append(f"#### {name_key}")
            
            if group['type'] == 'packed':
                lines.append(f"**Packed Register** - Address: {info['address']} (Offset: {info.get('relative_address', info['address'])})")
                lines.append("")

                # Check if register has embedded 'fields' array (YAML/JSON input)
                # This array contains actual subfields with bit_low/bit_high info
                embedded_fields = info.get('fields', [])
                if embedded_fields and isinstance(embedded_fields, list) and len(embedded_fields) > 0:
                    # Use embedded fields from YAML/JSON parser - sort by bit_low (high to low)
                    sorted_fields = sorted(embedded_fields, key=lambda f: int(f.get('bit_low', 0)), reverse=True)

                    has_enum = any(f.get('enum_values') for f in sorted_fields)
                    if has_enum:
                        lines.append("| Field | Bits | Type | Access | Default | Description | Enum Values |")
                        lines.append("|-------|------|------|--------|---------|-------------|-------------|")
                    else:
                        lines.append("| Field | Bits | Type | Access | Default | Description |")
                        lines.append("|-------|------|------|--------|---------|-------------|")

                    for field in sorted_fields:
                        fname = field.get('name', 'unknown')
                        bit_low = int(field.get('bit_low', 0))
                        bit_high = int(field.get('bit_high', bit_low))
                        width = int(field.get('width', 1))
                        bit_range = f"[{bit_low}]" if width == 1 else f"[{bit_high}:{bit_low}]"
                        fdefault = field.get('default_value', '-')
                        if fdefault != '-' and fdefault != 0:
                            fdefault = f"0x{int(fdefault):X}"
                        elif fdefault == 0:
                            fdefault = "0x0"
                        fdesc = field.get('description', '-')
                        ftype = field.get('signal_type', f"[{width-1}:0]" if width > 1 else "[0:0]")
                        faccess = field.get('access_mode', info['access_mode'])

                        if has_enum:
                            enum_dict = field.get('enum_values')
                            if enum_dict:
                                enum_str = ', '.join(f"{k}:{v}" for k, v in sorted(enum_dict.items()))
                            else:
                                enum_str = '-'
                            lines.append(f"| `{fname}` | {bit_range} | {ftype} | {faccess} | {fdefault} | {fdesc} | {enum_str} |")
                        else:
                            lines.append(f"| `{fname}` | {bit_range} | {ftype} | {faccess} | {fdefault} | {fdesc} |")
                else:
                    # Fallback: use grouped fields from VHDL parser
                    # Sort fields by bit offset (high to low - MSB first)
                    sorted_fields = sorted(group['fields'], key=lambda r: int(r.get('bit_offset', 0)), reverse=True)

                    has_enum = any(f.get('enum_values') for f in sorted_fields)
                    if has_enum:
                        lines.append("| Field | Bits | Type | Access | Default | Description | Enum Values |")
                        lines.append("|-------|------|------|--------|---------|-------------|-------------|")
                    else:
                        lines.append("| Field | Bits | Type | Access | Default | Description |")
                        lines.append("|-------|------|------|--------|---------|-------------|")

                    for field in sorted_fields:
                        fname = field['signal_name']
                        offset = int(field.get('bit_offset', 0))
                        width = int(field.get('width', 1))
                        bit_range = f"[{offset}]" if width == 1 else f"[{offset+width-1}:{offset}]"
                        fdefault = field.get('default_value', '-')
                        if fdefault != '-':
                            fdefault = f"0x{int(fdefault):X}"
                        fdesc = field.get('description', '-')

                        if has_enum:
                            enum_dict = field.get('enum_values')
                            if enum_dict:
                                enum_str = ', '.join(f"{k}:{v}" for k, v in sorted(enum_dict.items()))
                            else:
                                enum_str = '-'
                            lines.append(f"| `{fname}` | {bit_range} | {field['signal_type']} | {field['access_mode']} | {fdefault} | {fdesc} | {enum_str} |")
                        else:
                            lines.append(f"| `{fname}` | {bit_range} | {field['signal_type']} | {field['access_mode']} | {fdefault} | {fdesc} |")
                lines.append("")
                
            else:
                # Standalone
                description = info.get('description', '')
                if description:
                    lines.append(f"*{description}*")
                    lines.append("")
                lines.append(f"- **Address:** {info['address']}")
                lines.append(f"- **Offset:** {info.get('relative_address', info['address'])}")
                lines.append(f"- **Access Mode:** {info['access_mode']}")
                defs = info.get('default_value') or '-'
                if defs != '-': defs = f"0x{int(defs):X}"
                lines.append(f"- **Default:** {defs}")
                lines.append(f"- **Type:** `std_logic_vector(31 downto 0)`")
                lines.append("")
                lines.append("**Ports:**")
                lines.append(f"- `{info['signal_name']}` (inout): Register data signal")
                
                if info['read_strobe']:
                    lines.append(f"- `{info['signal_name']}_rd_strobe` (out): Read strobe pulse")
                if info['write_strobe']:
                    lines.append(f"- `{info['signal_name']}_wr_strobe` (out): Write strobe pulse")
                if info['access_mode'] in ['RO', 'RW']:
                    lines.append(f"- `{info['signal_name']}_wr_en` (in): Write enable from VHDL logic")
            
            lines.append("")
        
        lines.extend([
            "---",
            ""
        ])
        
        return lines
    
    def generate_html(self, modules: List[Dict]) -> str:
        """
        Generate multi-page HTML documentation with embedded CSS styling.
        
        Creates:
        - index.html: Main page with module list and links (in output root)
        - html/{module_name}.html: Separate page for each module (in html/ subdir)
        - html/about.html: About Axion-HDL page with project info
        
        Returns:
            Path to index.html
        """
        # Create html subdirectory for module pages
        html_dir = os.path.join(self.output_dir, "html")
        os.makedirs(html_dir, exist_ok=True)
        
        # Create index page in ROOT output dir
        index_path = os.path.join(self.output_dir, "index.html")
        index_content = self._generate_index_page(modules)
        
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        # Create individual module pages in html/ subdir
        for module in modules:
            page_name = module.get('_effective_name', module['name'])
            module_path = os.path.join(html_dir, f"{page_name}.html")
            module_content = self._generate_module_page(module, modules)
            
            with open(module_path, 'w', encoding='utf-8') as f:
                f.write(module_content)
        
        # Create about page in html/ subdir
        about_path = os.path.join(html_dir, "about.html")
        about_content = self._generate_about_page()
        with open(about_path, 'w', encoding='utf-8') as f:
            f.write(about_content)
        
        # Also create legacy single-file for backwards compatibility
        legacy_path = os.path.join(self.output_dir, "register_map.html")
        legacy_content = self._generate_single_page_html(modules)
        with open(legacy_path, 'w', encoding='utf-8') as f:
            f.write(legacy_content)
            
        return index_path
    
    def _generate_index_page(self, modules: List[Dict]) -> str:
        """Generate the main index.html page with module list."""
        total_regs = sum(len(m.get('registers', [])) for m in modules)
        
        # Check for overlapping address ranges
        module_ranges = []
        for module in modules:
            if 'address_range_start' in module and 'address_range_end' in module:
                module_ranges.append({
                    'name': module['name'],
                    'start': module['address_range_start'],
                    'end': module['address_range_end']
                })
        
        overlaps = []
        for i, m1 in enumerate(module_ranges):
            for m2 in module_ranges[i+1:]:
                if m1['start'] <= m2['end'] and m2['start'] <= m1['end']:
                    overlap_start = max(m1['start'], m2['start'])
                    overlap_end = min(m1['end'], m2['end'])
                    overlaps.append({
                        'm1': m1['name'],
                        'm2': m2['name'],
                        'm1_range': f"0x{m1['start']:04X} - 0x{m1['end']:04X}",
                        'm2_range': f"0x{m2['start']:04X} - 0x{m2['end']:04X}",
                        'overlap_range': f"0x{overlap_start:04X} - 0x{overlap_end:04X}"
                    })
        
        content = f'''
<div class="top-nav">
    <a href="html/about.html" class="about-link">About Axion-HDL</a>
</div>
<div class="hero">
    <div class="hero-logo">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="-10 145 880 170" width="480" height="93" aria-label="Axion-HDL">
            <defs>
                <mask id="dot-mask-hero">
                    <rect x="-500" y="-500" width="1500" height="1500" fill="white"/>
                    <circle cx="24" cy="-1" r="22" fill="black"/>
                </mask>
            </defs>
            <g transform="translate(250, 250)">
                <g mask="url(#dot-mask-hero)">
                    <text x="0" y="46" text-anchor="middle" font-family="'Arial Black', 'Helvetica Neue', sans-serif" font-weight="900" font-size="130" fill="#ffffff">AXI<tspan fill="#2f81f7">ON</tspan></text>
                    <text x="250" y="46" text-anchor="start" font-family="'Arial Black', 'Helvetica Neue', sans-serif" font-weight="900" font-size="130" fill="#ffffff">-HDL</text>
                </g>
                <circle cx="24" cy="-1" r="16" fill="#2f81f7"/>
            </g>
        </svg>
    </div>
    <p class="subtitle">AXI Register Map Documentation</p>
    <div class="stats">
        <div class="stat">
            <span class="stat-value">{len(modules)}</span>
            <span class="stat-label">Modules</span>
        </div>
        <div class="stat">
            <span class="stat-value">{total_regs}</span>
            <span class="stat-label">Registers</span>
        </div>
    </div>
</div>
'''
        
        # Add overlap warning if any
        if overlaps:
            content += '''
<div class="overlap-warning">
    <div class="warning-header">
        <span class="warning-title">Address Overlap Detected</span>
    </div>
    <div class="warning-content">
'''
            for overlap in overlaps:
                content += f'''
        <div class="overlap-item">
            <div class="overlap-modules">
                <span class="module-name">{overlap['m1']}</span>
                <span class="range">{overlap['m1_range']}</span>
                <span class="overlap-symbol">↔</span>
                <span class="module-name">{overlap['m2']}</span>
                <span class="range">{overlap['m2_range']}</span>
            </div>
            <div class="overlap-region">Overlap: {overlap['overlap_range']}</div>
        </div>
'''
            content += '''
    </div>
</div>
'''
        
        content += '''
<h2>Modules</h2>
<div class="module-list">
'''
        for module in modules:
            base_addr = module.get('base_address', 0)
            registers = module.get('registers', [])
            reg_count = len(registers)
            cdc_badge = '<span class="badge badge-cdc">CDC</span>' if module.get('cdc_enabled') else ''
            
            # Calculate address range
            range_start = module.get('address_range_start', base_addr)
            range_end = module.get('address_range_end', base_addr)
            range_str = f"0x{range_start:04X} - 0x{range_end:04X}"
            
            # Generate register preview (first 5 registers)
            reg_preview = ''
            for i, reg in enumerate(registers[:5]):
                reg_name = reg.get('signal_name', 'unknown')
                reg_addr = reg.get('relative_address', '0x00')
                reg_access = reg.get('access_mode', 'RW')
                reg_preview += f'<div class="reg-item"><code>{reg_name}</code><span class="reg-meta">{reg_addr} • {reg_access}</span></div>'
            
            if reg_count > 5:
                reg_preview += f'<div class="reg-more">+{reg_count - 5} more registers...</div>'
            
            page_name = module.get('_effective_name', module['name'])
            display_name = module.get('_effective_name', module['name'])
            content += f'''
    <a href="html/{page_name}.html" class="module-card-large">
        <div class="module-main">
            <div class="module-header">
                <h3>{display_name}</h3>
                {cdc_badge}
            </div>
            <div class="module-info">
                <div class="info-item">
                    <span class="info-label">Address Range</span>
                    <span class="info-value">{range_str}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Registers</span>
                    <span class="info-value">{reg_count}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Source</span>
                    <span class="info-value">{os.path.basename(module['file'])}</span>
                </div>
            </div>
        </div>
        <div class="register-preview">
            <div class="preview-title">Registers</div>
            {reg_preview}
        </div>
    </a>
'''
        
        content += '</div>'
        
        return self._wrap_html_with_style(content, title="AXI Register Map", is_index=True)
    
    def _generate_module_page(self, module: Dict, all_modules: List[Dict]) -> str:
        """Generate individual module page with navigation."""
        # Generate markdown content for this module
        md_lines = self._generate_module_section(module)
        md_content = '\n'.join(md_lines)
        
        # Convert to HTML
        html_content = self._markdown_to_html(md_content)
        
        # Add navigation
        nav_html = self._generate_navigation(module, all_modules)
        
        full_content = nav_html + html_content
        
        return self._wrap_html_with_style(
            full_content,
            title=f"{module.get('_effective_name', module['name'])} - AXI Register Map",
            is_index=False
        )
    
    def _generate_navigation(self, current_module: Dict, all_modules: List[Dict]) -> str:
        """Generate navigation bar for module pages."""
        current_page = current_module.get('_effective_name', current_module['name'])
        idx = next((i for i, m in enumerate(all_modules)
                    if m.get('_effective_name', m['name']) == current_page), 0)
        prev_module = all_modules[idx - 1] if idx > 0 else None
        next_module = all_modules[idx + 1] if idx < len(all_modules) - 1 else None

        def _page(m):
            return m.get('_effective_name', m['name'])

        prev_link = f'<a href="{_page(prev_module)}.html" class="nav-link">← {_page(prev_module)}</a>' if prev_module else '<span></span>'
        next_link = f'<a href="{_page(next_module)}.html" class="nav-link">{_page(next_module)} →</a>' if next_module else '<span></span>'

        return f'''
<nav class="breadcrumb">
    <a href="../index.html">All Modules</a>
    <span class="separator">›</span>
    <span class="current">{current_page}</span>
</nav>
<div class="page-nav">
    {prev_link}
    {next_link}
</div>
'''
    
    def _generate_single_page_html(self, modules: List[Dict]) -> str:
        """Generate legacy single-page HTML for backwards compatibility."""
        md_lines = [
            "# AXI Register Map Documentation",
            "",
            "---",
            ""
        ]
        
        for module in modules:
            md_lines.extend(self._generate_module_section(module))
        
        md_content = '\n'.join(md_lines)
        html_content = self._markdown_to_html(md_content)
        
        return self._wrap_html_with_style(html_content, title="AXI Register Map")
    
    def _generate_about_page(self) -> str:
        """Generate About Axion-HDL page with README.md content."""
        # Try to find and read README.md
        readme_content = self._read_readme()
        
        if readme_content:
            # Convert README markdown to HTML using enhanced converter
            readme_html = self._convert_readme_to_html(readme_content)
        else:
            readme_html = "<p>README.md not found</p>"
        
        content = f'''
<nav class="breadcrumb">
    <a href="../index.html">All Modules</a>
    <span class="separator">›</span>
    <span class="current">About Axion-HDL</span>
</nav>

<div class="readme-container">
    {readme_html}
</div>

<div class="about-links">
    <h2>Quick Links</h2>
    <div class="link-grid">
        <a href="https://github.com/bugratufan/axion-hdl" class="link-card" target="_blank">
            <div class="link-info">
                <h3>GitHub</h3>
                <p>Source code &amp; issues</p>
            </div>
        </a>
        <a href="https://pypi.org/project/axion-hdl/" class="link-card" target="_blank">
            <div class="link-info">
                <h3>PyPI</h3>
                <p>pip install axion-hdl</p>
            </div>
        </a>
        <a href="https://axion-hdl.readthedocs.io/" class="link-card" target="_blank">
            <div class="link-info">
                <h3>Documentation</h3>
                <p>Full user guide</p>
            </div>
        </a>
    </div>
</div>
'''
        return self._wrap_html_with_style(content, title="About Axion-HDL")
    
    def _read_readme(self) -> str:
        """Try to read README.md from various locations."""
        import importlib.resources
        
        # Try multiple possible README locations
        possible_paths = [
            # Installed package - try to find relative to module
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'README.md'),
            # Development environment
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'README.md'),
            # Current working directory
            os.path.join(os.getcwd(), 'README.md'),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception:
                    continue
        
        # Fallback: embedded minimal content
        return """
# Axion-HDL

**Automated AXI Register Space Generation Tool**

Axion-HDL automatically generates AXI4-Lite register interfaces from annotated VHDL source files or IP-XACT XML definitions.

## 🚀 Quick Start

```bash
pip install axion-hdl
axion-hdl -s your_vhdl_dir/ -o output/ --vhdl --header --doc
```

## ✨ Features

- **VHDL Annotations**: Simple `@axion` comments
- **Multi-Format Output**: VHDL, C headers, XML, JSON, YAML, HTML, PDF
- **CDC Support**: Built-in Clock Domain Crossing
- **Wide Signals**: Automatic handling of >32-bit signals

For full documentation, visit [axion-hdl.readthedocs.io](https://axion-hdl.readthedocs.io/)
"""


    
    def _markdown_to_html(self, md_content: str) -> str:
        """Convert markdown to HTML (simple converter without external deps)."""
        import re
        
        lines = md_content.split('\n')
        html_lines = []
        in_table = False
        table_header_done = False
        in_list = False
        
        for line in lines:
            # Headers
            if line.startswith('# '):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<h1>{line[2:]}</h1>')
            elif line.startswith('## '):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<h2>{line[3:]}</h2>')
            elif line.startswith('### '):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                heading_text = line[4:]
                if heading_text == "Register Map":
                    html_lines.append(f'<h3 id="register-table">{heading_text}</h3>')
                else:
                    html_lines.append(f'<h3>{heading_text}</h3>')
            elif line.startswith('#### '):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                # This is a register name - add ID for anchor linking
                reg_name = line[5:].strip()
                anchor_id = reg_name.replace('_', '-').lower()
                html_lines.append(f'<h4 id="reg-{anchor_id}">{reg_name}</h4>')
            # Horizontal rule
            elif line.strip() == '---':
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append('<hr>')
            # Table
            elif line.strip().startswith('|') and line.strip().endswith('|'):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                # Check if separator line
                if re.match(r'^\|[\s\-:|]+\|$', line.strip()):
                    table_header_done = True
                    continue
                
                if not in_table:
                    html_lines.append('<table>')
                    in_table = True
                    table_header_done = False
                
                cells = [c.strip() for c in line.strip().split('|')[1:-1]]
                if not table_header_done:
                    html_lines.append('<thead><tr>')
                    for cell in cells:
                        cell = self._process_inline_markdown(cell)
                        html_lines.append(f'<th>{cell}</th>')
                    html_lines.append('</tr></thead><tbody>')
                else:
                    # Logic to find register name cell (usually index 2) to set Row ID
                    row_attr = ''
                    reg_col_idx = 2  # Based on generator format: Addr | Offset | Name | ...
                    
                    if len(cells) > reg_col_idx and '`' in cells[reg_col_idx]:
                        import re
                        reg_match = re.search(r'`([^`]+)`', cells[reg_col_idx])
                        if reg_match:
                            r_name = reg_match.group(1)
                            r_id = r_name.replace('_', '-').lower()
                            row_attr = f' id="row-reg-{r_id}"'
                            
                    html_lines.append(f'<tr{row_attr}>')
                    for i, cell in enumerate(cells):
                        cell = self._process_inline_markdown(cell)
                        # Make register name column clickable
                        if i == reg_col_idx and '<code>' in cell:
                            # Extract register name from <code>name</code>
                            # cell is like "<code>reg_name</code>"
                            # We want <a href="#reg-id"><code>reg_name</code></a>
                            import re
                            # Use regex to be safe against extra spaces or tags
                            m = re.search(r'<code>(.*?)</code>', cell)
                            if m:
                                r_name = m.group(1)
                                r_id = r_name.replace('_', '-').lower()
                                cell = f'<a href="#reg-{r_id}">{cell}</a>'
                        html_lines.append(f'<td>{cell}</td>')
                    html_lines.append('</tr>')
            # List item
            elif line.strip().startswith('- '):
                if in_table:
                    html_lines.append('</tbody></table>')
                    in_table = False
                    table_header_done = False
                if not in_list:
                    html_lines.append('<ul>')
                    in_list = True
                content = self._process_inline_markdown(line.strip()[2:])
                html_lines.append(f'<li>{content}</li>')
            # Paragraph / other content
            elif line.strip():
                if in_table:
                    html_lines.append('</tbody></table>')
                    in_table = False
                    table_header_done = False
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                content = self._process_inline_markdown(line)
                html_lines.append(f'<p>{content}</p>')
            else:
                # Empty line
                if in_table:
                    html_lines.append('</tbody></table>')
                    in_table = False
                    table_header_done = False
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
        
        # Close any remaining open tags
        if in_table:
            html_lines.append('</tbody></table>')
        if in_list:
            html_lines.append('</ul>')
        
        return '\n'.join(html_lines)
    
    def _process_inline_markdown(self, text: str) -> str:
        """Process inline markdown elements like bold, italic, code."""
        import re
        
        # Code (backticks)
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        # Bold
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        # Italic
        text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
        
        return text
    
    def _convert_readme_to_html(self, md_content: str) -> str:
        """Convert README markdown to HTML using markdown library or enhanced fallback."""
        # Try to use the markdown library for better rendering
        try:
            import markdown
            html = markdown.markdown(
                md_content,
                extensions=['tables', 'fenced_code', 'codehilite', 'toc']
            )
            return html
        except ImportError:
            pass
        
        # Enhanced fallback converter for README
        import re
        
        lines = md_content.split('\n')
        html_lines = []
        in_code_block = False
        code_lang = ''
        code_content = []
        in_list = False
        
        for line in lines:
            # Code blocks (```)
            if line.strip().startswith('```'):
                if in_code_block:
                    # End code block
                    html_lines.append(f'<pre><code class="{code_lang}">{chr(10).join(code_content)}</code></pre>')
                    code_content = []
                    in_code_block = False
                else:
                    # Start code block
                    code_lang = line.strip()[3:] or 'text'
                    in_code_block = True
                continue
            
            if in_code_block:
                # Escape HTML in code
                escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                code_content.append(escaped)
                continue
            
            # Headers
            if line.startswith('# '):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<h1>{self._process_readme_inline(line[2:])}</h1>')
            elif line.startswith('## '):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<h2>{self._process_readme_inline(line[3:])}</h2>')
            elif line.startswith('### '):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<h3>{self._process_readme_inline(line[4:])}</h3>')
            # List items
            elif line.strip().startswith('- ') or line.strip().startswith('* '):
                if not in_list:
                    html_lines.append('<ul>')
                    in_list = True
                text = line.strip()[2:]
                html_lines.append(f'<li>{self._process_readme_inline(text)}</li>')
            # Horizontal rule
            elif line.strip() == '---' or line.strip() == '***':
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append('<hr>')
            # Paragraph
            elif line.strip():
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<p>{self._process_readme_inline(line)}</p>')
        
        if in_list:
            html_lines.append('</ul>')
        
        return '\n'.join(html_lines)
    
    def _process_readme_inline(self, text: str) -> str:
        """Process inline markdown with links, images, badges, etc."""
        import re
        
        # Images with links: [![alt](img)](link)
        text = re.sub(
            r'\[\!\[([^\]]*)\]\(([^)]+)\)\]\(([^)]+)\)',
            r'<a href="\3"><img src="\2" alt="\1"></a>',
            text
        )
        
        # Images: ![alt](url)
        text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', text)
        
        # Links: [text](url)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        
        # Inline code: `code`
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        
        # Bold: **text**
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        
        # Italic: *text*
        text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
        
        return text
    
    def _wrap_html_with_style(self, content: str, title: str = "AXI Register Map", is_index: bool = False) -> str:
        """Wrap HTML content with full document structure and CSS."""
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgLTcwIDE0MCAxNDAiIHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIj4KICA8ZGVmcz4KICAgIDxtYXNrIGlkPSJkb3QtbWFzayI+CiAgICAgIDxyZWN0IHg9Ii01MDAiIHk9Ii01MDAiIHdpZHRoPSIxNTAwIiBoZWlnaHQ9IjE1MDAiIGZpbGw9IndoaXRlIi8+CiAgICAgIDxjaXJjbGUgY3g9IjI0IiBjeT0iLTEiIHI9IjIyIiBmaWxsPSJibGFjayIvPgogICAgPC9tYXNrPgogIDwvZGVmcz4KCiAgPGcgbWFzaz0idXJsKCNkb3QtbWFzaykiPgogICAgPHRleHQgeD0iMCIgeT0iNDYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtZmFtaWx5PSInQXJpYWwgQmxhY2snLCAnSGVsdmV0aWNhIE5ldWUnLCBzYW5zLXNlcmlmIiBmb250LXdlaWdodD0iOTAwIiBmb250LXNpemU9IjEzMCIgZmlsbD0ibm9uZSI+CiAgICAgIEFYSTx0c3BhbiBmaWxsPSIjMmY4MWY3Ij5PPC90c3Bhbj5OCiAgICA8L3RleHQ+CiAgPC9nPgoKICA8Y2lyY2xlIGN4PSIyNCIgY3k9Ii0xIiByPSIxNiIgZmlsbD0iIzJmODFmNyIvPgo8L3N2Zz4K">
    <style>
        :root {{
            --primary-color: #2563eb;
            --primary-dark: #1d4ed8;
            --bg-color: #f8fafc;
            --text-color: #1e293b;
            --border-color: #e2e8f0;
            --code-bg: #f1f5f9;
            --card-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
        }}
        
        * {{
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            background-color: var(--bg-color);
        }}
        
        /* Hero Section */
        .hero {{
            text-align: center;
            padding: 2rem;
            margin-bottom: 2rem;
            background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
            border-radius: 16px;
            color: white;
        }}
        
        .hero-logo {{
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 0;
        }}
        
        .hero-logo svg {{
            max-width: 100%;
            height: auto;
        }}
        
        .hero h1 {{
            color: white;
            border: none;
            margin: 0;
            font-size: 2rem;
        }}
        
        .hero .subtitle {{
            opacity: 0.9;
            margin: 0.1rem 0 1.5rem 0;
            font-size: 1.1rem;
            font-weight: 500;
        }}
        
        .stats {{
            display: flex;
            justify-content: center;
            gap: 3rem;
        }}
        
        .stat {{
            display: flex;
            flex-direction: column;
        }}
        
        .stat-value {{
            font-size: 2.5rem;
            font-weight: bold;
        }}
        
        .stat-label {{
            opacity: 0.8;
            font-size: 0.9rem;
        }}
        
        /* Module Grid */
        .module-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1.5rem;
            margin: 1.5rem 0;
        }}
        
        .module-card {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: var(--card-shadow);
            text-decoration: none;
            color: inherit;
            transition: transform 0.2s, box-shadow 0.2s;
            border: 1px solid var(--border-color);
        }}
        
        .module-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.15);
        }}
        
        .module-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }}
        
        .module-header h3 {{
            margin: 0;
            color: var(--primary-color);
            font-size: 1.2rem;
        }}
        
        .badge {{
            font-size: 0.7rem;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-weight: 600;
        }}
        
        .badge-cdc {{
            background: #dcfce7;
            color: #166534;
        }}
        
        .module-info {{
            display: flex;
            gap: 1.5rem;
            margin-bottom: 1rem;
        }}
        
        .info-item {{
            display: flex;
            flex-direction: column;
        }}
        
        .info-label {{
            font-size: 0.75rem;
            color: #64748b;
            text-transform: uppercase;
        }}
        
        .info-value {{
            font-weight: 600;
            font-family: 'Monaco', 'Menlo', monospace;
        }}
        
        .module-source {{
            font-size: 0.8rem;
            color: #64748b;
            padding-top: 0.75rem;
            border-top: 1px solid var(--border-color);
        }}
        
        /* Overlap Warning */
        .overlap-warning {{
            background: #fef2f2;
            border: 2px solid #ef4444;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1.5rem 0;
        }}
        
        .warning-header {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1rem;
        }}
        
        .warning-icon {{
            font-size: 1.5rem;
        }}
        
        .warning-title {{
            font-size: 1.2rem;
            font-weight: 700;
            color: #dc2626;
        }}
        
        .warning-content {{
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }}
        
        .overlap-item {{
            background: white;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #fca5a5;
        }}
        
        .overlap-modules {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            flex-wrap: wrap;
            margin-bottom: 0.5rem;
        }}
        
        .overlap-modules .module-name {{
            font-weight: 600;
            color: #dc2626;
            font-family: 'Monaco', 'Menlo', monospace;
        }}
        
        .overlap-modules .range {{
            font-size: 0.85rem;
            color: #64748b;
            font-family: 'Monaco', 'Menlo', monospace;
        }}
        
        .overlap-symbol {{
            color: #dc2626;
            font-weight: bold;
        }}
        
        .overlap-region {{
            font-size: 0.9rem;
            color: #991b1b;
            font-weight: 500;
        }}
        
        /* Module List (Vertical Layout) */
        .module-list {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}
        
        .module-card-large {{
            display: flex;
            background: white;
            border-radius: 12px;
            box-shadow: var(--card-shadow);
            text-decoration: none;
            color: inherit;
            transition: transform 0.2s, box-shadow 0.2s;
            border: 1px solid var(--border-color);
            overflow: hidden;
        }}
        
        .module-card-large:hover {{
            transform: translateX(8px);
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.15);
        }}
        
        .module-card-large:hover .register-preview {{
            opacity: 1;
            max-width: 300px;
            padding: 1rem;
        }}
        
        .module-main {{
            flex: 1;
            padding: 1.5rem;
        }}
        
        .register-preview {{
            background: #f1f5f9;
            border-left: 1px solid var(--border-color);
            opacity: 0;
            max-width: 0;
            padding: 0;
            overflow: hidden;
            transition: all 0.3s ease;
        }}
        
        .preview-title {{
            font-weight: 600;
            color: #475569;
            margin-bottom: 0.75rem;
            font-size: 0.85rem;
            text-transform: uppercase;
        }}
        
        .reg-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.4rem 0;
            border-bottom: 1px solid var(--border-color);
            gap: 1rem;
        }}
        
        .reg-item:last-child {{
            border-bottom: none;
        }}
        
        .reg-item code {{
            font-size: 0.8rem;
            white-space: nowrap;
        }}
        
        .reg-meta {{
            font-size: 0.7rem;
            color: #64748b;
            white-space: nowrap;
        }}
        
        .reg-more {{
            font-size: 0.75rem;
            color: var(--primary-color);
            font-style: italic;
            margin-top: 0.5rem;
        }}
        
        /* Navigation */
        .breadcrumb {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 1rem;
            font-size: 0.9rem;
        }}
        
        .breadcrumb a {{
            color: var(--primary-color);
            text-decoration: none;
        }}
        
        .breadcrumb a:hover {{
            text-decoration: underline;
        }}
        
        .breadcrumb .separator {{
            color: #94a3b8;
        }}
        
        .breadcrumb .current {{
            color: #64748b;
        }}
        
        .page-nav {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 2rem;
            padding: 1rem;
            background: white;
            border-radius: 8px;
            box-shadow: var(--card-shadow);
        }}
        
        .nav-link {{
            color: var(--primary-color);
            text-decoration: none;
            font-weight: 500;
        }}
        
        .nav-link:hover {{
            text-decoration: underline;
        }}
        
        /* Existing styles */
        h1 {{
            color: var(--primary-color);
            border-bottom: 3px solid var(--primary-color);
            padding-bottom: 0.5rem;
        }}
        
        h2 {{
            color: var(--primary-color);
            margin-top: 2rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.3rem;
        }}
        
        h3, h4 {{
            color: #475569;
            margin-top: 1.5rem;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            background: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        th, td {{
            padding: 0.75rem 1rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}
        
        th {{
            background-color: var(--primary-color);
            color: white;
            font-weight: 600;
        }}
        
        tr:hover {{
            background-color: #f1f5f9;
        }}
        
        code {{
            background-color: var(--code-bg);
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9em;
        }}
        
        hr {{
            border: none;
            border-top: 2px solid var(--border-color);
            margin: 2rem 0;
        }}
        
        ul {{
            padding-left: 1.5rem;
        }}
        
        li {{
            margin: 0.3rem 0;
        }}
        
        strong {{
            color: var(--primary-color);
        }}
        
        p {{
            margin: 0.5rem 0;
        }}
        
        /* Top Navigation */
        .top-nav {{
            display: flex;
            justify-content: flex-end;
            margin-bottom: 1rem;
        }}
        
        .about-link {{
            color: var(--primary-color);
            text-decoration: none;
            font-weight: 500;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            background: white;
            box-shadow: var(--card-shadow);
            transition: transform 0.2s;
        }}
        
        .about-link:hover {{
            transform: translateY(-2px);
        }}
        
        /* About Page Styles */
        .about-hero {{
            text-align: center;
            padding: 2rem;
            margin-bottom: 2rem;
            background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
            border-radius: 16px;
            color: white;
        }}
        
        .about-hero h1 {{
            color: white;
            border: none;
            margin: 0;
            font-size: 2.5rem;
        }}
        
        .about-hero .tagline {{
            opacity: 0.9;
            font-size: 1.2rem;
            margin: 0.5rem 0 0 0;
        }}
        
        .about-content {{
            max-width: 900px;
            margin: 0 auto;
        }}
        
        .about-section {{
            margin-bottom: 2.5rem;
        }}
        
        .about-section p {{
            font-size: 1.05rem;
            line-height: 1.8;
        }}
        
        .feature-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }}
        
        .feature-card {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: var(--card-shadow);
            border: 1px solid var(--border-color);
        }}
        
        .feature-icon {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}
        
        .feature-card h3 {{
            margin: 0.5rem 0;
            color: var(--primary-color);
            font-size: 1rem;
        }}
        
        .feature-card p {{
            margin: 0;
            font-size: 0.85rem;
            color: #64748b;
        }}
        
        .link-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }}
        
        .link-card {{
            display: flex;
            align-items: center;
            gap: 1rem;
            background: white;
            border-radius: 12px;
            padding: 1rem 1.5rem;
            text-decoration: none;
            color: inherit;
            box-shadow: var(--card-shadow);
            border: 1px solid var(--border-color);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .link-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.15);
        }}
        
        .link-icon {{
            font-size: 1.5rem;
        }}
        
        .link-info h3 {{
            margin: 0;
            color: var(--primary-color);
            font-size: 1rem;
        }}
        
        .link-info p {{
            margin: 0;
            font-size: 0.85rem;
            color: #64748b;
        }}
        
        .code-block {{
            background: #1e293b;
            color: #e2e8f0;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            overflow-x: auto;
        }}
        
        .code-block code {{
            background: none;
            padding: 0;
            color: #67e8f9;
            font-size: 0.95rem;
        }}
        
        /* README Container */
        .readme-container {{
            background: white;
            border-radius: 12px;
            padding: 2rem;
            box-shadow: var(--card-shadow);
            margin-bottom: 2rem;
        }}
        
        .readme-container h1 {{
            color: var(--primary-color);
            border-bottom: 3px solid var(--primary-color);
        }}
        
        .readme-container img {{
            max-width: 100%;
            height: auto;
        }}
        
        .about-links {{
            margin-top: 2rem;
        }}
        
        /* Smooth Scrolling */
        html {{
            scroll-behavior: smooth;
        }}
        
        /* Clickable table links */
        td a {{
            color: var(--primary-color);
            text-decoration: none;
            font-weight: 500;
        }}
        
        td a:hover {{
            text-decoration: underline;
        }}
        
        td a code {{
            color: var(--primary-color);
        }}
        
        /* Back to Table Button */
        .back-to-table {{
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: var(--primary-color);
            color: white;
            padding: 0.75rem 1.5rem;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transition: transform 0.2s, box-shadow 0.2s;
            z-index: 1000;
            display: none;
        }}
        
        .back-to-table.visible {{
            display: block;
        }}
        
        .back-to-table:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.2);
        }}
        
        @media print {{
            body {{
                background: white;
                max-width: none;
            }}
            
            table {{
                box-shadow: none;
                border: 1px solid #ddd;
            }}
            
            .page-nav, .breadcrumb, .back-to-table {{
                display: none;
            }}
        }}
        
        @media (max-width: 600px) {{
            .stats {{
                gap: 1.5rem;
            }}
            
            .stat-value {{
                font-size: 1.8rem;
            }}
            
            .module-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
{content}
<footer style="margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--border-color); text-align: center; color: #64748b; font-size: 0.9rem;">
    <a href="https://github.com/bugratufan/axion-hdl" target="_blank" rel="noopener" style="color: #94a3b8; text-decoration: none;">© 2026 Axion HDL. MIT License.</a>
</footer>
''' + ('' if is_index else '''
<a href="#register-table" class="back-to-table" id="backToTable">↑ Back to Table</a>
<script>
// Show/hide back-to-table button based on scroll position
window.addEventListener('scroll', function() {{
    const btn = document.getElementById('backToTable');
    const tableSection = document.getElementById('register-table');
    if (!btn || !tableSection) return;
    
    const tableRect = tableSection.getBoundingClientRect();
    // Show button when scrolled past the table
    if (tableRect.bottom < 0) {{
        btn.classList.add('visible');
    }} else {{
        btn.classList.remove('visible');
    }}
}});

// Smart Navigation: Remember which register row was clicked
document.addEventListener('DOMContentLoaded', function() {{
    const links = document.querySelectorAll('td a');
    const backBtn = document.getElementById('backToTable');
    
    links.forEach(link => {{
        link.addEventListener('click', function(e) {{
            const href = this.getAttribute('href');
            if (href && href.startsWith('#reg-')) {{
                // Construct the row ID: #reg-name -> #row-reg-name
                const regId = href.substring(5);
                const rowId = 'row-reg-' + regId;
                
                // Update back button to point to the specific row
                if (backBtn) {{
                    backBtn.setAttribute('href', '#' + rowId);
                    // Update text slightly to indicate context
                    // backBtn.textContent = '↑ Back to Register'; 
                }}
            }}
        }});
    }});
}});
</script>
''') + '''
</body>
</html>'''
    
    def generate_pdf(self, modules: List[Dict]) -> str:
        """
        Generate PDF documentation using weasyprint.
        
        Returns:
            Output path on success, None if weasyprint is not available.
        """
        # First generate HTML
        html_path = self.generate_html(modules)
        
        try:
            from weasyprint import HTML
        except ImportError:
            print("  Warning: weasyprint not installed. Skipping PDF generation.")
            print("  Install with: pip install weasyprint")
            return None
        
        output_path = os.path.join(self.output_dir, "register_map.pdf")
        
        try:
            HTML(filename=html_path).write_pdf(output_path)
            return output_path
        except Exception as e:
            print(f"  Warning: PDF generation failed: {e}")
            return None


class CHeaderGenerator:
    """Generator for creating C header files."""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        
    def generate_header(self, module: Dict) -> str:
        """Generate C header file for a module."""
        module_name = module.get('_effective_name', module['name'])
        output_filename = f"{module_name}_regs.h"
        output_path = os.path.join(self.output_dir, output_filename)
        
        lines = self._generate_header_content(module)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
            
        return output_path
    
    def _get_signal_width(self, signal_type: str) -> int:
        """Extract signal width from type string.

        Supported formats:
            '[31:0]'                          (VHDL-annotation path)
            'std_logic_vector(31 downto 0)'   (YAML-input path)
            'std_logic'                       (YAML-input, 1-bit)
        """
        import re
        match = re.match(r'\[(\d+):(\d+)\]', signal_type)
        if match:
            return int(match.group(1)) - int(match.group(2)) + 1
        match = re.match(r'std_logic_vector\((\d+)\s+downto\s+(\d+)\)', signal_type)
        if match:
            return int(match.group(1)) - int(match.group(2)) + 1
        if signal_type.strip() == 'std_logic':
            return 1
        return 32
    
    def _get_num_regs(self, signal_width: int) -> int:
        """Calculate number of 32-bit registers needed for a signal."""
        return (signal_width + 31) // 32
    
    def _generate_header_content(self, module: Dict) -> List[str]:
        """Generate C header content with module-prefixed register names."""
        display_name = module.get('_effective_name', module['name'])
        c_safe = re.sub(r'[^A-Za-z0-9_]', '_', display_name)
        c_safe = re.sub(r'_+', '_', c_safe).strip('_') or 'module'
        if c_safe[0].isdigit():
            c_safe = 'v_' + c_safe
        module_name = c_safe.upper()
        module_prefix = f"{module_name}_"
        base_addr = module.get('base_address', 0x00)

        lines = [
            "/**",
            f" * @file {display_name}_regs.h",
            f" * @brief Register definitions for {display_name} module",
            " * @note Generated by Axion HDL - Do not edit manually",
            " *",
            " * All register definitions use module prefix to avoid namespace collisions",
            f" * when multiple modules are included in the same project.",
            " */",
            "",
            f"#ifndef {module_name}_REGS_H",
            f"#define {module_name}_REGS_H",
            "",
            "#include <stdint.h>",
            "",
            f"/* Module Base Address */",
            f"#define {module_name}_BASE_ADDR    0x{base_addr:08X}",
            "",
            "/* Register Address Offsets (relative to base) */",
        ]
        
        # Register offsets (relative) - with module prefix
        # For wide signals (>32 bits), generate _REG0, _REG1, etc. offsets
        for reg in module['registers']:
            reg_name_upper = reg['signal_name'].upper()
            offset_int = reg.get('relative_address_int', reg['address_int'])
            signal_width = self._get_signal_width(reg['signal_type'])
            num_regs = self._get_num_regs(signal_width)
            description = reg.get('description', '')
            
            if num_regs == 1:
                # Single 32-bit register
                offset = reg.get('relative_address', reg['address'])
                if description:
                    lines.append(f"#define {module_prefix}{reg_name_upper}_OFFSET    {offset}  /* {description} */")
                else:
                    lines.append(f"#define {module_prefix}{reg_name_upper}_OFFSET    {offset}")
            else:
                # Multi-register signal
                desc_suffix = f" - {description}" if description else ""
                lines.append(f"/* {reg['signal_name']} is {signal_width} bits wide, occupies {num_regs} registers{desc_suffix} */")
                for i in range(num_regs):
                    reg_offset = offset_int + (i * 4)
                    lines.append(f"#define {module_prefix}{reg_name_upper}_REG{i}_OFFSET    0x{reg_offset:02X}")
        
        lines.extend([
            "",
            "/* Absolute Register Addresses */",
        ])
        
        # Absolute addresses - with module prefix
        for reg in module['registers']:
            reg_name_upper = reg['signal_name'].upper()
            addr_int = reg['address_int']
            signal_width = self._get_signal_width(reg['signal_type'])
            num_regs = self._get_num_regs(signal_width)
            
            if num_regs == 1:
                lines.append(f"#define {module_prefix}{reg_name_upper}_ADDR    {reg['address']}")
            else:
                for i in range(num_regs):
                    reg_addr = addr_int + (i * 4)
                    lines.append(f"#define {module_prefix}{reg_name_upper}_REG{i}_ADDR    0x{reg_addr:X}")
        
        lines.extend([
            "",
            "/* Signal Width Definitions (for multi-register signals) */",
        ])
        
        # Add width definitions for wide signals
        has_wide_signals = False
        for reg in module['registers']:
            signal_width = self._get_signal_width(reg['signal_type'])
            if signal_width > 32:
                has_wide_signals = True
                reg_name_upper = reg['signal_name'].upper()
                num_regs = self._get_num_regs(signal_width)
                lines.append(f"#define {module_prefix}{reg_name_upper}_WIDTH    {signal_width}")
                lines.append(f"#define {module_prefix}{reg_name_upper}_NUM_REGS    {num_regs}")
        
        if not has_wide_signals:
            lines.append("/* No signals wider than 32 bits */")
        
        lines.extend([
            "",
            "/* Register Access Macros (using module base address) */",
            "/* Helper macros for bit field access */",
            "#ifndef GET_FIELD",
            "#define GET_FIELD(val, mask, shift)    (((val) & (mask)) >> (shift))",
            "#endif",
            "",
            "#ifndef SET_FIELD",
            "#define SET_FIELD(val, mask, shift, new_val)    (((val) & ~(mask)) | (((new_val) << (shift)) & (mask)))",
            "#endif",
        ])
        
        # Read macros - with module prefix
        for reg in module['registers']:
            if reg['access_mode'] in ['RO', 'RW']:
                reg_name_upper = reg['signal_name'].upper()
                signal_width = self._get_signal_width(reg['signal_type'])
                num_regs = self._get_num_regs(signal_width)
                
                if num_regs == 1:
                    lines.append(
                        f"#define {module_prefix}READ_{reg_name_upper}()    "
                        f"(*((volatile uint32_t*)({module_name}_BASE_ADDR + {module_prefix}{reg_name_upper}_OFFSET)))"
                    )
                else:
                    # Multi-register read macros
                    for i in range(num_regs):
                        lines.append(
                            f"#define {module_prefix}READ_{reg_name_upper}_REG{i}()    "
                            f"(*((volatile uint32_t*)({module_name}_BASE_ADDR + {module_prefix}{reg_name_upper}_REG{i}_OFFSET)))"
                        )
        
        lines.append("")
        
        # Write macros - with module prefix
        for reg in module['registers']:
            if reg['access_mode'] in ['WO', 'RW']:
                reg_name_upper = reg['signal_name'].upper()
                signal_width = self._get_signal_width(reg['signal_type'])
                num_regs = self._get_num_regs(signal_width)
                
                if num_regs == 1:
                    lines.append(
                        f"#define {module_prefix}WRITE_{reg_name_upper}(val)    "
                        f"(*((volatile uint32_t*)({module_name}_BASE_ADDR + {module_prefix}{reg_name_upper}_OFFSET)) = (val))"
                    )
                else:
                    # Multi-register write macros
                    for i in range(num_regs):
                        lines.append(
                            f"#define {module_prefix}WRITE_{reg_name_upper}_REG{i}(val)    "
                            f"(*((volatile uint32_t*)({module_name}_BASE_ADDR + {module_prefix}{reg_name_upper}_REG{i}_OFFSET)) = (val))"
                        )
                        
        lines.extend([
            "",
            "/* Bit Field Masks and Shifts (for packed registers) */",
        ])
        
        for reg in module['registers']:
            if reg.get('is_packed'):
                # Generate MASK and SHIFT for fields in this packed register
                reg_name_upper = reg['reg_name'].upper() # The container register
                
                for field in reg.get('fields', []):
                    field_name_upper = field['name'].upper()
                    bit_offset = int(field.get('bit_low', 0))
                    width = int(field.get('width', 1))
                    mask = ((1 << width) - 1) << bit_offset
                    
                    lines.append(f"#define {module_prefix}{reg_name_upper}_{field_name_upper}_MASK    0x{mask:X}")
                    lines.append(f"#define {module_prefix}{reg_name_upper}_{field_name_upper}_SHIFT   {bit_offset}")

        lines.extend([
            "",
            "/* Register Default Values */",
        ])
        
        # We need to construct the full 32-bit default for packed registers
        # For standalone, it's easy.
        
        # First, calculate defaults for packed registers
        packed_defaults = {}
        for reg in module['registers']:
            if reg.get('is_packed'):
                reg_name = reg['reg_name']
                if reg_name not in packed_defaults:
                    packed_defaults[reg_name] = 0
                
                default_val = reg.get('default_value') or '0'
                bit_offset = int(reg.get('bit_offset', 0))
                
                # Check if default is hex or dec
                # Check if default is hex or dec
                try:
                    if isinstance(default_val, int):
                        val = default_val
                    else:
                        val = int(default_val, 0) # Auto-detect base
                except (ValueError, TypeError):
                    val = 0
                    
                packed_defaults[reg_name] |= (val << bit_offset)

        # Iterate again to generate macros (skipping duplicates for packed)
        processed_packed_defaults = set()
        
        for reg in module['registers']:
            if reg.get('is_packed'):
                reg_name = reg['reg_name']
                if reg_name in processed_packed_defaults:
                    continue
                processed_packed_defaults.add(reg_name)
                
                val = packed_defaults.get(reg_name, 0)
                reg_name_upper = reg_name.upper()
                lines.append(f"#define {module_prefix}{reg_name_upper}_DEFAULT    0x{val:08X}")
                
            else:
                # Standalone
                reg_name_upper = reg['signal_name'].upper()
                default_val = reg.get('default_value') or '0'
                try:
                    if isinstance(default_val, int):
                        val = default_val
                    else:
                        val = int(default_val, 0)
                except (ValueError, TypeError):
                    val = 0
                
                # Handling wide signals? Default usually 0 for them in this simple generator for now
                if self._get_signal_width(reg['signal_type']) <= 32:
                     lines.append(f"#define {module_prefix}{reg_name_upper}_DEFAULT    0x{val:08X}")
        
        # Enumerated values macros for packed register fields
        def _sanitize_c_id(s: str) -> str:
            sanitized = re.sub(r'[^A-Za-z0-9_]', '_', s).upper()
            if sanitized and sanitized[0].isdigit():
                sanitized = '_' + sanitized
            return sanitized

        enum_macros_lines = []
        for reg in module['registers']:
            if reg.get('is_packed'):
                reg_name_upper = _sanitize_c_id(reg.get('reg_name', reg.get('signal_name', '')))
                for field in reg.get('fields', []):
                    enum_dict = field.get('enum_values')
                    if enum_dict:
                        field_name_upper = _sanitize_c_id(field['name'])
                        enum_macros_lines.append(f"/* {field['name']} enumerated values */")
                        for val, name in sorted(enum_dict.items()):
                            enum_macros_lines.append(
                                f"#define {module_prefix}{reg_name_upper}_{field_name_upper}_{_sanitize_c_id(name)}    0x{val:X}"
                            )
        if enum_macros_lines:
            lines.extend(["", "/* Enumerated Field Values */"] + enum_macros_lines)

        lines.extend([
            "",
            "/* Register Structure */",
            f"typedef struct {{",
        ])
        
        for reg in module['registers']:
            offset = reg.get('relative_address', reg['address'])
            signal_width = self._get_signal_width(reg['signal_type'])
            num_regs = self._get_num_regs(signal_width)
            description = reg.get('description', '')
            desc_suffix = f" - {description}" if description else ""
            
            if num_regs == 1:
                lines.append(f"    volatile uint32_t {reg['signal_name']};  /* {offset} - {reg['access_mode']}{desc_suffix} */")
            else:
                # Multi-register fields
                for i in range(num_regs):
                    reg_offset_int = reg.get('relative_address_int', reg['address_int']) + (i * 4)
                    lines.append(f"    volatile uint32_t {reg['signal_name']}_reg{i};  /* 0x{reg_offset_int:02X} - {reg['access_mode']} ({signal_width}-bit signal, part {i}){desc_suffix} */")
        
        lines.extend([
            f"}} {module['name']}_regs_t;",
            "",
            "/* Access register block as structure */",
            f"#define {module_name}_REGS    ((volatile {module['name']}_regs_t*)({module_name}_BASE_ADDR))",
            "",
            f"#endif /* {module_name}_REGS_H */",
            ""
        ])
        
        return lines


class XMLGenerator:
    """Generator for creating XML register maps."""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        
    def generate_xml(self, module: Dict) -> str:
        """Generate XML register map."""
        module_name = module.get('_effective_name', module['name'])
        output_filename = f"{module_name}_regs.xml"
        output_path = os.path.join(self.output_dir, output_filename)
        
        lines = self._generate_xml_content(module)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
            
        return output_path
    
    def _generate_xml_content(self, module: Dict) -> List[str]:
        """Generate XML content with round-trip compatible attributes."""
        base_addr = module.get('base_address', 0x00)
        cdc_en = module.get('cdc_enabled', False)
        cdc_stage = module.get('cdc_stages', 2)
        
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<spirit:component xmlns:spirit="http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5">',
            f'    <spirit:vendor>axion</spirit:vendor>',
            f'    <spirit:library>user</spirit:library>',
            f'    <spirit:name>{module.get("_effective_name", module["name"])}</spirit:name>',
            f'    <spirit:version>1.0</spirit:version>',
        ]
        
        # Add CDC configuration as vendor extension for round-trip
        if cdc_en:
            lines.extend([
                '    <spirit:vendorExtensions>',
                f'        <axion:config cdc_en="true" cdc_stage="{cdc_stage}" xmlns:axion="http://axion-hdl.org/extensions"/>',
                '    </spirit:vendorExtensions>',
            ])
        
        lines.extend([
            '    <spirit:memoryMaps>',
            '        <spirit:memoryMap>',
            '            <spirit:name>register_map</spirit:name>',
            '            <spirit:addressBlock>',
            '                <spirit:name>registers</spirit:name>',
            f'                <spirit:baseAddress>0x{base_addr:X}</spirit:baseAddress>',
        ])
        
        # Calculate range (using relative addresses)
        if module['registers']:
            max_offset = max(
                reg.get('relative_address_int', reg['address_int']) 
                for reg in module['registers']
            )
            lines.append(f'                <spirit:range>{max_offset + 4}</spirit:range>')
        else:
            lines.append('                <spirit:range>0</spirit:range>')
            
        lines.append('                <spirit:width>32</spirit:width>')
        
        # Registers
        for reg in module['registers']:
            offset = reg.get('relative_address', reg['address'])
            description = reg.get('description', '')
            r_strobe = reg.get('read_strobe', reg.get('r_strobe', False))
            w_strobe = reg.get('write_strobe', reg.get('w_strobe', False))

            # Build strobe attributes string for round-trip compatibility
            strobe_attrs = ''
            if r_strobe:
                strobe_attrs += ' r_strobe="true"'
            if w_strobe:
                strobe_attrs += ' w_strobe="true"'

            lines.extend([
                f'                <spirit:register{strobe_attrs}>',
                f'                    <spirit:name>{reg["signal_name"]}</spirit:name>',
            ])
            if description:
                lines.append(f'                    <spirit:description>{description}</spirit:description>')
            lines.extend([
                f'                    <spirit:addressOffset>{offset}</spirit:addressOffset>',
                '                    <spirit:size>32</spirit:size>',
                f'                    <spirit:access>{self._get_xml_access(reg["access_mode"])}</spirit:access>',
            ])

            # Emit nested fields if packed (with enum support)
            if reg.get('is_packed') and reg.get('fields'):
                for field in reg.get('fields', []):
                    bit_offset = int(field.get('bit_low', 0))
                    bit_width = int(field.get('width', 1))
                    f_access = self._get_xml_access(field.get('access_mode', reg['access_mode']))
                    lines.extend([
                        '                    <spirit:field>',
                        f'                        <spirit:name>{field["name"]}</spirit:name>',
                        f'                        <spirit:bitOffset>{bit_offset}</spirit:bitOffset>',
                        f'                        <spirit:bitWidth>{bit_width}</spirit:bitWidth>',
                        f'                        <spirit:access>{f_access}</spirit:access>',
                    ])
                    enum_dict = field.get('enum_values')
                    if enum_dict:
                        lines.append('                        <spirit:enumeratedValues>')
                        for val, name in sorted(enum_dict.items()):
                            lines.extend([
                                '                            <spirit:enumeratedValue>',
                                f'                                <spirit:name>{name}</spirit:name>',
                                f'                                <spirit:value>{val}</spirit:value>',
                                '                            </spirit:enumeratedValue>',
                            ])
                        lines.append('                        </spirit:enumeratedValues>')
                    lines.append('                    </spirit:field>')
            else:
                lines.extend([
                    '                    <spirit:field>',
                    f'                        <spirit:name>{reg["signal_name"]}_data</spirit:name>',
                    '                        <spirit:bitOffset>0</spirit:bitOffset>',
                    '                        <spirit:bitWidth>32</spirit:bitWidth>',
                    '                    </spirit:field>',
                ])
            lines.append('                </spirit:register>')
        
        lines.extend([
            '            </spirit:addressBlock>',
            '        </spirit:memoryMap>',
            '    </spirit:memoryMaps>',
            '</spirit:component>',
            ''
        ])
        
        return lines
    
    def _get_xml_access(self, access_mode: str) -> str:
        """Convert access mode to XML format."""
        mapping = {
            'RO': 'read-only',
            'WO': 'write-only',
            'RW': 'read-write'
        }
        return mapping.get(access_mode, 'read-write')


class YAMLGenerator:
    """Generator for creating YAML register maps."""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        
    def generate_yaml(self, module: Dict) -> str:
        """Generate YAML register map."""
        try:
            import yaml
        except ImportError:
            print("  Error: PyYAML required for YAML generation. Install with: pip install PyYAML")
            return ""
            
        module_name = module.get('_effective_name', module['name'])
        output_filename = f"{module_name}_regs.yaml"
        output_path = os.path.join(self.output_dir, output_filename)
        
        data = self._generate_yaml_data(module)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            
        return output_path
    
    def _generate_yaml_data(self, module: Dict) -> Dict:
        """Generate YAML data structure for round-trip compatibility."""
        base_addr = module.get('base_address', 0x00)
        cdc_en = module.get('cdc_enabled', False)
        cdc_stage = module.get('cdc_stages', 2)

        data = {
            'module': module.get('_effective_name', module['name']),
            'base_addr': f"0x{base_addr:04X}",
            'config': {
                'cdc_en': cdc_en,
                'cdc_stage': cdc_stage
            },
            'registers': []
        }
        
        for reg in module['registers']:
            offset = reg.get('relative_address_int', reg['address_int'])
            r_strobe = reg.get('read_strobe', reg.get('r_strobe', False))
            w_strobe = reg.get('write_strobe', reg.get('w_strobe', False))
            default_val = reg.get('default_value') or 0
            
            reg_entry = {
                'name': reg['signal_name'],
                'addr': f"0x{offset:02X}",
                'access': reg['access_mode'],
                'width': reg.get('width', 32)
            }
            
            if r_strobe:
                reg_entry['r_strobe'] = True
            if w_strobe:
                reg_entry['w_strobe'] = True
            if reg.get('description'):
                reg_entry['description'] = reg['description']
            if default_val != 0:
                reg_entry['default'] = f"0x{default_val:X}"
            
            # Handle packed registers
            if reg.get('is_packed'):
                reg_entry['fields'] = []
                for field in reg.get('fields', []):
                    field_entry = {
                        'name': field['name'],
                        'bit_offset': field['bit_low'],
                        'width': field['width'],
                        'access': field['access_mode']
                    }
                    if field.get('default_value', 0) != 0:
                        field_entry['default'] = f"0x{field['default_value']:X}"
                    enum_dict = field.get('enum_values')
                    if enum_dict:
                        field_entry['enum_values'] = {str(k): v for k, v in sorted(enum_dict.items())}
                    reg_entry['fields'].append(field_entry)

            data['registers'].append(reg_entry)

        return data


class JSONGenerator:
    """Generator for creating JSON register maps."""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        
    def generate_json(self, module: Dict) -> str:
        """Generate JSON register map."""
        import json
        
        module_name = module.get('_effective_name', module['name'])
        output_filename = f"{module_name}_regs.json"
        output_path = os.path.join(self.output_dir, output_filename)
        
        data = self._generate_json_data(module)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        return output_path
    
    def _generate_json_data(self, module: Dict) -> Dict:
        """Generate JSON data structure for round-trip compatibility."""
        base_addr = module.get('base_address', 0x00)
        cdc_en = module.get('cdc_enabled', False)
        cdc_stage = module.get('cdc_stages', 2)

        data = {
            'module': module.get('_effective_name', module['name']),
            'base_addr': f"0x{base_addr:04X}",
            'config': {
                'cdc_en': cdc_en,
                'cdc_stage': cdc_stage
            },
            'registers': []
        }
        
        for reg in module['registers']:
            offset = reg.get('relative_address_int', reg['address_int'])
            r_strobe = reg.get('read_strobe', reg.get('r_strobe', False))
            w_strobe = reg.get('write_strobe', reg.get('w_strobe', False))
            default_val = reg.get('default_value') or 0
            
            reg_entry = {
                'name': reg['signal_name'],
                'addr': f"0x{offset:02X}",
                'access': reg['access_mode'],
                'width': reg.get('width', 32)
            }
            
            if r_strobe:
                reg_entry['r_strobe'] = True
            if w_strobe:
                reg_entry['w_strobe'] = True
            if reg.get('description'):
                reg_entry['description'] = reg['description']
            if default_val != 0:
                reg_entry['default'] = f"0x{default_val:X}"
            
            # Handle packed registers
            if reg.get('is_packed'):
                reg_entry['fields'] = []
                for field in reg.get('fields', []):
                    field_entry = {
                        'name': field['name'],
                        'bit_offset': field['bit_low'],
                        'width': field['width'],
                        'access': field['access_mode']
                    }
                    if field.get('default_value', 0) != 0:
                        field_entry['default'] = f"0x{field['default_value']:X}"
                    enum_dict = field.get('enum_values')
                    if enum_dict:
                        field_entry['enum_values'] = {str(k): v for k, v in sorted(enum_dict.items())}
                    reg_entry['fields'].append(field_entry)

            data['registers'].append(reg_entry)

        return data


class TOMLGenerator:
    """Generator for creating TOML register maps."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def generate_toml(self, module: Dict) -> str:
        """Generate TOML register map."""
        try:
            import tomli_w
        except ImportError:
            print("Warning: tomli_w not installed. TOML generation requires: pip install tomli-w")
            return None

        module_name = module.get('_effective_name', module['name'])
        output_filename = f"{module_name}_regs.toml"
        output_path = os.path.join(self.output_dir, output_filename)

        data = self._generate_toml_data(module)

        with open(output_path, 'wb') as f:
            tomli_w.dump(data, f)

        return output_path

    def _generate_toml_data(self, module: Dict) -> Dict:
        """Generate TOML data structure for round-trip compatibility."""
        base_addr = module.get('base_address', 0x00)
        cdc_en = module.get('cdc_enabled', False)
        cdc_stage = module.get('cdc_stages', 2)

        data = {
            'module': module.get('_effective_name', module['name']),
            'base_addr': f"0x{base_addr:04X}",
            'config': {
                'cdc_en': cdc_en,
                'cdc_stage': cdc_stage
            },
            'registers': []
        }

        for reg in module['registers']:
            offset = reg.get('relative_address_int', reg['address_int'])
            r_strobe = reg.get('read_strobe', reg.get('r_strobe', False))
            w_strobe = reg.get('write_strobe', reg.get('w_strobe', False))
            default_val = reg.get('default_value') or 0

            reg_entry = {
                'name': reg['signal_name'],
                'addr': f"0x{offset:02X}",
                'access': reg['access_mode'],
                'width': reg.get('width', 32)
            }

            if r_strobe:
                reg_entry['r_strobe'] = True
            if w_strobe:
                reg_entry['w_strobe'] = True
            if reg.get('description'):
                reg_entry['description'] = reg['description']
            if default_val != 0:
                reg_entry['default'] = f"0x{default_val:X}"

            # Handle packed registers
            if reg.get('is_packed'):
                # For TOML, packed registers should use reg_name/bit_offset format
                # not the fields array format (which is YAML/JSON specific)
                pass

            data['registers'].append(reg_entry)

        return data


class AddressMapHTMLGenerator:
    """Generator for the address_map.html hierarchy overview report."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def generate(self, modules: List[Dict]) -> str:
        """
        Generate address_map.html showing all instances with address ranges.

        Args:
            modules: List of analyzed (and hierarchy-applied) module dicts.

        Returns:
            Absolute path to the generated address_map.html file.
        """
        def _to_int(v):
            if isinstance(v, int):
                return v
            try:
                return int(str(v), 0)
            except (ValueError, TypeError):
                return 0

        def _relative_offset(r, base_addr):
            if r.get('relative_address_int') is not None:
                return _to_int(r['relative_address_int'])
            if r.get('address_int') is not None:
                return _to_int(r['address_int']) - base_addr
            return _to_int(r.get('address', 0))

        def _reg_span(r):
            width = int(r.get('width', 32)) if r.get('width') else 32
            byte_size = max(4, (width + 7) // 8)
            return ((byte_size + 3) // 4) * 4

        rows = []
        for module in modules:
            display_name = module.get('_effective_name', module['name'])
            base_addr = _to_int(module.get('base_address', 0))
            regs = module.get('registers', [])
            if regs:
                size = max(
                    _relative_offset(r, base_addr) + _reg_span(r)
                    for r in regs
                )
            else:
                size = 0
            end_addr = base_addr + size - 1 if size > 0 else base_addr
            rows.append({
                'instance': display_name,
                'module': module['name'],
                'base': base_addr,
                'end': end_addr,
                'size': size,
            })

        rows.sort(key=lambda r: r['base'])

        table_rows = ''
        for row in rows:
            size_str = self._fmt_size(row['size'])
            table_rows += (
                f'<tr>'
                f'<td><code>{_html.escape(row["instance"])}</code></td>'
                f'<td>{_html.escape(row["module"])}</td>'
                f'<td><code>0x{row["base"]:08X}</code></td>'
                f'<td><code>0x{row["end"]:08X}</code></td>'
                f'<td>{size_str}</td>'
                f'</tr>\n'
            )

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Address Map</title>
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgLTcwIDE0MCAxNDAiIHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIj4KICA8ZGVmcz4KICAgIDxtYXNrIGlkPSJkb3QtbWFzayI+CiAgICAgIDxyZWN0IHg9Ii01MDAiIHk9Ii01MDAiIHdpZHRoPSIxNTAwIiBoZWlnaHQ9IjE1MDAiIGZpbGw9IndoaXRlIi8+CiAgICAgIDxjaXJjbGUgY3g9IjI0IiBjeT0iLTEiIHI9IjIyIiBmaWxsPSJibGFjayIvPgogICAgPC9tYXNrPgogIDwvZGVmcz4KCiAgPGcgbWFzaz0idXJsKCNkb3QtbWFzaykiPgogICAgPHRleHQgeD0iMCIgeT0iNDYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtZmFtaWx5PSInQXJpYWwgQmxhY2snLCAnSGVsdmV0aWNhIE5ldWUnLCBzYW5zLXNlcmlmIiBmb250LXdlaWdodD0iOTAwIiBmb250LXNpemU9IjEzMCIgZmlsbD0ibm9uZSI+CiAgICAgIEFYSTx0c3BhbiBmaWxsPSIjMmY4MWY3Ij5PPC90c3Bhbj5OCiAgICA8L3RleHQ+CiAgPC9nPgoKICA8Y2lyY2xlIGN4PSIyNCIgY3k9Ii0xIiByPSIxNiIgZmlsbD0iIzJmODFmNyIvPgo8L3N2Zz4K">
    <style>
        :root {{
            --primary-color: #2563eb;
            --primary-dark: #1d4ed8;
            --bg-color: #f8fafc;
            --text-color: #1e293b;
            --border-color: #e2e8f0;
        }}
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            max-width: 1000px;
            margin: 0 auto;
            padding: 2rem;
            background-color: var(--bg-color);
        }}
        .hero {{
            text-align: center;
            padding: 2rem;
            margin-bottom: 2rem;
            background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
            border-radius: 16px;
            color: white;
        }}
        .hero h1 {{ color: white; border: none; margin: 0; font-size: 2rem; }}
        .hero p {{ margin: 0.5rem 0 0; opacity: 0.9; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }}
        th {{
            background: var(--primary-color);
            color: white;
            padding: 0.75rem 1rem;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 0.65rem 1rem;
            border-bottom: 1px solid var(--border-color);
        }}
        tr:last-child td {{ border-bottom: none; }}
        tr:hover td {{ background-color: #eff6ff; }}
        code {{
            background: #f1f5f9;
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            font-family: 'Fira Code', 'Consolas', monospace;
            font-size: 0.9em;
        }}
        footer {{
            text-align: center;
            margin-top: 2rem;
            color: #64748b;
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <div class="hero">
        <h1>Address Map</h1>
        <p>Full module instance address space overview</p>
    </div>
    <table>
        <thead>
            <tr>
                <th>Instance Name</th>
                <th>Module</th>
                <th>Base Address</th>
                <th>End Address</th>
                <th>Size</th>
            </tr>
        </thead>
        <tbody>
{table_rows}        </tbody>
    </table>
    <footer><a href="https://github.com/bugratufan/axion-hdl" target="_blank" rel="noopener">© 2026 Axion HDL. MIT License.</a></footer>
</body>
</html>
'''
        output_path = os.path.join(self.output_dir, 'address_map.html')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return output_path

    @staticmethod
    def _fmt_size(size_bytes: int) -> str:
        """Format byte size as human-readable string."""
        if size_bytes >= 1024 * 1024:
            return f"{size_bytes // (1024 * 1024)} MB"
        if size_bytes >= 1024:
            return f"{size_bytes // 1024} KB"
        return f"{size_bytes} B"
