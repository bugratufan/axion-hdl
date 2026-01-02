# Python API

The Python API provides programmatic access to Axion-HDL, allowing integration with custom workflows, build systems, and other tools.

## Installation

```bash
pip install axion-hdl
```

## Quick Start

```python
from axion_hdl import AxionHDL

# Create instance
axion = AxionHDL()

# Add source files
axion.add_source("controller.yaml")
axion.add_source("./rtl")

# Analyze all sources
modules = axion.analyze()

# Generate outputs
axion.set_output_dir("./output")
axion.generate_all()
```

---

## Core Class: AxionHDL

### Creating an Instance

```python
from axion_hdl import AxionHDL

# Basic usage
axion = AxionHDL()

# With initial source
axion = AxionHDL()
axion.add_source("registers.yaml")
```

### Adding Sources

```python
# Add single file (auto-detects type by extension)
axion.add_source("registers.yaml")
axion.add_source("controller.xml")
axion.add_source("gpio.json")
axion.add_source("spi_master.vhd")

# Add directory (recursive scan)
axion.add_source("./rtl")

# Add specific format
axion.add_yaml_src("registers.yaml")
axion.add_xml_src("controller.xml")
axion.add_json_src("gpio.json")

# List current sources
sources = axion.list_src()
print(f"Loaded sources: {sources}")
```

### Excluding Files

```python
# Exclude by pattern
axion.exclude("*_tb.vhd")
axion.exclude("test_*")
axion.exclude("deprecated")

# List excludes
excludes = axion.list_excludes()

# Clear all excludes
axion.clear_excludes()
```

### Analysis

```python
# Analyze all sources
modules = axion.analyze()

# Check if analyzed
if axion.is_analyzed:
    print(f"Found {len(modules)} modules")

# Get parsed modules
modules = axion.get_modules()

for module in modules:
    print(f"Module: {module['name']}")
    print(f"  Source: {module['source_file']}")
    print(f"  Base Address: {module['base_addr']}")
    print(f"  Registers: {len(module['registers'])}")
    
    for reg in module['registers']:
        print(f"    - {reg['name']}: {reg['access']} @ {reg['addr']}")
```

### Generation

```python
# Set output directory
axion.set_output_dir("./output")

# Generate all outputs
axion.generate_all()

# Generate specific formats
axion.generate_vhdl()
axion.generate_c_header()
axion.generate_documentation()  # Markdown
axion.generate_xml()
axion.generate_yaml()
axion.generate_json()
```

---

## Complete Examples

### Example 1: Basic Generation

```python
from axion_hdl import AxionHDL

def generate_from_yaml():
    axion = AxionHDL()
    
    # Add source
    axion.add_source("registers.yaml")
    
    # Analyze
    modules = axion.analyze()
    print(f"Found {len(modules)} modules")
    
    # Generate all outputs
    axion.set_output_dir("./generated")
    axion.generate_all()
    
    print("Generation complete!")

if __name__ == "__main__":
    generate_from_yaml()
```

### Example 2: Multi-Source Project

```python
from axion_hdl import AxionHDL

def generate_project():
    axion = AxionHDL()
    
    # Add multiple sources
    axion.add_source("./rtl")          # VHDL files
    axion.add_source("extra_regs.yaml") # Additional YAML
    axion.add_source("config.json")     # JSON config
    
    # Exclude testbenches
    axion.exclude("*_tb.vhd")
    axion.exclude("*_test.vhd")
    
    # Analyze
    modules = axion.analyze()
    
    # Print summary
    for m in modules:
        print(f"  {m['name']}: {len(m['registers'])} registers")
    
    # Generate
    axion.set_output_dir("./output")
    axion.generate_all()

if __name__ == "__main__":
    generate_project()
```

### Example 3: Custom Workflow with Validation

```python
from axion_hdl import AxionHDL
from axion_hdl.rule_checker import RuleChecker

def validated_generation():
    axion = AxionHDL()
    
    # Add sources
    axion.add_source("./rtl")
    
    # Analyze
    modules = axion.analyze()
    
    # Run validation
    checker = RuleChecker()
    results = checker.run_all_checks(modules)
    
    # Check for errors
    if results["errors"]:
        print("❌ Validation failed!")
        for error in results["errors"]:
            print(f"  ERROR: {error['message']}")
        return False
    
    # Show warnings
    if results["warnings"]:
        print("⚠️ Warnings:")
        for warning in results["warnings"]:
            print(f"  WARNING: {warning['message']}")
    
    # Generate only if valid
    print("✓ Validation passed, generating...")
    axion.set_output_dir("./output")
    axion.generate_all()
    
    return True

if __name__ == "__main__":
    success = validated_generation()
    exit(0 if success else 1)
```

