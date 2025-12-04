# Axion-HDL

[![PyPI version](https://badge.fury.io/py/axion-hdl.svg)](https://badge.fury.io/py/axion-hdl)
[![Tests](https://github.com/bugratufan/axion-hdl/actions/workflows/tests.yml/badge.svg)](https://github.com/bugratufan/axion-hdl/actions/workflows/tests.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Axion-HDL** is an automated AXI4-Lite register interface generator for VHDL modules. It parses VHDL source files with special `@axion` annotations and generates complete, protocol-compliant AXI4-Lite register interfaces, C headers, XML register maps, and documentation.

## Naming Convention

| Context | Name | Example |
|---------|------|---------|
| PyPI Package | `axion-hdl` | `pip install axion-hdl` |
| Python Import | `axion_hdl` | `from axion_hdl import AxionHDL` |
| CLI Command | `axion-hdl` | `axion-hdl --help` |

## Features

- **AXI4-Lite Compliant**: Generates fully protocol-compliant AXI4-Lite slave interfaces
- **Annotation-Based**: Simple `@axion` annotations in VHDL comments define register behavior
- **Multiple Outputs**: Generates VHDL modules, C headers, XML (IP-XACT compatible), and Markdown documentation
- **Flexible Access Modes**: Supports RW (read-write), RO (read-only), and WO (write-only) registers
- **Strobe Support**: Optional read/write strobe signals for register access notification
- **CDC Support**: Built-in clock domain crossing with configurable synchronization stages
- **Module-Prefixed Headers**: C headers use module-prefixed macros for multi-module projects
- **Pure Python**: No external dependencies required

## Installation

### From PyPI (Recommended)

```bash
pip install axion-hdl
```

### From Source

```bash
git clone https://github.com/bugratufan/axion-hdl.git
cd axion-hdl
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/bugratufan/axion-hdl.git
cd axion-hdl
pip install -e ".[dev]"
```

## Quick Start

### 1. Add Annotations to Your VHDL

Add `@axion` annotations to your VHDL signals:

```vhdl
library ieee;
use ieee.std_logic_1164.all;

-- @axion_def BASE_ADDR=0x0000 CDC_EN CDC_STAGE=2

entity sensor_controller is
    port (
        clk   : in  std_logic;
        rst_n : in  std_logic
    );
end entity;

architecture rtl of sensor_controller is
    -- Read-only status register
    signal status_reg : std_logic_vector(31 downto 0);  -- @axion RO ADDR=0x00
    
    -- Write-only control register with write strobe
    signal control_reg : std_logic_vector(31 downto 0); -- @axion WO ADDR=0x04 W_STROBE
    
    -- Read-write config register
    signal config_reg : std_logic_vector(31 downto 0);  -- @axion RW ADDR=0x08
begin
    -- Your logic here
end architecture;
```

### 2. Generate Register Interface

#### Using CLI

```bash
# Generate all outputs
axion-hdl -s ./src -o ./output --all

# Generate only VHDL and C headers
axion-hdl -s ./rtl -o ./generated --vhdl --c-header

# Multiple source directories
axion-hdl -s ./src -s ./ip -o ./output

# Exclude specific files or directories
axion-hdl -s ./src -o ./output -e "testbenches" -e "*_tb.vhd"

# Show version
axion-hdl --version
```

#### Using Python API

```python
from axion_hdl import AxionHDL

# Initialize generator
axion = AxionHDL(output_dir="./output")

# Add source directories
axion.add_src("./src")

# Exclude files or directories (optional)
axion.exclude("testbenches")        # Exclude directory
axion.exclude("*_tb.vhd")           # Exclude testbench files
axion.exclude("debug_module.vhd")   # Exclude specific file

# Analyze VHDL files
axion.analyze()

# Generate all outputs
axion.generate_all()

# Or generate specific outputs
axion.generate_vhdl()
axion.generate_c_header()
axion.generate_xml()
axion.generate_documentation()
```

#### Exclusion Patterns

The `exclude()` method supports various pattern types:

| Pattern Type | Example | Description |
|--------------|---------|-------------|
| File name | `"test.vhd"` | Exclude specific file |
| Directory | `"testbenches"` | Exclude entire directory |
| Glob pattern | `"*_tb.vhd"` | Exclude files matching pattern |
| Multiple | `"test_*.vhd"` | Wildcard patterns |

```python
# Multiple exclusions at once
axion.exclude("error_cases", "*_tb.vhd", "deprecated")

# Remove exclusion
axion.include("deprecated")

# List current exclusions
axion.list_excludes()

# Clear all exclusions
axion.clear_excludes()
```

### 3. Generated Outputs

Axion-HDL generates:

| Output | File Pattern | Description |
|--------|--------------|-------------|
| VHDL Module | `*_axion_reg.vhd` | AXI4-Lite slave register interface |
| C Header | `*_regs.h` | Register definitions with module-prefixed macros |
| XML | `*_regs.xml` | IP-XACT compatible register description |
| Documentation | `register_map.md` | Markdown register map documentation |

## Annotation Syntax

### Module-Level Definition (`@axion_def`)

Place at the top of VHDL file, near entity declaration:

```vhdl
-- @axion_def BASE_ADDR=0x1000 CDC_EN CDC_STAGE=3
```

| Attribute | Description | Default |
|-----------|-------------|---------|
| `BASE_ADDR` | Module base address | `0x0000` |
| `CDC_EN` | Enable clock domain crossing | Disabled |
| `CDC_STAGE` | CDC synchronizer stages | `2` |

### Signal Annotation (`@axion`)

Place on the same line as signal declaration:

```vhdl
signal my_reg : std_logic_vector(31 downto 0); -- @axion <MODE> [ADDR=<offset>] [R_STROBE] [W_STROBE] [DESC="description"]
```

| Parameter | Values | Description |
|-----------|--------|-------------|
| Mode | `RO`, `WO`, `RW` | Register access mode (required) |
| `ADDR` | `0x00`-`0xFFFF` | Address offset (optional, auto-assigned if omitted) |
| `R_STROBE` | flag | Generate read strobe signal |
| `W_STROBE` | flag | Generate write strobe signal |
| `DESC` | `"text"` | Register description (appears in documentation) |

#### Examples with Description

```vhdl
signal status_reg : std_logic_vector(31 downto 0); -- @axion RO DESC="System status flags"
signal control_reg : std_logic_vector(31 downto 0); -- @axion WO W_STROBE DESC="Main control register"
signal config_reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x10 DESC="Configuration settings"
```

### Access Modes

| Mode | AXI Can | VHDL Logic Can | Port Direction |
|------|---------|----------------|----------------|
| `RO` | Read | Write | `in` |
| `WO` | Write | Read | `out` |
| `RW` | Read/Write | Read | `out` |

## Generated C Header Format

C headers use module-prefixed macro names for namespace isolation:

```c
// sensor_controller_regs.h
#ifndef SENSOR_CONTROLLER_REGS_H
#define SENSOR_CONTROLLER_REGS_H

#include <stdint.h>

/* Base Address */
#define SENSOR_CONTROLLER_BASE_ADDR          0x00000000

/* Register Offsets */
#define SENSOR_CONTROLLER_STATUS_REG_OFFSET  0x00000000
#define SENSOR_CONTROLLER_CONTROL_REG_OFFSET 0x00000004
#define SENSOR_CONTROLLER_CONFIG_REG_OFFSET  0x00000008

/* Absolute Addresses */
#define SENSOR_CONTROLLER_STATUS_REG_ADDR    0x00000000
#define SENSOR_CONTROLLER_CONTROL_REG_ADDR   0x00000004
#define SENSOR_CONTROLLER_CONFIG_REG_ADDR    0x00000008

/* Access Macros */
#define SENSOR_CONTROLLER_READ_STATUS_REG() \
    (*((volatile uint32_t*)(SENSOR_CONTROLLER_BASE_ADDR + SENSOR_CONTROLLER_STATUS_REG_OFFSET)))

#define SENSOR_CONTROLLER_WRITE_CONTROL_REG(val) \
    (*((volatile uint32_t*)(SENSOR_CONTROLLER_BASE_ADDR + SENSOR_CONTROLLER_CONTROL_REG_OFFSET)) = (val))

/* Register Structure */
typedef struct {
    volatile uint32_t status_reg;   /* 0x00 - RO */
    volatile uint32_t control_reg;  /* 0x04 - WO */
    volatile uint32_t config_reg;   /* 0x08 - RW */
} sensor_controller_regs_t;

#define SENSOR_CONTROLLER_REGS \
    ((volatile sensor_controller_regs_t*)(SENSOR_CONTROLLER_BASE_ADDR))

#endif
```

## AXI4-Lite Protocol Compliance

Generated VHDL modules are fully compliant with the AXI4-Lite specification:

- ✅ Independent address and data channels
- ✅ Proper VALID/READY handshaking
- ✅ BRESP/RRESP response signaling (OKAY/SLVERR)
- ✅ Address alignment checking
- ✅ Write strobe (WSTRB) support for byte-level writes
- ✅ Single-cycle response capability
- ✅ Proper reset behavior (all outputs deasserted)

## Project Structure

```
axion-hdl/
├── axion_hdl/                 # Main Python package
│   ├── __init__.py
│   ├── axion.py               # Main AxionHDL class
│   ├── cli.py                 # Command-line interface
│   ├── parser.py              # VHDL parser
│   ├── generator.py           # VHDL code generator
│   ├── doc_generators.py      # C header, XML, Markdown generators
│   ├── address_manager.py     # Address allocation
│   ├── annotation_parser.py   # @axion annotation parser
│   ├── vhdl_utils.py          # VHDL utilities
│   ├── code_formatter.py      # Code formatting utilities
│   └── README.md              # Library documentation
├── tests/                     # Test files
│   ├── c/                     # C header tests
│   │   └── test_c_headers.c
│   ├── python/                # Python tests
│   │   └── test_axion.py
│   ├── vhdl/                  # VHDL examples and testbenches
│   │   ├── sensor_controller.vhd
│   │   ├── spi_controller.vhd
│   │   └── multi_module_tb.vhd
│   └── run_full_test.sh       # Full test script
├── Makefile                   # Build and test automation
├── pyproject.toml             # Python project configuration
├── setup.py                   # Package setup
├── README.md                  # This file
└── LICENSE                    # MIT License
```

## Makefile Commands

```bash
make help           # Show all available commands

# Build & Install
make build          # Build package (sdist + wheel)
make install        # Install package locally
make dev-install    # Install in development mode

# Testing
make test           # Run all tests (Python + C + VHDL)
make test-python    # Run Python tests only
make test-c         # Run C header tests only
make test-vhdl      # Run VHDL simulation tests only

# Code Generation
make generate       # Generate all outputs from examples

# Distribution
make check          # Check package for PyPI
make upload-test    # Upload to TestPyPI
make upload         # Upload to PyPI

# Cleanup
make clean          # Clean generated files
make clean-all      # Clean everything including dist
```

## CLI Reference

```
usage: axion-hdl [-h] [-v] -s DIR [-o DIR] [--all] [--vhdl] [--doc]
                 [--doc-format FORMAT] [--xml] [--c-header]

Axion-HDL: Automated AXI4-Lite Register Interface Generator for VHDL

options:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -s DIR, --source DIR  Source directory containing VHDL files (can be repeated)
  -o DIR, --output DIR  Output directory (default: ./axion_output)

Generation Options:
  --all                 Generate all outputs
  --vhdl                Generate VHDL register interface modules
  --doc                 Generate register map documentation
  --doc-format FORMAT   Documentation format: md, html, or pdf
  --xml                 Generate XML register map description
  --c-header            Generate C header files

Examples:
  axion-hdl -s ./src -o ./output
  axion-hdl -s ./rtl -s ./ip -o ./generated --all
  axion-hdl -s ./hdl -o ./out --vhdl --c-header
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make test`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

- **Bugra Tufan** - [bugratufan97@gmail.com](mailto:bugratufan97@gmail.com)
- GitHub: [https://github.com/bugratufan/axion-hdl](https://github.com/bugratufan/axion-hdl)

## Contact

- **Author**: Bugra Tufan
- **Email**: bugratufan97@gmail.com
- **GitHub**: [https://github.com/bugratufan/axion-hdl](https://github.com/bugratufan/axion-hdl)
