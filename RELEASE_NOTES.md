# Release Notes Template for GitHub

Copy the content below when creating a GitHub release:

---

# 🚀 Axion-HDL v0.1.0 - Initial Release

**Automated AXI4-Lite Register Interface Generator for VHDL**

## ✨ Highlights

- 🔧 **Simple Annotations**: Just add `@axion` comments to your VHDL signals
- ⚡ **Full AXI4-Lite Compliance**: Protocol-compliant register interfaces
- 📄 **Multiple Outputs**: VHDL, C headers, XML, and Markdown documentation
- 🔄 **CDC Support**: Built-in clock domain crossing with configurable stages
- 🐍 **Pure Python**: No external dependencies, works out of the box

## 📦 Installation

```bash
pip install axion-hdl
```

## 🎯 Quick Start

### 1. Annotate your VHDL

```vhdl
-- @axion_def BASE_ADDR=0x1000

signal status_reg  : std_logic_vector(31 downto 0);  -- @axion RO ADDR=0x00
signal control_reg : std_logic_vector(31 downto 0);  -- @axion WO ADDR=0x04 W_STROBE
signal config_reg  : std_logic_vector(31 downto 0);  -- @axion RW ADDR=0x08
```

### 2. Generate outputs

```bash
# CLI
axion-hdl -s ./src -o ./output --all

# Python API
from axion_hdl import AxionHDL
axion = AxionHDL(output_dir="./output")
axion.add_src("./src")
axion.analyze()
axion.generate_all()
```

### 3. Get your files

- `*_axion_reg.vhd` - AXI4-Lite register interface module
- `*_regs.h` - C header with register definitions
- `*_regs.xml` - IP-XACT compatible register map
- `register_map.md` - Documentation

## 🆕 What's New

### Core Features
- VHDL parser with `@axion` annotation support
- AXI4-Lite slave interface generator
- C header generator with module-prefixed macros
- XML register map generator (IP-XACT compatible)
- Markdown documentation generator

### Annotation System
- Module-level `@axion_def` for base address and CDC config
- Signal-level `@axion` with RO/WO/RW access modes
- Automatic or manual address assignment
- Read/Write strobe generation

### AXI4-Lite Compliance
- Independent address and data channels
- Proper VALID/READY handshaking
- SLVERR for invalid address access
- Byte-level write strobe (WSTRB) support

## 📚 Documentation

- [README](https://github.com/bugratufan/axion-hdl#readme)
- [Full Changelog](https://github.com/bugratufan/axion-hdl/blob/main/CHANGELOG.md)

## 🙏 Feedback

Found a bug or have a feature request? Please [open an issue](https://github.com/bugratufan/axion-hdl/issues).

---

**Full Changelog**: https://github.com/bugratufan/axion-hdl/blob/main/CHANGELOG.md
