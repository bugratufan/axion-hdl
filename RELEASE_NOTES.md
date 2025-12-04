# Release Notes Template for GitHub

Copy the content below when creating a GitHub release:

---

# 🚀 Axion-HDL v0.3.0 - Description & Conflict Detection

**Automated AXI4-Lite Register Interface Generator for VHDL**

## ✨ Highlights

- � **DESC Attribute**: Add human-readable descriptions to registers
- ⚠️ **Address Conflict Detection**: Clear error messages with requirement references
- � **Exclude Patterns**: Filter files and directories from parsing

## 🆕 New Features

### Register Descriptions (DESC Attribute)

Add documentation directly in your VHDL code:

```vhdl
signal status_reg : std_logic_vector(31 downto 0);    -- @axion RO DESC="System status flags"
signal control_reg : std_logic_vector(31 downto 0);   -- @axion WO W_STROBE DESC="Main control register"
signal config_reg : std_logic_vector(31 downto 0);    -- @axion RW ADDR=0x10 DESC="Configuration settings"
```

Descriptions appear in all outputs:
- **Markdown**: Register table and Port Descriptions
- **C Header**: Comments on definitions
- **XML**: `<spirit:description>` element
- **VHDL**: Port signal comments

### Address Conflict Detection

Clear, actionable error messages when addresses conflict:

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                          ADDRESS CONFLICT ERROR                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Address 0x0000 is already assigned in module 'my_module'                     
╠══════════════════════════════════════════════════════════════════════════════╣
║ Existing register: reg_alpha                                                ║
║ Conflicting register: reg_beta                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ VIOLATED REQUIREMENTS:                                                       ║
║   • AXION-006: Each register must have a unique address                      ║
║   • AXION-007: Address offsets must be correctly calculated                  ║
║   • AXION-008: No address overlap allowed within a module                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ SOLUTION: Change the ADDR attribute for one of the registers:                ║
║   signal reg_beta : ... -- @axion ... ADDR=0x0004             
║   Or remove ADDR to use auto-assignment                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### Exclude Patterns

Filter out files and directories from parsing:

```python
# Python API
axion.exclude("error_cases")        # Exclude directory
axion.exclude("*_tb.vhd")           # Exclude testbench files
axion.exclude("debug.vhd", "test")  # Multiple patterns
```

```bash
# CLI
axion-hdl -s ./src -o ./out -e "testbenches" -e "*_tb.vhd"
```

## 📦 Installation

```bash
pip install axion-hdl==0.3.0
```

## 🔄 Upgrade

```bash
pip install --upgrade axion-hdl
```

## 📋 What's Changed

### Added
- DESC attribute for register descriptions
- AddressConflictError with detailed error messages
- Exclude patterns for file/directory filtering
- `-e/--exclude` CLI option
- Address conflict test suite

### Improved
- Error reporting with requirement references
- Parser tracks signal-to-address mapping
- Documentation with exclusion examples

## 🧪 Test Results

```
Total Tests: 53 + 3 (Address Conflict Tests)
  - AXION Requirements: 37 (AXION-001 to AXION-026)
  - AXI-LITE Protocol : 16
  - Address Conflict  : 3
Passed: All
Failed: 0

ALL REQUIREMENTS VERIFIED [PASS]
```

---

# Previous Release: v0.2.0 - Mixed Signal Width Support

# Previous Release: v0.1.1

# 🐛 Axion-HDL v0.1.1 - CDC Bug Fix Release

**Automated AXI4-Lite Register Interface Generator for VHDL**

## 🐛 Bug Fixes

### CDC Implementation Fixed
- **Critical**: Fixed missing CDC synchronization process in generated VHDL code
- CDC sync signals were being declared but never actually used in previous version
- Now properly implements 3-stage synchronization for cross-domain signals

### Testbench Improvements  
- Fixed deadlock issue in AXI write procedures where simultaneous `awready`/`wready` assertion caused simulation hang
- Increased simulation time to allow all 40 requirement tests to complete

## 📦 Installation

```bash
pip install axion-hdl==0.1.1
```

## 🔄 Upgrade

```bash
pip install --upgrade axion-hdl
```

## 📋 What's Changed

- RO registers now properly sync from `module_clk` → `axi_aclk` domain
- WO/RW registers now properly sync from `axi_aclk` → `module_clk` domain
- All 40 requirement tests (24 AXION + 16 AXI-LITE) pass successfully

---

# Previous Release: v0.1.0

# �🚀 Axion-HDL v0.1.0 - Initial Release

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
