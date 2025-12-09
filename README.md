# Axion-HDL

[![PyPI version](https://img.shields.io/pypi/v/axion-hdl.svg)](https://pypi.org/project/axion-hdl/)
[![Tests](https://github.com/bugratufan/axion-hdl/actions/workflows/tests.yml/badge.svg)](https://github.com/bugratufan/axion-hdl/actions/workflows/tests.yml)
[![Python 3.8+](https://img.shields.io/pypi/pyversions/axion-hdl.svg)](https://pypi.org/project/axion-hdl/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Axion-HDL** is an automated AXI4-Lite register interface generator for VHDL. Parse VHDL files with `@axion` annotations or XML register definitions to generate complete, protocol-compliant register interfaces, C headers, and documentation.

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **Dual Input Formats** | VHDL with `@axion` annotations or standalone XML register definitions |
| **AXI4-Lite Compliant** | Fully protocol-compliant slave interfaces with proper handshaking |
| **Subregisters** | Pack multiple bit-fields into single 32-bit registers |
| **Default Values** | Define reset values with `DEFAULT` attribute |
| **Wide Signals** | Automatic multi-register allocation for signals >32 bits |
| **Multiple Outputs** | VHDL, C headers, XML (IP-XACT), Markdown documentation |
| **CDC Support** | Built-in clock domain crossing synchronizers |
| **Pure Python** | No external dependencies, Python 3.8+ |

## 📦 Installation

```bash
pip install axion-hdl
```

## 🚀 Quick Start

### Option 1: VHDL Annotations

Add `@axion` annotations directly in your VHDL:

```vhdl
-- @axion_def BASE_ADDR=0x0000 CDC_EN CDC_STAGE=2

entity sensor_controller is
    port (clk : in std_logic; rst_n : in std_logic);
end entity;

architecture rtl of sensor_controller is
    signal status_reg  : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00 DESC="Status"
    signal control_reg : std_logic_vector(31 downto 0); -- @axion WO ADDR=0x04 W_STROBE
    signal config_reg  : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x08 DEFAULT=0xCAFE
begin
end architecture;
```

```bash
axion-hdl -s sensor_controller.vhd -o ./output
```

### Option 2: XML Register Definition

Define registers in standalone XML files:

```xml
<register_map module="sensor_controller" base_addr="0x0000">
    <config cdc_en="true" cdc_stage="2"/>
    <register name="status_reg"  addr="0x00" access="RO" width="32" description="Status"/>
    <register name="control_reg" addr="0x04" access="WO" width="32" w_strobe="true"/>
    <register name="config_reg"  addr="0x08" access="RW" width="32" default="0xCAFE"/>
</register_map>
```

```bash
axion-hdl -s registers.xml -o ./output
```

### Generated Outputs

| Output | File | Description |
|--------|------|-------------|
| VHDL | `*_axion_reg.vhd` | AXI4-Lite slave register interface |
| C Header | `*_regs.h` | Module-prefixed register definitions |
| XML | `*_regs.xml` | IP-XACT compatible register map |
| Docs | `register_map.md` | Markdown documentation |

---

## 📖 Annotation Reference

### Module-Level (`@axion_def`)

```vhdl
-- @axion_def BASE_ADDR=0x1000 CDC_EN CDC_STAGE=3
```

| Attribute | Description | Default |
|-----------|-------------|---------|
| `BASE_ADDR` | Module base address | `0x0000` |
| `CDC_EN` | Enable clock domain crossing | Disabled |
| `CDC_STAGE` | Synchronizer stages (2-4) | `2` |

### Signal-Level (`@axion`)

```vhdl
signal my_reg : std_logic_vector(31 downto 0); -- @axion <MODE> [options]
```

| Parameter | Values | Description |
|-----------|--------|-------------|
| Mode | `RO`, `WO`, `RW` | Access mode (required) |
| `ADDR` | `0x00`-`0xFFFF` | Address offset (auto-assigned if omitted) |
| `DEFAULT` | `0x...` or decimal | Reset value (default: 0) |
| `R_STROBE` | flag | Generate read strobe signal |
| `W_STROBE` | flag | Generate write strobe signal |
| `DESC` | `"text"` | Register description |

#### Examples

```vhdl
signal status  : std_logic_vector(31 downto 0); -- @axion RO DESC="System status"
signal control : std_logic_vector(31 downto 0); -- @axion WO W_STROBE DEFAULT=0x01
signal config  : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x10 R_STROBE W_STROBE
```

---

## 🧩 Advanced Features

### Subregisters (Packed Bit-Fields)

Pack multiple fields into a single 32-bit register:

```vhdl
-- Enable field at bit 0 (1 bit)
signal enable : std_logic; -- @axion RW REG_NAME=control_reg BIT_OFFSET=0 DEFAULT=1

-- Mode field at bits 2:1 (2 bits)
signal mode : std_logic_vector(1 downto 0); -- @axion RW REG_NAME=control_reg BIT_OFFSET=1

-- IRQ mask at bits 7:4 (4 bits)
signal irq_mask : std_logic_vector(3 downto 0); -- @axion RW REG_NAME=control_reg BIT_OFFSET=4
```

Or in XML:

```xml
<register name="enable"   reg_name="control_reg" addr="0x00" width="1" access="RW" bit_offset="0" default="1"/>
<register name="mode"     reg_name="control_reg" addr="0x00" width="2" access="RW" bit_offset="1"/>
<register name="irq_mask" reg_name="control_reg" addr="0x00" width="4" access="RW" bit_offset="4"/>
```

### Wide Signals (>32 bits)

Signals wider than 32 bits automatically span multiple registers:

```vhdl
signal counter_64bit : std_logic_vector(63 downto 0); -- @axion RO ADDR=0x00
-- Accessible at: 0x00 (bits 31:0), 0x04 (bits 63:32)

signal data_256bit : std_logic_vector(255 downto 0); -- @axion RW ADDR=0x10
-- Accessible at: 0x10, 0x14, 0x18, 0x1C, 0x20, 0x24, 0x28, 0x2C
```

### Clock Domain Crossing (CDC)

Enable automatic synchronization between AXI and module clock domains:

```vhdl
-- @axion_def CDC_EN CDC_STAGE=3

-- RO registers: synced from module_clk → axi_aclk
signal sensor_data : std_logic_vector(31 downto 0); -- @axion RO

-- RW/WO registers: synced from axi_aclk → module_clk
signal control : std_logic_vector(31 downto 0); -- @axion RW
```

---

## 💻 CLI Reference

```bash
# Basic usage
axion-hdl -s ./src -o ./output

# Single file (auto-detects VHDL or XML by extension)
axion-hdl -s module.vhd -o ./output
axion-hdl -s registers.xml -o ./output

# Multiple sources (files and directories)
axion-hdl -s ./rtl -s ./extra/module.vhd -s definitions.xml -o ./output

# Selective outputs
axion-hdl -s ./src -o ./output --vhdl --c-header

# Exclude patterns
axion-hdl -s ./src -o ./output -e "*_tb.vhd" -e "testbenches"

# Documentation format
axion-hdl -s ./src -o ./output --doc --doc-format html
```

### Options

| Option | Description |
|--------|-------------|
| `-s, --source PATH` | Source file (.vhd, .vhdl, .xml) or directory |
| `-o, --output DIR` | Output directory (default: ./axion_output) |
| `-e, --exclude PATTERN` | Exclude pattern (can repeat) |
| `--all` | Generate all outputs (default) |
| `--vhdl` | Generate VHDL only |
| `--c-header` | Generate C header only |
| `--xml` | Generate XML only |
| `--doc` | Generate documentation only |
| `--doc-format FORMAT` | Doc format: md, html, pdf |

---

## 🐍 Python API

```python
from axion_hdl import AxionHDL

axion = AxionHDL(output_dir="./output")

# Add sources (auto-detects type by extension)
axion.add_source("./rtl")           # Directory
axion.add_source("module.vhd")      # VHDL file
axion.add_source("registers.xml")   # XML file

# Or use type-specific methods
axion.add_src("./vhdl_files")       # VHDL sources
axion.add_xml_src("./xml_files")    # XML sources

# Exclude patterns
axion.exclude("*_tb.vhd", "testbenches")

# Analyze and generate
axion.analyze()
axion.generate_all()

# Or generate specific outputs
axion.generate_vhdl()
axion.generate_c_header()
axion.generate_xml()
axion.generate_documentation()
```

---

## 🧪 Testing

The project includes 201 automated tests covering all requirements:

```bash
make test              # Run all tests
make test-python       # Python tests only
make test-vhdl         # VHDL simulation tests only
```

Test categories: AXION (37), AXI-LITE (16), PARSER (20), GEN (30), CLI (14), CDC (8), ADDR (9), ERR (9), STRESS (6), SUB (9), DEF (10)

---

## 📁 Project Structure

```
axion-hdl/
├── axion_hdl/           # Main Python package
│   ├── axion.py         # AxionHDL main class
│   ├── cli.py           # Command-line interface
│   ├── parser.py        # VHDL parser
│   ├── xml_input_parser.py  # XML parser
│   ├── generator.py     # VHDL generator
│   └── doc_generators.py    # C/XML/MD generators
├── tests/
│   ├── vhdl/            # VHDL examples & testbenches
│   ├── xml/             # XML examples
│   └── python/          # Python unit tests
├── requirements.md      # Full requirements specification
└── CHANGELOG.md         # Version history
```

---

## 📋 Naming Convention

| Context | Name | Example |
|---------|------|---------|
| PyPI Package | `axion-hdl` | `pip install axion-hdl` |
| Python Import | `axion_hdl` | `from axion_hdl import AxionHDL` |
| CLI Command | `axion-hdl` | `axion-hdl --help` |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch from `develop`
3. Make your changes
4. Run tests: `make test`
5. Submit a pull request to `develop`

---

## 📄 License

MIT License - see [LICENSE](LICENSE)

---

## 👤 Author

**Bugra Tufan**  
📧 [bugratufan97@gmail.com](mailto:bugratufan97@gmail.com)  
🔗 [github.com/bugratufan/axion-hdl](https://github.com/bugratufan/axion-hdl)
