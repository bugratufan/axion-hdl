# Axion HDL - Library Module

This directory contains the core Python modules for the Axion HDL register interface generator.

## Module Overview

| Module | Description |
|--------|-------------|
| `__init__.py` | Package initialization and public API exports |
| `axion.py` | Main `AxionHDL` class - orchestrates the entire workflow |
| `cli.py` | Command-line interface implementation |
| `parser.py` | VHDL file parser for extracting entity information |
| `generator.py` | VHDL code generator for AXI4-Lite register interfaces |
| `doc_generators.py` | Documentation generators (C headers, XML, Markdown) |
| `address_manager.py` | Address allocation and management utilities |
| `annotation_parser.py` | `@axion` annotation parser |
| `vhdl_utils.py` | VHDL parsing and formatting utilities |
| `code_formatter.py` | Code formatting utilities for various output formats |

## Core Classes

### AxionHDL

The main entry point for using Axion HDL programmatically.

```python
from axion_hdl import AxionHDL

axion = AxionHDL(output_dir="./output")
axion.add_src("./src")
axion.analyze()
axion.generate_all()
```

### AddressManager

Handles automatic and manual address allocation for registers.

```python
from axion_hdl import AddressManager

addr_mgr = AddressManager(start_addr=0x00, alignment=4)
addr1 = addr_mgr.allocate_address()           # Auto: 0x00
addr2 = addr_mgr.allocate_address()           # Auto: 0x04
addr3 = addr_mgr.allocate_address(0x100)      # Manual: 0x100
```

### VHDLUtils

Static utilities for VHDL parsing and code generation.

```python
from axion_hdl import VHDLUtils

# Parse signal type
type_name, high, low = VHDLUtils.parse_signal_type("std_logic_vector(31 downto 0)")

# Get signal width
width = VHDLUtils.get_signal_width(31, 0)  # Returns 32

# Extract entity name
entity = VHDLUtils.extract_entity_name(vhdl_code)
```

### AnnotationParser

Parses `@axion` annotations from VHDL comments.

```python
from axion_hdl import AnnotationParser

parser = AnnotationParser()
attrs = parser.parse_annotation("-- @axion RW ADDR=0x10 W_STROBE")
# Returns: {'access_mode': 'RW', 'address': 16, 'write_strobe': True, ...}
```

### CodeFormatter

Utilities for formatting generated code.

```python
from axion_hdl import CodeFormatter

# Format VHDL header comment
header = CodeFormatter.format_vhdl_header(
    filename="module.vhd",
    description="Register Interface"
)

# Format Markdown table
table = CodeFormatter.format_markdown_table(
    headers=["Register", "Address"],
    rows=[["CTRL", "0x00"]]
)
```

## Public API

All public classes and utilities are exported from the package root:

```python
from axion_hdl import (
    AxionHDL,
    AddressManager,
    VHDLUtils,
    AnnotationParser,
    CodeFormatter,
    VHDLParser,
    VHDLGenerator,
    DocGenerator,
    CHeaderGenerator,
    XMLGenerator,
    __version__,
)
```

## Version

Current version: `0.1.0`

For more information, see the [main README](../README.md) in the project root.
