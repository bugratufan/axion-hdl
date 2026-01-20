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

Create a YAML file `led_blinker.yaml`:

```yaml
module: led_blinker
base_addr: "0x0000"
registers:
  - name: control
    addr: "0x00"
    access: RW
    width: 32
    description: "LED control register"

  - name: led_state
    addr: "0x04"
    access: RO
    width: 32
    description: "Current LED state"

  - name: period_ms
    addr: "0x08"
    access: RW
    width: 32
    default: 500
    description: "Blink period in milliseconds"
```

### Step 2: Generate Output

```bash
axion-hdl -s led_blinker.yaml -o output --all
```

### Step 3: Check Generated Files

The `output/` directory will contain:

| File | Description |
|------|-------------|
| `led_blinker_axion_reg.vhd` | AXI4-Lite slave module |
| `led_blinker_regs.h` | C header with macros |
| `index.html` | Register documentation (main page) |
| `html/` | Module documentation pages |
| `led_blinker_regs.xml` | IP-XACT description |
| `led_blinker_regs.yaml` | YAML register map |
| `led_blinker_regs.json` | JSON register map |

### Step 4: Integrate

Instantiate the generated module in your top-level VHDL:

```vhdl
led_blinker_regs : entity work.led_blinker_axion_reg
    port map (
        axi_aclk    => clk,
        axi_aresetn => rst_n,
        -- AXI4-Lite bus connections
        axi_awaddr  => s_axi_awaddr,
        axi_awvalid => s_axi_awvalid,
        -- ... other AXI signals ...
        -- Register signals
        control     => control_reg,
        led_state   => led_state_sig,
        period_ms   => period_reg
    );
```

## Next Steps

- [Data Formats](data-formats) - Learn about all input formats
- [CLI Reference](cli-reference) - Master the command-line
- [GUI](gui) - Interactive web-based register management
