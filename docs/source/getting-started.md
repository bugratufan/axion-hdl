# Getting Started

This guide will walk you through installing Axion-HDL and creating your first register interface.

## Installation

Axion-HDL is available on PyPI:

```bash
pip install axion-hdl
```

### Prerequisites

- **Python 3.7+**
- **GHDL** (Optional, only required for simulations)

## Quick Start

### Step 1: Define Registers

Create a YAML file `blinky.yaml`:

```yaml
module: blinky_ctrl
base_addr: 0x00001000
registers:
  - name: control
    addr: 0x00
    description: "Main control register"
    fields:
      - name: enable
        bit_offset: 0
        width: 1
        access: RW
        description: "Enable LED blinking"

  - name: speed
    addr: 0x04
    access: RW
    width: 32
    default: 1000
    description: "Blink speed in ms"

  - name: status
    addr: 0x08
    access: RO
    width: 32
    description: "Current LED status"
```

### Step 2: Generate Output

```bash
axion-hdl -s blinky.yaml -o output --all
```

### Step 3: Check Generated Files

The `output/` directory will contain:

- `blinky_ctrl_axion_reg.vhd` - AXI4-Lite slave module
- `blinky_ctrl_regs.h` - C header with macros
- `register_map.md` - Documentation
- `blinky_ctrl_regs.xml` - IP-XACT description

## Next Steps

- [Data Formats](data-formats) - Learn about all input formats
- [CLI Reference](cli-reference) - Master the command-line
- [Advanced Features](advanced-features) - CDC, subregisters, etc.
