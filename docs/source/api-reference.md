# API Reference

This reference documents the main Python classes and functions in Axion-HDL.

---

## Core Classes

### AxionHDL

The main entry point for programmatic usage.

```python
from axion_hdl import AxionHDL

# Create instance
axion = AxionHDL()

# Add source files or directories
axion.add_source("./rtl")           # Auto-detect by extension
axion.add_source("registers.yaml")

# Analyze all sources
modules = axion.analyze()

# Generate outputs
axion.set_output_dir("./output")
axion.generate_all()
```

#### Constructor

```python
AxionHDL(output_dir="./axion_output")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output_dir` | str | `"./axion_output"` | Output directory for generated files |

#### Source Management Methods

| Method | Description |
|--------|-------------|
| `add_source(path)` | Add source file/directory (auto-detects type by extension) |
| `add_src(path)` | Add VHDL source file or directory |
| `add_yaml_src(path)` | Add YAML source file or directory |
| `add_json_src(path)` | Add JSON source file or directory |
| `add_xml_src(path)` | Add XML source file or directory |
| `list_src()` | List all added source files and directories |

**Example:**

```python
axion = AxionHDL()

# Unified method (recommended)
axion.add_source("./rtl")           # Directory with VHDL files
axion.add_source("config.yaml")     # YAML file
axion.add_source("extra.json")      # JSON file

# Type-specific methods
axion.add_src("spi_master.vhd")     # VHDL only
axion.add_yaml_src("registers.yaml") # YAML only

# List sources
sources = axion.list_src()
print(sources)
```

#### Exclusion Methods

| Method | Description |
|--------|-------------|
| `exclude(*patterns)` | Exclude files/directories matching glob patterns |
| `include(*patterns)` | Remove patterns from exclusion list |
| `clear_excludes()` | Clear all exclusion patterns |
| `list_excludes()` | List current exclusion patterns |

**Example:**

```python
axion = AxionHDL()
axion.add_source("./rtl")

# Exclude testbenches and deprecated files
axion.exclude("*_tb.vhd", "test_*.vhd")
axion.exclude("deprecated")

# Check what's excluded
print(axion.list_excludes())
# Output: {'*_tb.vhd', 'test_*.vhd', 'deprecated'}

# Re-include something
axion.include("test_*.vhd")
```

#### Analysis Methods

| Method | Description |
|--------|-------------|
| `analyze()` | Parse all sources and return list of modules |
| `get_modules()` | Get list of analyzed modules |
| `is_analyzed` | Property: True if analyze() has been called |

**Example:**

```python
axion = AxionHDL()
axion.add_source("./rtl")
axion.exclude("*_tb.vhd")

# Analyze
modules = axion.analyze()
print(f"Found {len(modules)} modules")

# Access later
if axion.is_analyzed:
    modules = axion.get_modules()
    for m in modules:
        print(f"  {m['name']}: {len(m['registers'])} registers")
```

#### Generation Methods

| Method | Description |
|--------|-------------|
| `set_output_dir(path)` | Set output directory for generated files |
| `generate_all(doc_format="md")` | Generate all output formats |
| `generate_vhdl()` | Generate VHDL register modules |
| `generate_c_header()` | Generate C header files |
| `generate_documentation(format="md")` | Generate documentation (md, html, pdf) |
| `generate_xml()` | Generate XML register maps |
| `generate_yaml()` | Generate YAML register maps |
| `generate_json()` | Generate JSON register maps |

**Example:**

```python
axion = AxionHDL()
axion.add_source("registers.yaml")
axion.analyze()

# Set output directory
axion.set_output_dir("./generated")

# Generate everything
axion.generate_all()

# Or generate specific formats
axion.generate_vhdl()
axion.generate_c_header()
axion.generate_documentation(format="html")
```

#### Validation Methods

| Method | Description |
|--------|-------------|
| `run_rules(report_file=None)` | Run validation rules and print report |
| `check_address_overlaps()` | Check for address overlaps between modules |

**Example:**

```python
axion = AxionHDL()
axion.add_source("./rtl")
axion.analyze()

# Run rule checks
axion.run_rules()

# Or save to file
axion.run_rules(report_file="validation_report.txt")

# Check address overlaps
try:
    errors = axion.check_address_overlaps()
except AddressConflictError as e:
    print(f"Overlap: {e}")
```

```{eval-rst}
.. autoclass:: axion_hdl.AxionHDL
   :members:
   :undoc-members:
   :show-inheritance:
```

---

## RuleChecker

Validates register definitions against design rules.

```python
from axion_hdl.rule_checker import RuleChecker
from axion_hdl import AxionHDL

# Analyze sources
axion = AxionHDL()
axion.add_source("./rtl")
modules = axion.analyze()

# Run rule checks
checker = RuleChecker()
results = checker.run_all_checks(modules)

# Get report
print(checker.generate_report())

# Check status
if results["errors"]:
    print(f"Found {len(results['errors'])} errors")
```

### Methods

| Method | Description |
|--------|-------------|
| `run_all_checks(modules)` | Run all validation checks |
| `generate_report()` | Generate text report |
| `generate_json()` | Generate JSON report |
| `check_address_overlaps(modules)` | Check for address overlaps |
| `check_address_alignment(modules)` | Check 4-byte alignment |
| `check_default_values(modules)` | Validate default values fit width |
| `check_naming_conventions(modules)` | Validate VHDL identifiers |
| `check_duplicate_names(modules)` | Check for duplicate register names |
| `check_unique_module_names(modules)` | Check for duplicate module names |
| `check_documentation(modules)` | Check for missing descriptions |
| `check_logical_integrity(modules)` | Check module/register structure |
| `check_source_file_formats(dirs)` | Check source file syntax |

