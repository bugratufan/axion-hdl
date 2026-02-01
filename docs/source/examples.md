# Examples

Working examples are available in the [examples directory](https://github.com/bugratufan/axion-hdl/tree/develop/docs/examples). This section provides complete examples with input files, commands, and generated outputs for each format.

---

## VHDL Example: SPI Master

**Input File (`spi_master.vhd`):**

```vhdl
--------------------------------------------------------------------------------
-- SPI Master Example - VHDL Annotations
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- Enable CDC with 2 synchronization stages (default)
-- @axion_def BASE_ADDR=0x0000 CDC_EN

entity spi_master is
    port (
        clk       : in  std_logic;
        rst_n     : in  std_logic;
        spi_clk   : out std_logic;
        spi_mosi  : out std_logic;
        spi_miso  : in  std_logic;
        spi_cs_n  : out std_logic
    );
end entity spi_master;

architecture rtl of spi_master is
    -- Control register: start transfer, clock divider, etc.
    signal control_reg : std_logic_vector(31 downto 0); -- @axion RW W_STROBE DESC="SPI control: bit0=start, bits[15:8]=clk_div"
    
    -- Status register: busy flag, transfer complete, errors
    signal status_reg : std_logic_vector(31 downto 0); -- @axion RO R_STROBE DESC="SPI status: bit0=busy, bit1=done, bit2=error"
    
    -- TX data register (write-only from software perspective)
    signal tx_data_reg : std_logic_vector(31 downto 0); -- @axion WO DESC="Transmit data buffer"
    
    -- RX data register (read-only from software perspective)
    signal rx_data_reg : std_logic_vector(31 downto 0); -- @axion RO DESC="Receive data buffer"
    
    -- Configuration register at specific address
    signal config_reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x20 DESC="SPI configuration"
    
    -- Interrupt control
    signal irq_enable_reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x30 DESC="Interrupt enable mask"
    signal irq_status_reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x34 R_STROBE W_STROBE DESC="Interrupt status"
begin
    spi_clk  <= '0';
    spi_mosi <= '0';
    spi_cs_n <= '1';
end architecture rtl;
```

**Command:**

```bash
axion-hdl -s spi_master.vhd -o output --all
```

**Terminal Output:**

```
VHDL source file added: spi_master.vhd

============================================================
Starting analysis of VHDL files...
============================================================
Parsing VHDL file: spi_master.vhd
Found 1 modules from VHDL files.

Analysis complete. Found 1 total modules.

================================================================================
Module: spi_master
File: spi_master.vhd
CDC: Enabled (Stages: 2)
Base Address: 0x0000
================================================================================

Signal Name               Type     Abs.Addr   Offset     Access   Strobes
------------------------- -------- ---------- ---------- -------- ---------------
control_reg               [31:0]   0x00       0x00       RW       WR
status_reg                [31:0]   0x04       0x04       RO       RD
tx_data_reg               [31:0]   0x08       0x08       WO       None
rx_data_reg               [31:0]   0x0C       0x0C       RO       None
config_reg                [31:0]   0x20       0x20       RW       None
irq_enable_reg            [31:0]   0x30       0x30       RW       None
irq_status_reg            [31:0]   0x34       0x34       RW       RD, WR

Total Registers: 7

================================================================================

============================================================
Generating VHDL register modules...
============================================================
  Generated: spi_master_axion_reg.vhd

============================================================
Generating documentation (MD)...
============================================================
  Generated: register_map.md

============================================================
Generating XML register map...
============================================================
  Generated: spi_master_regs.xml

============================================================
Generating YAML register map...
============================================================
  Generated: spi_master_regs.yaml

============================================================
Generating JSON register map...
============================================================
  Generated: spi_master_regs.json

============================================================
Generating C header files...
============================================================
  Generated: spi_master_regs.h

============================================================
All files generated successfully!
Output directory: output
============================================================
```

**Generated VHDL Module (`spi_master_axion_reg.vhd`):**

```vhdl
--------------------------------------------------------------------------------
-- File: spi_master_axion_reg.vhd
-- Description: AXI Register Interface Module
-- Generated by Axion HDL
--
-- Module: spi_master
-- Source: spi_master.vhd
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity spi_master_axion_reg is
    generic (
        BASE_ADDR : std_logic_vector(31 downto 0) := x"00000000"
    );
    port (
        -- AXI4-Lite Interface
        axi_aclk    : in  std_logic;
        axi_aresetn : in  std_logic;
        
        -- AXI Write Address Channel
        axi_awaddr  : in  std_logic_vector(31 downto 0);
        axi_awvalid : in  std_logic;
        axi_awready : out std_logic;
        
        -- AXI Write Data Channel
        axi_wdata   : in  std_logic_vector(31 downto 0);
        axi_wstrb   : in  std_logic_vector(3 downto 0);
        axi_wvalid  : in  std_logic;
        axi_wready  : out std_logic;
        
        -- AXI Write Response Channel
        axi_bresp   : out std_logic_vector(1 downto 0);
        axi_bvalid  : out std_logic;
        axi_bready  : in  std_logic;
        
        -- AXI Read Address Channel
        axi_araddr  : in  std_logic_vector(31 downto 0);
        axi_arvalid : in  std_logic;
        axi_arready : out std_logic;
        
        -- AXI Read Data Channel
        axi_rdata   : out std_logic_vector(31 downto 0);
        axi_rresp   : out std_logic_vector(1 downto 0);
        axi_rvalid  : out std_logic;
        axi_rready  : in  std_logic;
        
        -- Module Clock (for CDC)
        module_clk  : in  std_logic;
        
        -- Register Signals
        control_reg : out std_logic_vector(31 downto 0);  -- SPI control: bit0=start, bits[15:8]=clk_div
        control_reg_wr_strobe : out std_logic;
        status_reg : in  std_logic_vector(31 downto 0);  -- SPI status: bit0=busy, bit1=done, bit2=error
        status_reg_rd_strobe : out std_logic;
        tx_data_reg : out std_logic_vector(31 downto 0);  -- Transmit data buffer
        rx_data_reg : in  std_logic_vector(31 downto 0);  -- Receive data buffer
        config_reg : out std_logic_vector(31 downto 0);  -- SPI configuration
        irq_enable_reg : out std_logic_vector(31 downto 0);  -- Interrupt enable mask
        irq_status_reg : out std_logic_vector(31 downto 0);  -- Interrupt status
        irq_status_reg_rd_strobe : out std_logic;
        irq_status_reg_wr_strobe : out std_logic
    );
end entity spi_master_axion_reg;

-- Full architecture includes:
-- - AXI4-Lite state machine (IDLE, WR_WAIT_ADDR, WR_WAIT_DATA, WR_DO_WRITE, WR_RESP, RD_ADDR, RD_DATA)
-- - 2-stage CDC synchronizers for all registers
-- - Byte-level write strobe support (WSTRB)
-- - Address decoding and access control
-- - Read/write strobe generation
```

---

## YAML Example: LED Blinker

**Input File (`led_blinker.yaml`):**

```yaml
# LED Blinker Example - Beginner Level

module: led_blinker
base_addr: "0x0000"

registers:
  # Enable/disable LED blinking and set speed
  - name: control
    addr: "0x00"
    access: RW
    width: 32
    default: 0
    description: "LED control register"

  # Current LED state (read-only from software)
  - name: led_state
    addr: "0x04"
    access: RO
    width: 32
    description: "Current LED output state"

  # Blink period in milliseconds
  - name: period_ms
    addr: "0x08"
    access: RW
    width: 32
    default: 500
    description: "Blink period in milliseconds"

  # LED pattern for multi-LED designs
  - name: pattern
    addr: "0x0C"
    access: RW
    width: 32
    default: "0x55"
    description: "LED pattern (8-bit pattern for 8 LEDs)"
```

**Command:**

```bash
axion-hdl -s led_blinker.yaml -o output --all
```

**Terminal Output:**

```
YAML source file added: led_blinker.yaml

============================================================
Starting analysis of YAML files...
============================================================
Parsing YAML file: led_blinker.yaml
Found 1 modules from YAML files.

Analysis complete. Found 1 total modules.

================================================================================
Module: led_blinker
File: led_blinker.yaml
CDC: Disabled
Base Address: 0x0000
================================================================================

Signal Name               Type       Abs.Addr   Offset     Access   Strobes
------------------------- ---------- ---------- ---------- -------- ---------------
control                   [31:0]     0x00       0x00       RW       None
led_state                 [31:0]     0x04       0x04       RO       None
period_ms                 [31:0]     0x08       0x08       RW       None
pattern                   [31:0]     0x0C       0x0C       RW       None

Total Registers: 4

================================================================================

============================================================
Generating VHDL register modules...
============================================================
  Generated: led_blinker_axion_reg.vhd

============================================================
All files generated successfully!
Output directory: output
============================================================
```

**Generated VHDL Module (`led_blinker_axion_reg.vhd`):**

```vhdl
--------------------------------------------------------------------------------
-- File: led_blinker_axion_reg.vhd
-- Description: AXI Register Interface Module
-- Generated by Axion HDL
--
-- Module: led_blinker
-- Source: led_blinker.yaml
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity led_blinker_axion_reg is
    generic (
        BASE_ADDR : std_logic_vector(31 downto 0) := x"00000000"
    );
    port (
        -- AXI4-Lite Interface
        axi_aclk    : in  std_logic;
        axi_aresetn : in  std_logic;
        
        -- AXI Write Address Channel
        axi_awaddr  : in  std_logic_vector(31 downto 0);
        axi_awvalid : in  std_logic;
        axi_awready : out std_logic;
        
        -- AXI Write Data Channel
        axi_wdata   : in  std_logic_vector(31 downto 0);
        axi_wstrb   : in  std_logic_vector(3 downto 0);
        axi_wvalid  : in  std_logic;
        axi_wready  : out std_logic;
        
        -- AXI Write Response Channel
        axi_bresp   : out std_logic_vector(1 downto 0);
        axi_bvalid  : out std_logic;
        axi_bready  : in  std_logic;
        
        -- AXI Read Address Channel
        axi_araddr  : in  std_logic_vector(31 downto 0);
        axi_arvalid : in  std_logic;
        axi_arready : out std_logic;
        
        -- AXI Read Data Channel
        axi_rdata   : out std_logic_vector(31 downto 0);
        axi_rresp   : out std_logic_vector(1 downto 0);
        axi_rvalid  : out std_logic;
        axi_rready  : in  std_logic;
        
        -- Register Signals
        control : out std_logic_vector(31 downto 0);  -- LED control register
        led_state : in  std_logic_vector(31 downto 0);  -- Current LED output state
        period_ms : out std_logic_vector(31 downto 0);  -- Blink period in milliseconds
        pattern : out std_logic_vector(31 downto 0)  -- LED pattern (8-bit pattern for 8 LEDs)
    );
end entity led_blinker_axion_reg;

-- Features:
-- - Default values: period_ms = 0x000001F4 (500), pattern = 0x00000055 (0x55)
-- - No CDC (single clock domain)
-- - Full AXI4-Lite compliance
```

---

## XML Example: PWM Controller

**Input File (`pwm_controller.xml`):**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!--
  PWM Controller Example - Intermediate Level
  Demonstrates CDC with 3 stages, read/write strobes
-->
<register_map module="pwm_controller" base_addr="0x0000">
    <!-- Enable CDC for safe cross-clock-domain access -->
    <config cdc_en="true" cdc_stage="3"/>
    
    <!-- Global control register -->
    <register name="global_enable" addr="0x00" access="RW" width="32" 
              w_strobe="true" description="Global PWM enable"/>
    
    <!-- Channel 0 -->
    <register name="ch0_duty" addr="0x04" access="RW" width="32" 
              default="128" description="Channel 0 duty cycle (0-255)"/>
    <register name="ch0_period" addr="0x08" access="RW" width="32" 
              default="255" description="Channel 0 period"/>
    
    <!-- Channel 1 -->
    <register name="ch1_duty" addr="0x0C" access="RW" width="32" 
              default="128" description="Channel 1 duty cycle"/>
    <register name="ch1_period" addr="0x10" access="RW" width="32" 
              default="255" description="Channel 1 period"/>
    
    <!-- Status register with read strobe -->
    <register name="status" addr="0x20" access="RO" width="32" 
              r_strobe="true" description="PWM status (clears on read)"/>
    
    <!-- Interrupt control -->
    <register name="irq_enable" addr="0x24" access="RW" width="32" 
              description="Interrupt enable mask"/>
    <register name="irq_status" addr="0x28" access="RW" width="32" 
              r_strobe="true" w_strobe="true" 
              description="Interrupt status (write 1 to clear)"/>
</register_map>
```

**Command:**

```bash
axion-hdl -s pwm_controller.xml -o output --all
```

**Terminal Output:**

```
XML source file added: pwm_controller.xml

============================================================
Starting analysis of XML files...
============================================================
Parsing XML file: pwm_controller.xml
Found 1 modules from XML files.

Analysis complete. Found 1 total modules.

================================================================================
Module: pwm_controller
File: pwm_controller.xml
CDC: Enabled (Stages: 3)
Base Address: 0x0000
================================================================================

Signal Name               Type       Abs.Addr   Offset     Access   Strobes
------------------------- ---------- ---------- ---------- -------- ---------------
global_enable             [31:0]     0x00       0x00       RW       WR
ch0_duty                  [31:0]     0x04       0x04       RW       None
ch0_period                [31:0]     0x08       0x08       RW       None
ch1_duty                  [31:0]     0x0C       0x0C       RW       None
ch1_period                [31:0]     0x10       0x10       RW       None
status                    [31:0]     0x20       0x20       RO       RD
irq_enable                [31:0]     0x24       0x24       RW       None
irq_status                [31:0]     0x28       0x28       RW       RD, WR

Total Registers: 8

================================================================================

============================================================
All files generated successfully!
Output directory: output
============================================================
```

**Generated VHDL Module (`pwm_controller_axion_reg.vhd`):**

```vhdl
--------------------------------------------------------------------------------
-- File: pwm_controller_axion_reg.vhd
-- Description: AXI Register Interface Module
-- Generated by Axion HDL
--
-- Module: pwm_controller
-- Source: pwm_controller.xml
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity pwm_controller_axion_reg is
    generic (
        BASE_ADDR : std_logic_vector(31 downto 0) := x"00000000"
    );
    port (
        -- AXI4-Lite Interface
        axi_aclk    : in  std_logic;
        axi_aresetn : in  std_logic;
        
        -- AXI Write Address Channel
        axi_awaddr  : in  std_logic_vector(31 downto 0);
        axi_awvalid : in  std_logic;
        axi_awready : out std_logic;
        
        -- AXI Write Data Channel
        axi_wdata   : in  std_logic_vector(31 downto 0);
        axi_wstrb   : in  std_logic_vector(3 downto 0);
        axi_wvalid  : in  std_logic;
        axi_wready  : out std_logic;
        
        -- AXI Write Response Channel
        axi_bresp   : out std_logic_vector(1 downto 0);
        axi_bvalid  : out std_logic;
        axi_bready  : in  std_logic;
        
        -- AXI Read Address Channel
        axi_araddr  : in  std_logic_vector(31 downto 0);
        axi_arvalid : in  std_logic;
        axi_arready : out std_logic;
        
        -- AXI Read Data Channel
        axi_rdata   : out std_logic_vector(31 downto 0);
        axi_rresp   : out std_logic_vector(1 downto 0);
        axi_rvalid  : out std_logic;
        axi_rready  : in  std_logic;
        
        -- Module Clock (for CDC)
        module_clk  : in  std_logic;
        
        -- Register Signals
        global_enable : out std_logic_vector(31 downto 0);  -- Global PWM enable
        global_enable_wr_strobe : out std_logic;
        ch0_duty : out std_logic_vector(31 downto 0);  -- Channel 0 duty cycle (0-255)
        ch0_period : out std_logic_vector(31 downto 0);  -- Channel 0 period
        ch1_duty : out std_logic_vector(31 downto 0);  -- Channel 1 duty cycle
        ch1_period : out std_logic_vector(31 downto 0);  -- Channel 1 period
        status : in  std_logic_vector(31 downto 0);  -- PWM status (clears on read)
        status_rd_strobe : out std_logic;
        irq_enable : out std_logic_vector(31 downto 0);  -- Interrupt enable mask
        irq_status : out std_logic_vector(31 downto 0);  -- Interrupt status (write 1 to clear)
        irq_status_rd_strobe : out std_logic;
        irq_status_wr_strobe : out std_logic
    );
end entity pwm_controller_axion_reg;

-- Features:
-- - 3-stage CDC synchronizers (module_clk <-> axi_aclk)
-- - Default values: ch0_duty = 128, ch0_period = 255, ch1_duty = 128, ch1_period = 255
-- - Read/write strobes for status and irq_status
```

---

## JSON Example: GPIO Controller

**Input File (`gpio_controller.json`):**

```json
{
    "module": "gpio_controller",
    "base_addr": "0x1000",
    "registers": [
        {
            "name": "direction",
            "addr": "0x00",
            "access": "RW",
            "width": 32,
            "default": 0,
            "description": "GPIO direction (0=input, 1=output)"
        },
        {
            "name": "output_data",
            "addr": "0x04",
            "access": "RW",
            "width": 32,
            "default": 0,
            "description": "GPIO output values"
        },
        {
            "name": "input_data",
            "addr": "0x08",
            "access": "RO",
            "width": 32,
            "description": "GPIO input values (directly from pins)"
        },
        {
            "name": "irq_enable",
            "addr": "0x0C",
            "access": "RW",
            "width": 32,
            "default": 0,
            "description": "Interrupt enable per pin"
        },
        {
            "name": "irq_status",
            "addr": "0x10",
            "access": "RW",
            "width": 32,
            "w_strobe": true,
            "description": "Interrupt status (write 1 to clear)"
        }
    ]
}
```

**Command:**

```bash
axion-hdl -s gpio_controller.json -o output --all
```

**Terminal Output:**

```
JSON source file added: gpio_controller.json

============================================================
Starting analysis of JSON files...
============================================================
Parsing JSON file: gpio_controller.json
Found 1 modules from JSON files.

Analysis complete. Found 1 total modules.

================================================================================
Module: gpio_controller
File: gpio_controller.json
CDC: Disabled
Base Address: 0x1000
================================================================================

Signal Name               Type       Abs.Addr   Offset     Access   Strobes
------------------------- ---------- ---------- ---------- -------- ---------------
direction                 [31:0]     0x1000     0x00       RW       None
output_data               [31:0]     0x1004     0x04       RW       None
input_data                [31:0]     0x1008     0x08       RO       None
irq_enable                [31:0]     0x100C     0x0C       RW       None
irq_status                [31:0]     0x1010     0x10       RW       WR

Total Registers: 5

================================================================================

============================================================
All files generated successfully!
Output directory: output
============================================================
```

**Generated VHDL Module (`gpio_controller_axion_reg.vhd`):**

```vhdl
--------------------------------------------------------------------------------
-- File: gpio_controller_axion_reg.vhd
-- Description: AXI Register Interface Module
-- Generated by Axion HDL
--
-- Module: gpio_controller
-- Source: gpio_controller.json
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity gpio_controller_axion_reg is
    generic (
        BASE_ADDR : std_logic_vector(31 downto 0) := x"00001000"
    );
    port (
        -- AXI4-Lite Interface
        axi_aclk    : in  std_logic;
        axi_aresetn : in  std_logic;
        
        -- AXI Write Address Channel
        axi_awaddr  : in  std_logic_vector(31 downto 0);
        axi_awvalid : in  std_logic;
        axi_awready : out std_logic;
        
        -- AXI Write Data Channel
        axi_wdata   : in  std_logic_vector(31 downto 0);
        axi_wstrb   : in  std_logic_vector(3 downto 0);
        axi_wvalid  : in  std_logic;
        axi_wready  : out std_logic;
        
        -- AXI Write Response Channel
        axi_bresp   : out std_logic_vector(1 downto 0);
        axi_bvalid  : out std_logic;
        axi_bready  : in  std_logic;
        
        -- AXI Read Address Channel
        axi_araddr  : in  std_logic_vector(31 downto 0);
        axi_arvalid : in  std_logic;
        axi_arready : out std_logic;
        
        -- AXI Read Data Channel
        axi_rdata   : out std_logic_vector(31 downto 0);
        axi_rresp   : out std_logic_vector(1 downto 0);
        axi_rvalid  : out std_logic;
        axi_rready  : in  std_logic;
        
        -- Register Signals
        direction : out std_logic_vector(31 downto 0);  -- GPIO direction (0=input, 1=output)
        output_data : out std_logic_vector(31 downto 0);  -- GPIO output values
        input_data : in  std_logic_vector(31 downto 0);  -- GPIO input values (directly from pins)
        irq_enable : out std_logic_vector(31 downto 0);  -- Interrupt enable per pin
        irq_status : out std_logic_vector(31 downto 0);  -- Interrupt status (write 1 to clear)
        irq_status_wr_strobe : out std_logic
    );
end entity gpio_controller_axion_reg;

-- Features:
-- - Base address set to 0x1000 (absolute addresses: 0x1000-0x1010)
-- - No CDC (single clock domain)
-- - Write strobe for irq_status (write-1-to-clear pattern)
```

---

## TOML Example: SPI Master

**Input File (`spi_master.toml`):**

```toml
# SPI Master Controller Register Definitions
# TOML format example for Axion HDL

module = "spi_master"
base_addr = "0x0000"

[config]
cdc_en = true
cdc_stage = 2

[[registers]]
name = "control"
addr = "0x00"
access = "RW"
width = 32
w_strobe = true
description = "SPI control register"

[[registers]]
name = "status"
addr = "0x04"
access = "RO"
width = 32
r_strobe = true
description = "SPI status register"

[[registers]]
name = "tx_data"
addr = "0x08"
access = "WO"
width = 32
description = "Transmit data register"

[[registers]]
name = "rx_data"
addr = "0x0C"
access = "RO"
width = 32
description = "Receive data register"

[[registers]]
name = "clock_div"
addr = "0x10"
access = "RW"
width = 32
default = "0x00000008"
description = "Clock divider (SPI clock = system clock / (2 * clock_div))"

[[registers]]
name = "chip_select"
addr = "0x14"
access = "RW"
width = 32
description = "Chip select control (one-hot encoding)"
```

**Command:**

```bash
axion-hdl -s spi_master.toml -o output --all
```

**Terminal Output:**

```
Axion-HDL v1.0.1
Automated AXI4-Lite Register Interface Generator
Developed by bugratufan
--------------------------------------------------
TOML source file added: spi_master.toml

============================================================
Starting analysis of TOML files...
============================================================
Found 1 modules from TOML files.

Analysis complete. Found 1 total modules.

==============================================================================================================
Module: spi_master
File: spi_master.toml
CDC: Enabled (Stages: 2)
Base Address: 0x0000
==============================================================================================================

Signal Name               Type     Abs.Addr   Offset     Access   Strobes         Ports Generated
------------------------- -------- ---------- ---------- -------- --------------- ----------------------------------------
control                   std_logic_vector(31 downto 0) 0x00       0x00       RW       WR              control, control_wr_strobe
status                    std_logic_vector(31 downto 0) 0x04       0x04       RO       RD              status, status_rd_strobe
tx_data                   std_logic_vector(31 downto 0) 0x08       0x08       WO       None            tx_data
rx_data                   std_logic_vector(31 downto 0) 0x0C       0x0C       RO       None            rx_data
clock_div                 std_logic_vector(31 downto 0) 0x10       0x10       RW       None            clock_div
chip_select               std_logic_vector(31 downto 0) 0x14       0x14       RW       None            chip_select

Total Registers: 6

==============================================================================================================
Summary: 1 module(s) analyzed
Total Registers: 6
==============================================================================================================


============================================================
Generating VHDL register modules...
============================================================
  Generated: spi_master_axion_reg.vhd

VHDL files generated in: output

============================================================
Generating documentation (HTML)...
============================================================
  Generated: index.html

Documentation generated in: output

============================================================
Generating XML register map...
============================================================
  Generated: spi_master_regs.xml

XML files generated in: output

============================================================
Generating YAML register map...
============================================================
  Generated: spi_master_regs.yaml

YAML files generated in: output

============================================================
Generating JSON register map...
============================================================
  Generated: spi_master_regs.json

JSON files generated in: output

============================================================
Generating C header files...
============================================================
  Generated: spi_master_regs.h

C header files generated in: output

============================================================
All files generated successfully!
Output directory: output
============================================================
```

**Generated Files:**

```bash
$ ls -lh output/
total 88K
drwxrwxr-x 2 bugra bugra   80 Jan 31 20:57 html
-rw-rw-r-- 1 bugra bugra  19K Jan 31 20:57 index.html
-rw-rw-r-- 1 bugra bugra  24K Jan 31 20:57 register_map.html
-rw-rw-r-- 1 bugra bugra  21K Jan 31 20:57 spi_master_axion_reg.vhd
-rw-rw-r-- 1 bugra bugra 3.8K Jan 31 20:57 spi_master_regs.h
-rw-rw-r-- 1 bugra bugra 1.2K Jan 31 20:57 spi_master_regs.json
-rw-rw-r-- 1 bugra bugra 4.8K Jan 31 20:57 spi_master_regs.xml
-rw-rw-r-- 1 bugra bugra  754 Jan 31 20:57 spi_master_regs.yaml
```

**Generated C Header Excerpt (`spi_master_regs.h`):**

```c
#ifndef SPI_MASTER_REGS_H
#define SPI_MASTER_REGS_H

#include <stdint.h>

/* Module Base Address */
#define SPI_MASTER_BASE_ADDR    0x00000000

/* Register Address Offsets (relative to base) */
#define SPI_MASTER_CONTROL_OFFSET    0x00  /* SPI control register */
#define SPI_MASTER_STATUS_OFFSET     0x04  /* SPI status register */
#define SPI_MASTER_TX_DATA_OFFSET    0x08  /* Transmit data register */
#define SPI_MASTER_RX_DATA_OFFSET    0x0C  /* Receive data register */
#define SPI_MASTER_CLOCK_DIV_OFFSET  0x10  /* Clock divider */
#define SPI_MASTER_CHIP_SELECT_OFFSET 0x14  /* Chip select control */

/* Register Structure */
typedef struct {
    volatile uint32_t control;      /* 0x00 - RW - SPI control register */
    volatile uint32_t status;       /* 0x04 - RO - SPI status register */
    volatile uint32_t tx_data;      /* 0x08 - WO - Transmit data register */
    volatile uint32_t rx_data;      /* 0x0C - RO - Receive data register */
    volatile uint32_t clock_div;    /* 0x10 - RW - Clock divider */
    volatile uint32_t chip_select;  /* 0x14 - RW - Chip select control */
} spi_master_regs_t;

/* Access register block as structure */
#define SPI_MASTER_REGS    ((volatile spi_master_regs_t*)(SPI_MASTER_BASE_ADDR))

#endif /* SPI_MASTER_REGS_H */
```

**Generated VHDL Entity:**

```vhdl
entity spi_master_axion_reg is
    generic (
        BASE_ADDR : std_logic_vector(31 downto 0) := x"00000000"
    );
    port (
        -- AXI4-Lite Interface
        axi_aclk    : in  std_logic;
        axi_aresetn : in  std_logic;

        -- AXI Write/Read Channels...

        -- Module Clock (for CDC)
        module_clk  : in  std_logic;

        -- Register Signals
        control : out std_logic_vector(31 downto 0);
        control_wr_strobe : out std_logic;
        status : in  std_logic_vector(31 downto 0);
        status_rd_strobe : out std_logic;
        tx_data : out std_logic_vector(31 downto 0);
        rx_data : in  std_logic_vector(31 downto 0);
        clock_div : out std_logic_vector(31 downto 0);
        chip_select : out std_logic_vector(31 downto 0)
    );
end entity spi_master_axion_reg;
```

**Key Features Demonstrated:**

- **TOML's clean syntax** - No braces, minimal punctuation
- **CDC synchronizers** with 2 stages for clock domain crossing
- **Register strobes** for control/status (control_wr_strobe, status_rd_strobe)
- **Default values** (clock_div = 0x00000008)
- **Mixed access modes** (RO, WO, RW)
- **Comprehensive output** - VHDL (21KB), C header (3.8KB), docs, XML/YAML/JSON
- **Production-ready** code with full AXI4-Lite compliance

---

## Generated Output Files Summary

Each example generates the following files:

| File | Description |
|------|-------------|
| `*_axion_reg.vhd` | AXI4-Lite slave VHDL module |
| `*_regs.h` | C header with register macros |
| `*_regs.xml` | IP-XACT style XML register map |
| `*_regs.yaml` | YAML register map (re-importable) |
| `*_regs.json` | JSON register map (re-importable) |
| `register_map.md` | Markdown documentation |
