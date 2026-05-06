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
axion.add_source("spi.toml")
axion.add_source("spi_master.vhd")
axion.add_source("design.sv")

# Add directory (recursive scan)
axion.add_source("./rtl")

# Add specific format
axion.add_yaml_src("registers.yaml")
axion.add_xml_src("controller.xml")
axion.add_json_src("gpio.json")
axion.add_toml_src("spi.toml")
axion.add_sv_src("design.sv")      # SystemVerilog source file
axion.add_sv_src("./rtl/sv")       # Directory of .sv/.svh files

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

# Generate all outputs (default: HTML documentation)
axion.generate_all()

# Generate all outputs with specific documentation format
axion.generate_all(doc_format="md")   # Use Markdown instead of HTML
axion.generate_all(doc_format="pdf")  # Use PDF (requires weasyprint)

# Generate specific formats only
axion.generate_vhdl()
axion.generate_systemverilog()
axion.generate_c_header()
axion.generate_documentation(format="html")  # HTML (default)
axion.generate_documentation(format="md")    # Markdown
axion.generate_documentation(format="pdf")   # PDF
axion.generate_xml()
axion.generate_yaml()
axion.generate_json()
```

**Documentation Output Formats:**

| Format | Output Files | Notes |
|--------|-------------|-------|
| **HTML** (default) | `index.html` + `html/*.html` | Multi-page interactive docs |
| **Markdown** | `register_map.md` | Single file, GitHub-compatible |
| **PDF** | `register_map.pdf` | Requires `weasyprint` package |

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

## CI/CD Integration

Use the Python API for advanced CI/CD pipelines with validation, conditional generation, and reporting.

### GitHub Actions with Python

Create `.github/workflows/validate-regs.yml`:

```yaml
name: Validate & Generate Registers

on:
  push:
    paths:
      - 'regs/**'
  pull_request:
    paths:
      - 'regs/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install Dependencies
        run: pip install axion-hdl
      
      - name: Validate Register Definitions
        run: |
          python3 << 'EOF'
          from axion_hdl import AxionHDL
          from axion_hdl.rule_checker import RuleChecker
          import sys
          
          axion = AxionHDL()
          axion.add_source("./regs")
          axion.exclude("*_tb.vhd")
          
          try:
              modules = axion.analyze()
          except Exception as e:
              print(f"❌ Analysis failed: {e}")
              sys.exit(1)
          
          print(f"📦 Found {len(modules)} modules")
          
          checker = RuleChecker()
          results = checker.run_all_checks(modules)
          
          # Report warnings
          for w in results["warnings"]:
              print(f"⚠️  {w['message']}")
          
          # Report errors
          for e in results["errors"]:
              print(f"❌ {e['message']}")
          
          if results["errors"]:
              print(f"\n❌ Validation failed with {len(results['errors'])} errors")
              sys.exit(1)
          else:
              print(f"\n✅ Validation passed!")
          EOF
      
      - name: Generate Files
        if: success()
        run: |
          python3 << 'EOF'
          from axion_hdl import AxionHDL
          
          axion = AxionHDL()
          axion.add_source("./regs")
          axion.exclude("*_tb.vhd")
          axion.analyze()
          axion.set_output_dir("./generated")
          axion.generate_all()
          print("✅ Generation complete")
          EOF
      
      - name: Upload Artifacts
        uses: actions/upload-artifact@v4
        with:
          name: generated-registers
          path: generated/
```

### GitLab CI with Python

```yaml
stages:
  - validate
  - generate

variables:
  REGS_DIR: "./regs"
  OUTPUT_DIR: "./generated"

validate-registers:
  stage: validate
  image: python:3.11
  script:
    - pip install axion-hdl
    - python3 scripts/validate_regs.py
  only:
    - merge_requests
    - main

generate-registers:
  stage: generate
  image: python:3.11
  script:
    - pip install axion-hdl
    - python3 scripts/generate_regs.py
  artifacts:
    paths:
      - generated/
    expire_in: 1 week
  only:
    - main
```

Create `scripts/validate_regs.py`:

```python
#!/usr/bin/env python3
"""Validate register definitions for CI."""

import sys
from axion_hdl import AxionHDL
from axion_hdl.rule_checker import RuleChecker

def main():
    axion = AxionHDL()
    axion.add_source("./regs")
    axion.exclude("*_tb.vhd")
    
    print("🔍 Analyzing register definitions...")
    modules = axion.analyze()
    
    print(f"📦 Found {len(modules)} modules:")
    for m in modules:
        print(f"   - {m['name']}: {len(m['registers'])} registers")
    
    print("\n🔎 Running validation checks...")
    checker = RuleChecker()
    results = checker.run_all_checks(modules)
    
    # Print results
    for w in results["warnings"]:
        print(f"⚠️  WARNING: {w['message']}")
    
    for e in results["errors"]:
        print(f"❌ ERROR: {e['message']}")
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"   Modules:  {len(modules)}")
    print(f"   Warnings: {len(results['warnings'])}")
    print(f"   Errors:   {len(results['errors'])}")
    
    if results["errors"]:
        print("\n❌ Validation FAILED")
        return 1
    else:
        print("\n✅ Validation PASSED")
        return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Pytest Integration

Create `tests/test_registers.py`:

```python
"""Test register definitions with pytest."""

import pytest
from axion_hdl import AxionHDL
from axion_hdl.rule_checker import RuleChecker

@pytest.fixture
def axion():
    """Create AxionHDL instance with sources."""
    a = AxionHDL()
    a.add_source("./regs")
    a.exclude("*_tb.vhd")
    return a

@pytest.fixture
def modules(axion):
    """Analyze and return modules."""
    return axion.analyze()

def test_modules_found(modules):
    """Verify at least one module is defined."""
    assert len(modules) > 0, "No modules found in ./regs"

def test_no_validation_errors(modules):
    """Verify no validation errors exist."""
    checker = RuleChecker()
    results = checker.run_all_checks(modules)
    
    error_messages = [e["message"] for e in results["errors"]]
    assert len(results["errors"]) == 0, f"Validation errors: {error_messages}"

def test_no_address_overlaps(axion, modules):
    """Verify no address overlaps between modules."""
    overlaps = axion.check_address_overlaps()
    assert len(overlaps) == 0, f"Address overlaps detected: {overlaps}"

def test_all_modules_have_registers(modules):
    """Verify each module has at least one register."""
    for m in modules:
        assert len(m["registers"]) > 0, f"Module {m['name']} has no registers"

def test_all_registers_have_descriptions(modules):
    """Verify all registers have descriptions."""
    missing = []
    for m in modules:
        for r in m["registers"]:
            if not r.get("description"):
                missing.append(f"{m['name']}.{r['name']}")
    
    assert len(missing) == 0, f"Registers missing descriptions: {missing}"
```

Run with:

```bash
pytest tests/test_registers.py -v
```

### Pre-commit Hook

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: validate-registers
        name: Validate Register Definitions
        entry: python scripts/validate_regs.py
        language: python
        additional_dependencies: ['axion-hdl']
        files: ^regs/.*\.(yaml|yml|json|xml|vhd)$
        pass_filenames: false
```

Install and run:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

### Custom Build Script

Create `scripts/build_all.py`:

```python
#!/usr/bin/env python3
"""
Complete build script with validation, generation, and reporting.
"""

import sys
import os
import json
from datetime import datetime
from axion_hdl import AxionHDL
from axion_hdl.rule_checker import RuleChecker

def main():
    # Configuration
    source_dir = os.environ.get("REGS_DIR", "./regs")
    output_dir = os.environ.get("OUTPUT_DIR", "./generated")
    
    print("=" * 60)
    print("Axion-HDL Build Script")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Initialize
    axion = AxionHDL()
    axion.add_source(source_dir)
    axion.exclude("*_tb.vhd")
    axion.exclude("deprecated")
    
    # Analyze
    print(f"\n📂 Source: {source_dir}")
    try:
        modules = axion.analyze()
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return 1
    
    print(f"📦 Modules: {len(modules)}")
    total_regs = sum(len(m["registers"]) for m in modules)
    print(f"📝 Registers: {total_regs}")
    
    # Validate
    print("\n🔎 Validating...")
    checker = RuleChecker()
    results = checker.run_all_checks(modules)
    
    if results["errors"]:
        print(f"❌ {len(results['errors'])} errors found:")
        for e in results["errors"]:
            print(f"   - {e['message']}")
        return 1
    
    if results["warnings"]:
        print(f"⚠️  {len(results['warnings'])} warnings:")
        for w in results["warnings"]:
            print(f"   - {w['message']}")
    
    print("✅ Validation passed")
    
    # Generate
    print(f"\n📁 Output: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)
    axion.set_output_dir(output_dir)
    axion.generate_all()
    
    # Report
    print("\n📋 Generated files:")
    for m in modules:
        print(f"   - {m['name']}_axion_reg.vhd")
        print(f"   - {m['name']}_regs.h")
    
    # Write build info
    build_info = {
        "timestamp": datetime.now().isoformat(),
        "modules": len(modules),
        "registers": total_regs,
        "warnings": len(results["warnings"]),
        "source": source_dir
    }
    
    with open(f"{output_dir}/build_info.json", "w") as f:
        json.dump(build_info, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✅ Build completed successfully!")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Example 7: SystemVerilog Project

```python
from axion_hdl import AxionHDL

axion = AxionHDL(output_dir="./output")

# Add SystemVerilog source files
axion.add_sv_src("./rtl/sensor_ctrl.sv")
axion.add_sv_src("./rtl/dma_engine.sv")

# Analyze
modules = axion.analyze()
print(f"Found {len(modules)} modules")

# Generate SystemVerilog register modules + C headers
axion.generate_systemverilog()
axion.generate_c_header()
axion.generate_documentation()
```

You can also mix VHDL and SystemVerilog sources in a single run:

```python
axion.add_src("./rtl/legacy_block.vhd")   # VHDL source
axion.add_sv_src("./rtl/new_block.sv")    # SystemVerilog source
axion.add_yaml_src("./regs/shared.yaml")  # YAML definitions

axion.analyze()
axion.generate_vhdl()            # VHDL output for legacy_block
axion.generate_systemverilog()   # SV output for new_block
axion.generate_c_header()        # C headers for all modules
```

---

## Python Register Model API

axion-hdl provides a Python simulation model of each register space for use in golden models.
The model enforces hardware access semantics (RO/WO/RW), supports bit-field masking, enum lookups,
and strobe callbacks.

### Getting a model from AxionHDL

```python
from axion_hdl import AxionHDL

axion = AxionHDL(output_dir="./output")
axion.add_source("my_module.yaml")
axion.analyze()

# Get a single module
space = axion.get_model("my_module")

# Get all modules
models = axion.get_models()   # Dict[str, RegisterSpaceModel]
```

### `AxionHDL` model methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get_model(module_name)` | `RegisterSpaceModel` | Return model for one module. Raises `RuntimeError` before `analyze()`, `KeyError` if not found. |
| `get_models()` | `Dict[str, RegisterSpaceModel]` | Return models for all analyzed modules. |
| `generate_python(output_dir=None)` | `List[str] \| False` | Generate `*_regs.py` files for all modules. Returns list of created paths, or `False` on error. |

### `RegisterSpaceModel`

```python
from axion_hdl import RegisterSpaceModel

space = RegisterSpaceModel.from_module_dict(module_dict)

space.name            # str — module name
space.base_address    # int — base address
space.registers       # Dict[str, RegisterModel]

# Bus-level access (absolute addresses)
space.read(0x1000)           # int
space.write(0x1000, 0x42)    # None; raises ReadOnlyError for RO

# Named access
space.control            # RegisterModel (via __getattr__)
space.control.value      # int

# Strobe callbacks
space.on_write("control", lambda name, val: ...)
space.on_read("irq_status", lambda name, val: ...)

# Utilities
space.reset()            # Restore all registers to defaults
space.dump()             # str — human-readable dump of all registers
space.get_register("control")           # RegisterModel
space.get_register_at(0x1000)           # RegisterModel

# Iteration in address order
for reg in space:
    print(reg.name, hex(reg.address))
```

### `RegisterModel`

```python
reg = space.get_register("status")

reg.name             # str
reg.address          # int — absolute address
reg.relative_address # int — offset from base
reg.access_mode      # str — 'RO', 'RW', or 'WO'
reg.width            # int — bit width (usually 32)
reg.default_value    # int
reg.is_packed        # bool — True if has bit fields
reg.fields           # Dict[str, FieldModel]

reg.value            # int — WO returns 0 (bus semantics)
reg.raw_value        # int — always actual value (golden model inspection)
reg.read()           # int — fires read_strobe callback if applicable
reg.write(0x42)      # None — fires write_strobe callback if applicable; raises ReadOnlyError for RO
reg.reset()          # Restore to default_value
reg.dump()           # str

# Attribute access to fields (packed registers only)
reg.ready            # FieldModel  (same as reg.fields['ready'])
```

### `FieldModel`

```python
field = space.status.fields["ready"]

field.name           # str
field.bit_low        # int
field.bit_high       # int
field.width          # int
field.access_mode    # str
field.mask           # int — pre-computed bit mask
field.default_value  # int

field.value          # int — extracted from parent raw_value
field.value = 1      # Write (raises ReadOnlyError if RO)
field.raw_value      # int — always actual bits (WO inspection)
field.enum_name      # Optional[str] — current value as enum string
field.reset()        # Restore to default_value without RO check
```

### Exceptions

```python
from axion_hdl import ReadOnlyError, AddressError

# ReadOnlyError — write attempted on RO register or field
try:
    space.write(0x1008, 0xFF)   # status is RO
except ReadOnlyError as e:
    print(e)   # "Register 'status' is read-only"

# AddressError — bus access at unregistered address
try:
    space.read(0xDEAD)
except AddressError as e:
    print(e)   # "No register at address 0xDEAD in space 'my_module'"
```

### Generating `*_regs.py` files

Use `--python` on the CLI or `generate_python()` in code to produce stand-alone model files:

```bash
axion-hdl -s my_module.yaml -o ./output --python
# Produces: ./output/my_module_regs.py
```

```python
# In your golden model (axion_hdl must be installed):
from my_module_regs import MY_MODULE

base = MY_MODULE.base_address
MY_MODULE.write(base + 0x0000, 0x1)
print(MY_MODULE.dump())
```

---

## See Also

- [CLI Usage](cli-usage) - Command-line interface
- [Interactive GUI](gui) - Web-based interface
- [API Reference](api-reference) - Full API documentation