### Return Value

`run_all_checks()` returns a dictionary:

```python
{
    "errors": [
        {
            "rule": "address_overlap",
            "module": "spi_master",
            "message": "Registers control and status overlap at 0x00"
        }
    ],
    "warnings": [
        {
            "rule": "documentation",
            "module": "gpio",
            "message": "Register 'direction' missing description"
        }
    ]
}
```

### Check Categories

| Category | Rule ID | Description |
|----------|---------|-------------|
| Address | `address_overlap` | Registers share same address |
| Address | `address_alignment` | Not 4-byte aligned |
| Values | `default_value` | Default exceeds width |
| Naming | `naming_convention` | Invalid VHDL identifier |
| Naming | `duplicate_name` | Duplicate register name |
| Naming | `duplicate_module` | Duplicate module name |
| Documentation | `missing_description` | No description field |
| Structure | `empty_module` | Module has no registers |

```{eval-rst}
.. autoclass:: axion_hdl.rule_checker.RuleChecker
   :members:
   :undoc-members:
```

---

## Parsers

Individual parsers for each input format. Usually you don't need these directly - use `AxionHDL.add_source()` instead.

### VHDLParser

Parses VHDL files with `@axion` annotations.

```python
from axion_hdl.parser import VHDLParser

parser = VHDLParser()
modules = parser.parse_file("module.vhd")
```

### YAMLInputParser

Parses YAML register definition files.

```python
from axion_hdl.yaml_input_parser import YAMLInputParser

parser = YAMLInputParser()
module = parser.parse_file("registers.yaml")
```

### JSONInputParser

Parses JSON register definition files.

```python
from axion_hdl.json_input_parser import JSONInputParser

parser = JSONInputParser()
module = parser.parse_file("registers.json")
```

### XMLInputParser

Parses XML register definition files.

```python
from axion_hdl.xml_input_parser import XMLInputParser

parser = XMLInputParser()
module = parser.parse_file("registers.xml")
```

---

## Generators

Individual generators for each output format. Usually accessed via `AxionHDL.generate_*()` methods.

### VHDLGenerator

Generates AXI4-Lite slave VHDL modules.

```python
from axion_hdl.generator import VHDLGenerator

generator = VHDLGenerator(output_dir="./output")
output_path = generator.generate(module)
```

### DocGenerator

Generates documentation (Markdown, HTML, PDF).

```python
from axion_hdl.doc_generators import DocGenerator

generator = DocGenerator(output_dir="./output")
output_path = generator.generate_doc(modules, format="md")  # or "html"
```

### CHeaderGenerator

Generates C header files.

```python
from axion_hdl.doc_generators import CHeaderGenerator

generator = CHeaderGenerator(output_dir="./output")
output_path = generator.generate_header(module)
```

### XMLGenerator

Generates XML register maps.

```python
from axion_hdl.doc_generators import XMLGenerator

generator = XMLGenerator(output_dir="./output")
output_path = generator.generate_xml(module)
```

### YAMLGenerator

Generates YAML register maps.

```python
from axion_hdl.doc_generators import YAMLGenerator

generator = YAMLGenerator(output_dir="./output")
output_path = generator.generate_yaml(module)
```

### JSONGenerator

Generates JSON register maps.

```python
from axion_hdl.doc_generators import JSONGenerator

generator = JSONGenerator(output_dir="./output")
output_path = generator.generate_json(module)
```

---

## Data Structures

### Module Dictionary

Returned by `analyze()` and `get_modules()`:

```python
module = {
    "name": "spi_master",
    "entity_name": "spi_master",
    "source_file": "/path/to/spi_master.vhd",
    "base_address": 4096,           # Integer (0x1000)
    "base_addr": "0x1000",          # String representation
    "cdc_enabled": True,
    "cdc_stages": 2,
    "registers": [
        # List of Register dictionaries
    ]
}
```

### Register Dictionary

Each register in a module:

```python
register = {
    "name": "control",
    "addr": "0x00",
    "offset": 0,
    "access": "RW",              # "RO", "WO", or "RW"
    "width": 32,
    "default": 0,
    "description": "Control register",
    "r_strobe": False,
    "w_strobe": True,
    "fields": []                 # Optional subregisters
}
```

### Register Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | str | ✓ | Register/signal name |
| `addr` | str | ✓ | Hex address (e.g., "0x04") |
| `offset` | int | | Integer offset from base |
| `access` | str | ✓ | "RO", "WO", or "RW" |
| `width` | int | | Bit width (default: 32) |
| `default` | int/str | | Reset value (default: 0) |
| `description` | str | | Documentation |
| `r_strobe` | bool | | Generate read strobe (default: False) |
| `w_strobe` | bool | | Generate write strobe (default: False) |
| `fields` | list | | Subregister bit fields |

---

## Exceptions

### AddressConflictError

Raised when address conflicts are detected.

```python
from axion_hdl.address_manager import AddressConflictError

try:
    axion.check_address_overlaps()
except AddressConflictError as e:
    print(f"Conflict at address {e.address}")
    print(f"Between: {e.existing_signal} and {e.new_signal}")
```

---

## Module Reference

```{eval-rst}
.. automodule:: axion_hdl
   :members:
   :undoc-members:
   :show-inheritance:
```

---

## See Also

- [Python API Usage](python-api) - Practical examples and workflows
- [CLI Usage](cli-usage) - Command-line interface
- [Interactive GUI](gui) - Web-based interface
