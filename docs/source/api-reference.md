# API Reference

This reference documents the main Python classes and functions in Axion-HDL.

## Core Classes

### AxionHDL

The main entry point for programmatic usage.

```python
from axion_hdl import AxionHDL

# Create instance
axion = AxionHDL()

# Add source files or directories
axion.add_source_path("./rtl")
axion.add_source_path("registers.yaml")

# Analyze all sources
modules = axion.analyze()

# Generate outputs
axion.generate(output_dir="./output", formats=["vhdl", "c_header", "md"])
```

```{eval-rst}
.. autoclass:: axion_hdl.AxionHDL
   :members:
   :undoc-members:
   :show-inheritance:
```

---

## Rule Checker

### RuleChecker

Validates register definitions against design rules.

```python
from axion_hdl.rule_checker import RuleChecker
from axion_hdl import AxionHDL

# Analyze sources
axion = AxionHDL()
axion.add_source_path("./rtl")
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

```{eval-rst}
.. autoclass:: axion_hdl.rule_checker.RuleChecker
   :members:
   :undoc-members:
```

---

## Parsers

### VHDL Parser

Parses VHDL files with `@axion` annotations.

```python
from axion_hdl.parser import VHDLParser

parser = VHDLParser()
module = parser.parse_file("module.vhd")
```

### YAML Parser

Parses YAML register definition files.

```python
from axion_hdl.yaml_parser import YAMLParser

parser = YAMLParser()
module = parser.parse_file("registers.yaml")
```

### JSON Parser

Parses JSON register definition files.

```python
from axion_hdl.json_parser import JSONParser

parser = JSONParser()
module = parser.parse_file("registers.json")
```

### XML Parser

Parses XML register definition files.

```python
from axion_hdl.xml_parser import XMLParser

parser = XMLParser()
module = parser.parse_file("registers.xml")
```

---

## Generators

### VHDL Generator

Generates AXI4-Lite slave VHDL modules.

```python
from axion_hdl.generators.vhdl_generator import VHDLGenerator

generator = VHDLGenerator()
vhdl_code = generator.generate(module)
generator.write_file(module, output_dir="./output")
```

### C Header Generator

Generates C header files with register macros.

```python
from axion_hdl.generators.c_header_generator import CHeaderGenerator

generator = CHeaderGenerator()
header_code = generator.generate(module)
generator.write_file(module, output_dir="./output")
```

### Documentation Generator

Generates Markdown/HTML documentation.

```python
from axion_hdl.generators.doc_generator import DocGenerator

generator = DocGenerator(format="md")  # or "html"
doc = generator.generate(modules)
generator.write_file(modules, output_dir="./output")
```

---

## Data Structures

### Module

Represents a parsed module with registers.

```python
module = {
    "name": "spi_master",
    "base_addr": "0x1000",
    "source_file": "spi_master.vhd",
    "config": {
        "cdc_en": True,
        "cdc_stage": 2
    },
    "registers": [
        {
            "name": "control",
            "addr": "0x00",
            "access": "RW",
            "width": 32,
            "default": 0,
            "description": "Control register",
            "r_strobe": False,
            "w_strobe": True
        }
    ]
}
```

### Register

Individual register definition:

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Register/signal name |
| `addr` | str | Hex address (e.g., "0x04") |
| `access` | str | "RO", "WO", or "RW" |
| `width` | int | Bit width (1-1024) |
| `default` | int/str | Reset value |
| `description` | str | Documentation |
| `r_strobe` | bool | Generate read strobe |
| `w_strobe` | bool | Generate write strobe |
| `fields` | list | Subregister fields (optional) |

---

## Module Reference

```{eval-rst}
.. automodule:: axion_hdl
   :members:
   :undoc-members:
   :show-inheritance:
```
