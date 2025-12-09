# Outputs & Integration

Axion-HDL generates several files for each analyzed module. This guide explains how to use them.

## 1. VHDL AXI4-Lite Slave (`*_axion_reg.vhd`)

This is the synthesizable VHDL module you instantiate in your design.

### Interface
It has a standard AXI4-Lite slave interface plus user logic ports.

```vhdl
entity my_module_axion_reg is
    port (
        -- AXI4-Lite Interface
        s_axi_aclk    : in  std_logic;
        s_axi_aresetn : in  std_logic;
        s_axi_awaddr  : in  std_logic_vector(31 downto 0);
        -- ... (other AXI signals)

        -- User Register Interface
        ctrl_reg_o    : out std_logic_vector(31 downto 0); -- Output for RW register
        status_reg_i  : in  std_logic_vector(31 downto 0)  -- Input for RO register
    );
end entity;
```

### Instantiation
Instantiate this component in your top-level wrapper and connect it to your AXI interconnect.
- **`*_o` Ports:** Drive your logic control signals (e.g., enable bits, thresholds).
- **`*_i` Ports:** Connect status signals from your logic (e.g., error flags, counters).

## 2. C Headers (`*_regs.h`)

For firmware development, Axion generates a C header file defining macro constants.

### Content
- **Base Address Offsets:** `MODULE_REG_NAME_OFFSET`
- **Bit Masks:** For sub-registers (fields).
- **Reset Values:** Default values.

### Example Usage

```c
#include "sensor_cntrl_regs.h"

// Write to Control Register
volatile uint32_t *base = (uint32_t *)0x40000000;
uint32_t ctrl = base[SENSOR_CNTRL_CONFIG_OFFSET / 4];

// Set ENABLE bit using generated mask
ctrl |= SENSOR_CNTRL_CONFIG_ENABLE_MASK;

base[SENSOR_CNTRL_CONFIG_OFFSET / 4] = ctrl;
```

## 3. Documentation (`register_map.md`)

A Markdown file summarizing the register map. Ideally, you commit this to your repo or serve it via GitHub Pages. It contains:
- Memory map table.
- Detailed bit-field diagrams (text-based).
- Access types and descriptions.
