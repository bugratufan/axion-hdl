# Getting Started

This guide will walk you through installing Axion-HDL and creating your first register interface.

## 1. Installation

Axion-HDL is available on PyPI.

```bash
pip install axion-hdl
```

### Prerequisites
- **Python 3.8+**
- **GHDL** (Optional, only required if you want to run simulations)

## 2. Your First Project

Let's create a simple "Blinky" controller with a speed register.

### Step A: Define Registers
You can define registers in VHDL comments, YAML, or JSON. Here, we'll use a **YAML** file for simplicity. Create a file named `blinky.yaml`:

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
      - name: mode
        bit_offset: 1
        width: 2
        access: RW
        description: "Blink pattern mode"

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
    description: "Current LED status debug"
```

### Step B: Generate Output
Run Axion-HDL pointing to your YAML file:

```bash
axion-hdl -s blinky.yaml -o output --all
```

This command tells Axion to:
- `-s blinky.yaml`: Use `blinky.yaml` as the source.
- `-o output`: Place generated files in the `output/` directory.
- `--all`: Generate VHDL, C headers, Documentation, and XML.

### Step C: Inspect the Output

Check the `output/` directory. You will find:

1.  **`blinky_ctrl_axion_reg.vhd`**: The AXI4-Lite slave module. Connect this to your AXI interconnect.
2.  **`blinky_ctrl_regs.h`**: C header with `#define` macros for your firmware.
3.  **`register_map.md`**: Beautiful documentation of your register map.
4.  **`blinky_ctrl_regs.xml`**: IP-XACT description.

## 3. Next Steps

- Learn about all supported input methods in **[Data Formats](Data_Formats.md)**.
- Explore command line options in **[CLI Reference](CLI_Reference.md)**.
- See how to handle clock domain crossing in **[Advanced Features](Advanced_Features.md)**.
