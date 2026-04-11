# Axion-HDL

**AXI4-Lite register interfaces from VHDL, SystemVerilog, YAML, TOML, XML, or JSON. One command.**

[![PyPI](https://img.shields.io/pypi/v/axion-hdl.svg)](https://pypi.org/project/axion-hdl/)
[![Tests](https://github.com/bugratufan/axion-hdl/actions/workflows/tests.yml/badge.svg)](https://github.com/bugratufan/axion-hdl/actions/workflows/tests.yml)
[![Docs](https://readthedocs.org/projects/axion-hdl/badge/?version=stable)](https://axion-hdl.readthedocs.io/en/stable/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## Install

**For users:**
```bash
pip install axion-hdl
```

**For development:**
```bash
git clone https://github.com/bugratufan/axion-hdl.git
cd axion-hdl
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"  # Includes pytest, cocotb, etc.
```

## Use

```bash
# From VHDL with @axion annotations
axion-hdl -s my_module.vhd -o output/

# From SystemVerilog with @axion annotations
axion-hdl -s my_module.sv -o output/

# From YAML/TOML/XML/JSON
axion-hdl -s registers.yaml -o output/
axion-hdl -s registers.toml -o output/
```

**Output:** VHDL/SystemVerilog modules, C headers, documentation, YAML/TOML/XML/JSON exports.

## Define Registers

**VHDL** — embed in your code:
```vhdl
-- @axion_def BASE_ADDR=0x1000 CDC_EN
signal status  : std_logic_vector(31 downto 0); -- @axion RO
signal control : std_logic_vector(31 downto 0); -- @axion RW W_STROBE
```

**SystemVerilog** — same annotations, different syntax:
```systemverilog
// @axion_def BASE_ADDR=0x1000 CDC_EN
logic [31:0] status;  // @axion RO
logic [31:0] control; // @axion RW W_STROBE
```

**YAML** — standalone file:
```yaml
module: my_module
base_addr: "0x1000"
config:
  cdc_en: true
registers:
  - name: status
    access: RO
  - name: control
    access: RW
    w_strobe: true
```

**TOML** — clean, readable syntax:
```toml
module = "spi_master"
base_addr = "0x0000"

[config]
cdc_en = true
cdc_stage = 2

[[registers]]
name = "control"
addr = "0x00"
access = "RW"
w_strobe = true
description = "SPI control register"

[[registers]]
name = "status"
addr = "0x04"
access = "RO"
r_strobe = true
description = "SPI status register"
```

**Output** — one command:
```bash
axion-hdl -s spi_master.toml -o output --all
```

Generates: VHDL + SystemVerilog modules, C header, HTML docs, YAML/TOML/XML/JSON exports

## Features

- **Multi-format input** — VHDL/SystemVerilog annotations, YAML, TOML, XML, JSON
- **Multi-HDL output** — Generate both VHDL and SystemVerilog register interfaces
- **CDC support** — built-in clock domain crossing synchronizers
- **Subregisters** — pack multiple fields into one address
- **Wide signals** — auto-split 64-bit+ signals across addresses
- **Tested** — 307+ tests, GHDL simulation verified

## Documentation

📖 **[axion-hdl.readthedocs.io](https://axion-hdl.readthedocs.io/en/stable/)**

## Development & Testing

**Quick start:**
```bash
git clone https://github.com/bugratufan/axion-hdl.git
cd axion-hdl
make test  # Auto-installs dependencies and runs all tests
```

The `make test` command automatically:
- Creates a virtual environment if needed
- Installs all test dependencies
- Runs 307+ tests (Python + VHDL + cocotb)

> **Note:** For SystemVerilog linting tests, `verilator` must be installed on your system (`sudo apt install verilator`) for `make test` to pass.

**Manual setup (optional):**
```bash
make setup-dev  # Create venv + install dependencies
source venv/bin/activate
```

**CI/Automated environments:**
```bash
AXION_AUTO_INSTALL=1 make test  # Skip prompt, auto-install
```

**Contributing:**
```bash
git checkout develop
git checkout -b feature/your-feature
# Make changes
make test  # Dependencies auto-installed on first run
# Submit PR to develop branch
```

## License

MIT — [Bugra Tufan](mailto:bugratufan97@gmail.com)
