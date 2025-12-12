# Advanced Features

## Clock Domain Crossing (CDC)

Enable CDC synchronizers when your AXI bus and register logic use different clocks.

### VHDL
```vhdl
-- @axion_def BASE_ADDR=0x1000 CDC_EN CDC_STAGE=3
```

### YAML
```yaml
module: my_module
base_addr: "0x1000"
config:
  cdc_en: true
  cdc_stage: 3
```

### XML
```xml
<register_map module="my_module" base_addr="0x1000">
    <config cdc_en="true" cdc_stage="3"/>
</register_map>
```

### JSON
```json
{
  "module": "my_module",
  "base_addr": "0x1000",
  "config": {
    "cdc_en": true,
    "cdc_stage": 3
  }
}
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `CDC_EN` / `cdc_en` | Enable CDC synchronizers | `false` |
| `CDC_STAGE` / `cdc_stage` | Number of synchronizer stages | `2` |

---

## Strobe Signals

Strobe signals provide single-cycle pulses on read/write operations.

### VHDL
```vhdl
signal irq_status : std_logic_vector(31 downto 0); -- @axion RW R_STROBE W_STROBE DESC="Interrupt status"
```

### YAML
```yaml
- name: irq_status
  access: RW
  r_strobe: true
  w_strobe: true
  description: "Interrupt status"
```

### XML
```xml
<register name="irq_status" access="RW" r_strobe="true" w_strobe="true" description="Interrupt status"/>
```

### JSON
```json
{
  "name": "irq_status",
  "access": "RW",
  "r_strobe": true,
  "w_strobe": true,
  "description": "Interrupt status"
}
```

**Use Cases:**
- `R_STROBE`: Clear-on-read status registers
- `W_STROBE`: Trigger actions on write (start transfer, clear flags)

---

## Subregisters (Packed Fields)

Pack multiple fields into a single 32-bit register address.

### VHDL

In VHDL, subregisters are defined using `reg_name` to group fields:

```vhdl
-- Control register at address 0x00 with packed fields
signal enable : std_logic;                        -- @axion RW REG_NAME=control BIT_OFFSET=0 DESC="Enable bit"
signal mode   : std_logic_vector(1 downto 0);     -- @axion RW REG_NAME=control BIT_OFFSET=4 DESC="Mode select"
signal speed  : std_logic_vector(7 downto 0);     -- @axion RW REG_NAME=control BIT_OFFSET=8 DESC="Speed value"
```

### YAML
```yaml
- name: control
  addr: "0x00"
  fields:
    - name: enable
      bit_offset: 0
      width: 1
      access: RW
      description: "Enable bit"
    - name: mode
      bit_offset: 4
      width: 2
      access: RW
      description: "Mode select"
    - name: speed
      bit_offset: 8
      width: 8
      access: RW
      description: "Speed value"
```

### XML
```xml
<!-- All fields share address 0x00 via reg_name -->
<register name="enable" reg_name="control" addr="0x00" width="1" access="RW" bit_offset="0" description="Enable bit"/>
<register name="mode" reg_name="control" addr="0x00" width="2" access="RW" bit_offset="4" description="Mode select"/>
<register name="speed" reg_name="control" addr="0x00" width="8" access="RW" bit_offset="8" description="Speed value"/>
```

### JSON
```json
{
  "name": "control",
  "addr": "0x00",
  "fields": [
    {"name": "enable", "bit_offset": 0, "width": 1, "access": "RW", "description": "Enable bit"},
    {"name": "mode", "bit_offset": 4, "width": 2, "access": "RW", "description": "Mode select"},
    {"name": "speed", "bit_offset": 8, "width": 8, "access": "RW", "description": "Speed value"}
  ]
}
```

This creates individual signals for each field while sharing one address.

---

## Wide Signals

Signals wider than 32 bits automatically span multiple addresses.

### VHDL
```vhdl
signal counter : std_logic_vector(63 downto 0); -- @axion RO DESC="64-bit counter"
```

### YAML
```yaml
- name: counter
  access: RO
  width: 64
  description: "64-bit counter"
```

### XML
```xml
<register name="counter" access="RO" width="64" description="64-bit counter"/>
```

### JSON
```json
{
  "name": "counter",
  "access": "RO",
  "width": 64,
  "description": "64-bit counter"
}
```

This creates two consecutive 32-bit registers:
- `counter[31:0]` at offset 0x00
- `counter[63:32]` at offset 0x04

---

## Default Values

Set reset values for registers.

### VHDL
```vhdl
signal config : std_logic_vector(31 downto 0); -- @axion RW DEFAULT=0xCAFEBABE DESC="Configuration"
```

### YAML
```yaml
- name: config
  access: RW
  width: 32
  default: "0xCAFEBABE"
  description: "Configuration"
```

### XML
```xml
<register name="config" access="RW" width="32" default="0xCAFEBABE" description="Configuration"/>
```

### JSON
```json
{
  "name": "config",
  "access": "RW",
  "width": 32,
  "default": "0xCAFEBABE",
  "description": "Configuration"
}
```

---

## Manual Address Assignment

Override automatic address allocation.

### VHDL
```vhdl
signal debug_reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x100 DESC="Debug register"
```

### YAML
```yaml
- name: debug_reg
  addr: "0x100"
  access: RW
  description: "Debug register"
```

### XML
```xml
<register name="debug_reg" addr="0x100" access="RW" description="Debug register"/>
```

### JSON
```json
{
  "name": "debug_reg",
  "addr": "0x100",
  "access": "RW",
  "description": "Debug register"
}
```

---

## Access Types

Three access modes are supported:

### VHDL
```vhdl
signal status  : std_logic_vector(31 downto 0); -- @axion RO DESC="Read-only status"
signal command : std_logic_vector(31 downto 0); -- @axion WO DESC="Write-only command"
signal config  : std_logic_vector(31 downto 0); -- @axion RW DESC="Read-write config"
```

### YAML
```yaml
registers:
  - name: status
    access: RO
    description: "Read-only status"
  - name: command
    access: WO
    description: "Write-only command"
  - name: config
    access: RW
    description: "Read-write config"
```

### XML
```xml
<register name="status" access="RO" description="Read-only status"/>
<register name="command" access="WO" description="Write-only command"/>
<register name="config" access="RW" description="Read-write config"/>
```

### JSON
```json
{
  "registers": [
    {"name": "status", "access": "RO", "description": "Read-only status"},
    {"name": "command", "access": "WO", "description": "Write-only command"},
    {"name": "config", "access": "RW", "description": "Read-write config"}
  ]
}
```

| Access | Software | Hardware |
|--------|----------|----------|
| `RO` | Read | Write |
| `WO` | Write | Read |
| `RW` | Read/Write | Read/Write |