### Example 4: Address Overlap Detection

```python
from axion_hdl import AxionHDL

def check_overlaps():
    axion = AxionHDL()
    
    # Add all modules
    axion.add_source("./rtl")
    axion.analyze()
    
    # Check for address overlaps between modules
    overlaps = axion.check_address_overlaps()
    
    if overlaps:
        print("⚠️ Address overlaps detected:")
        for overlap in overlaps:
            print(f"  {overlap['module1']} ({overlap['range1']}) "
                  f"overlaps with {overlap['module2']} ({overlap['range2']})")
    else:
        print("✓ No address overlaps")

if __name__ == "__main__":
    check_overlaps()
```

### Example 5: Selective Generation

```python
from axion_hdl import AxionHDL

def generate_specific_outputs():
    axion = AxionHDL()
    
    axion.add_source("registers.yaml")
    axion.analyze()
    axion.set_output_dir("./output")
    
    # Generate only VHDL and C header
    axion.generate_vhdl()
    axion.generate_c_header()
    
    print("Generated VHDL and C header only")

if __name__ == "__main__":
    generate_specific_outputs()
```

### Example 6: Build System Integration

```python
#!/usr/bin/env python3
"""
build_regs.py - Integrate with build system
"""

import sys
import os
from axion_hdl import AxionHDL

def build_registers(source_dir: str, output_dir: str) -> bool:
    """Generate register files for build."""
    axion = AxionHDL()
    
    # Add source directory
    axion.add_source(source_dir)
    axion.exclude("*_tb.vhd")
    
    # Analyze
    try:
        modules = axion.analyze()
    except Exception as e:
        print(f"Analysis error: {e}", file=sys.stderr)
        return False
    
    if not modules:
        print("No modules found!", file=sys.stderr)
        return False
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate
    axion.set_output_dir(output_dir)
    axion.generate_all()
    
    # Report
    print(f"Generated files for {len(modules)} modules:")
    for m in modules:
        print(f"  - {m['name']}_axion_reg.vhd")
        print(f"  - {m['name']}_regs.h")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <source_dir> <output_dir>")
        sys.exit(1)
    
    success = build_registers(sys.argv[1], sys.argv[2])
    sys.exit(0 if success else 1)
```

---

## RuleChecker API

The RuleChecker validates register definitions before generation.

```python
from axion_hdl.rule_checker import RuleChecker
from axion_hdl import AxionHDL

# Setup
axion = AxionHDL()
axion.add_source("registers.yaml")
modules = axion.analyze()

# Create checker
checker = RuleChecker()

# Run all checks
results = checker.run_all_checks(modules)

# Access results
print(f"Errors: {len(results['errors'])}")
print(f"Warnings: {len(results['warnings'])}")

# Get detailed report
report = checker.generate_report()
print(report)

# Individual check result
for error in results["errors"]:
    print(f"[{error['rule']}] {error['message']}")
    print(f"  Module: {error['module']}")
    if 'register' in error:
        print(f"  Register: {error['register']}")
```

### Check Categories

| Category | Checks |
|----------|--------|
| **Address** | Overlap, alignment, conflicts |
| **Naming** | Duplicates, conventions |
| **Values** | Default value validity |
| **Structure** | Missing fields, invalid types |

---

## Data Structures

### Module Structure

```python
module = {
    "name": "spi_master",
    "base_addr": "0x1000",
    "source_file": "spi_master.yaml",
    "config": {
        "cdc_en": True,
        "cdc_stage": 2
    },
    "registers": [
        # List of register dicts
    ]
}
```

### Register Structure

```python
register = {
    "name": "control",
    "addr": "0x00",
    "access": "RW",          # RO, WO, RW
    "width": 32,
    "default": 0,
    "description": "Control register",
    "r_strobe": False,
    "w_strobe": True,
    "fields": []             # Optional subregisters
}
```

---

## Error Handling

```python
from axion_hdl import AxionHDL

axion = AxionHDL()

try:
    axion.add_source("nonexistent.yaml")
except FileNotFoundError:
    print("Source file not found")

try:
    axion.add_source("invalid.yaml")
    axion.analyze()
except ValueError as e:
    print(f"Parse error: {e}")

try:
    axion.generate_all()
except RuntimeError:
    print("Must analyze before generating")
```

---

## See Also

- [CLI Usage](cli-usage) - Command-line interface
- [Interactive GUI](gui) - Web-based interface
- [API Reference](api-reference) - Full API documentation
