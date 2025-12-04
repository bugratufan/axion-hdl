# Release Notes Template for GitHub

Copy the content below when creating a GitHub release:

---

# 🚀 Axion-HDL v0.2.0 - Mixed Signal Width Support

**Automated AXI4-Lite Register Interface Generator for VHDL**

## ✨ Highlights

- 📏 **Wide Signal Support**: Signals up to 200+ bits with automatic multi-register allocation
- 🔢 **Narrow Signal Support**: 1-bit to 31-bit signals with proper masking
- 📄 **Enhanced C Headers**: Width definitions and multi-register macros
- 🧪 **Expanded Test Suite**: 53 tests covering all signal width scenarios

## 🆕 New Features

### Mixed Signal Width Support (AXION-025/026)

Now you can use signals of any width in your AXI register interfaces:

```vhdl
-- Narrow signals (< 32 bits)
signal enable_flag    : std_logic;                        -- @axion RW (1-bit)
signal channel_select : std_logic_vector(5 downto 0);     -- @axion RW (6-bit)
signal threshold      : std_logic_vector(15 downto 0);    -- @axion RW (16-bit)

-- Wide signals (> 32 bits)
signal counter_48     : std_logic_vector(47 downto 0);    -- @axion RO (48-bit, 2 regs)
signal timestamp_64   : std_logic_vector(63 downto 0);    -- @axion RO (64-bit, 2 regs)
signal data_100       : std_logic_vector(99 downto 0);    -- @axion RO (100-bit, 4 regs)
signal huge_data      : std_logic_vector(199 downto 0);   -- @axion RO (200-bit, 7 regs)
```

### Multi-Register Access

Wide signals are automatically split across multiple 32-bit registers:

| Signal (100-bit) | Address | Bits |
|------------------|---------|------|
| `data_100_REG0`  | 0x00    | [31:0] |
| `data_100_REG1`  | 0x04    | [63:32] |
| `data_100_REG2`  | 0x08    | [95:64] |
| `data_100_REG3`  | 0x0C    | [99:96] |

### Enhanced C Headers

```c
/* Signal Width Definitions */
#define MODULE_DATA_100_WIDTH      100
#define MODULE_DATA_100_NUM_REGS   4

/* Multi-Register Offsets */
#define MODULE_DATA_100_REG0_OFFSET  0x00
#define MODULE_DATA_100_REG1_OFFSET  0x04
#define MODULE_DATA_100_REG2_OFFSET  0x08
#define MODULE_DATA_100_REG3_OFFSET  0x0C
```

## 📦 Installation

```bash
pip install axion-hdl==0.2.0
```

## 🔄 Upgrade

```bash
pip install --upgrade axion-hdl
```

## 📋 What's Changed

### Added
- Wide signal support (48-bit to 200+ bit) with multi-register allocation
- Narrow signal support (1-bit to 31-bit) with proper masking
- C header width definitions (`*_WIDTH`, `*_NUM_REGS` macros)
- 13 new tests for AXION-025/026 requirements
- Mixed-width controller test module

### Improved
- Address validation for overlapping multi-register signals
- Documentation generation for wide signals
- Test suite reorganization (37 AXION + 16 AXI-LITE = 53 total)

## 🧪 Test Results

```
Total Tests: 53
  - AXION Requirements: 37 (AXION-001 to AXION-026)
  - AXI-LITE Protocol : 16
Passed: 53
Failed: 0

ALL REQUIREMENTS VERIFIED [PASS]
```

---

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
