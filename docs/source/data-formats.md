# Data Formats

Axion-HDL supports multiple input formats for defining register interfaces. This section covers all available attributes, keywords, and their usage across all supported formats.

## Format Overview

| Format | Extension | Use Case |
|--------|-----------|----------|
| **VHDL** | `.vhd`, `.vhdl` | Embedded in existing RTL code |
| **SystemVerilog** | `.sv`, `.svh` | Embedded in existing RTL code |
| **YAML** | `.yaml`, `.yml` | Human-readable, version control friendly |
| **XML** | `.xml` | IP-XACT compatible, tool integration |
| **JSON** | `.json` | Automation and scripting |
| **TOML** | `.toml` | Clean syntax, Python ecosystem standard |

---

## Module-Level Attributes

These attributes define module-wide settings like base address and CDC configuration.

### VHDL (`@axion_def`)

Module-level configuration is defined with `@axion_def` comment anywhere in the file:

```vhdl
-- @axion_def BASE_ADDR=0x1000 CDC_EN CDC_STAGE=3
```

### SystemVerilog (`@axion_def`)

Use `//` comments for module configuration:

```systemverilog
// @axion_def BASE_ADDR=0x1000 CDC_EN CDC_STAGE=3
```

### YAML/TOML/XML/JSON

| Attribute | YAML | TOML | XML | JSON | Description | Default |
|-----------|------|------|-----|------|-------------|---------|
| Module Name | `module:` | `module =` | `module=""` | `"module":` | Module/entity name | Required |
| Base Address | `base_addr:` | `base_addr =` | `base_addr=""` | `"base_addr":` | Starting address (hex string) | `0x0000` |
| CDC Enable | `config.cdc_en:` | `[config]`<br/>`cdc_en =` | `<config cdc_en=""/>` | `"config":{"cdc_en":}` | Enable clock domain crossing | `false` |
| CDC Stages | `config.cdc_stage:` | `[config]`<br/>`cdc_stage =` | `<config cdc_stage=""/>` | `"config":{"cdc_stage":}` | Synchronizer stages (2-5) | `2` |

### VHDL Module Attributes Table

| Attribute | Syntax | Description | Default |
|-----------|--------|-------------|---------|
| `BASE_ADDR` | `BASE_ADDR=0xNNNN` | Module base address | `0x0000` |
| `CDC_EN` | `CDC_EN` or `CDC_EN=true` | Enable CDC synchronizers | `false` |
| `CDC_STAGE` | `CDC_STAGE=N` | Number of sync stages (2-5) | `2` |

---

## Register-Level Attributes

### Access Modes

| Mode | Software | Hardware | Description |
|------|----------|----------|-------------|
| `RO` | Read | Write | Hardware writes, software reads |
| `WO` | Write | Read | Software writes, hardware reads |
| `RW` | Read/Write | Read/Write | Both can read and write |

### Complete Attribute Reference

#### VHDL Register Attributes (`@axion`)

```vhdl
signal reg_name : std_logic_vector(31 downto 0); -- @axion ACCESS [OPTIONS]
```

Attributes are optional — a bare `-- @axion` annotation is valid and uses all defaults:

```vhdl
signal my_reg : std_logic_vector(31 downto 0); -- @axion
-- Defaults to: RW access, auto-assigned address, no strobes
```

#### SystemVerilog Register Attributes (`@axion`)

```systemverilog
logic [31:0] reg_name; // @axion ACCESS [OPTIONS]
```

Attributes are optional — a bare `// @axion` annotation is valid and uses all defaults:

```systemverilog
logic [31:0] my_reg; // @axion
// Defaults to: RW access, auto-assigned address, no strobes
```

| Attribute | Syntax | Description | Default |
|-----------|--------|-------------|---------|
| Access Mode | `RO`, `WO`, `RW` | Register access type | `RW` |
| Address | `ADDR=0xNN` | Manual address assignment | Auto-assigned |
| Description | `DESC="text"` | Register description | Empty |
| Read Strobe | `R_STROBE` | Generate read strobe signal | `false` |
| Write Strobe | `W_STROBE` | Generate write strobe signal | `false` |
| Default Value | `DEFAULT=0xNN` | Reset value | `0x0` |
| Register Name | `REG_NAME=name` | Group into packed register | Signal name |
| Bit Offset | `BIT_OFFSET=N` | Bit position in packed reg | `0` |

#### YAML Register Attributes

```yaml
registers:
  - name: register_name
    addr: "0x00"           # Optional: manual address
    access: RW             # Required: RO, WO, RW
    width: 32              # Optional: bit width (default: 32)
    default: "0x00"        # Optional: reset value
    description: "text"    # Optional: documentation
    r_strobe: true         # Optional: read strobe
    w_strobe: true         # Optional: write strobe
    fields:                # Optional: subregister fields
      - name: field_name
        bit_offset: 0
        width: 8
        access: RW
```

| Attribute | Type | Description | Default |
|-----------|------|-------------|---------|
| `name` | string | Register/signal name | Required |
| `addr` | string | Address in hex (e.g., "0x04") | Auto-assigned |
| `access` | string | `RO`, `WO`, or `RW` | Required |
| `width` | integer | Bit width (1-1024) | `32` |
| `default` | string/int | Reset value | `0` |
| `description` | string | Documentation text | Empty |
| `r_strobe` | boolean | Generate read strobe | `false` |
| `w_strobe` | boolean | Generate write strobe | `false` |
| `fields` | array | Subregister field definitions | None |

#### XML Register Attributes

```xml
<register name="reg_name" addr="0x00" access="RW" width="32" 
          default="0x00" r_strobe="true" w_strobe="true" 
          description="Description text"/>
```

| Attribute | Type | Description | Default |
|-----------|------|-------------|---------|
| `name` | string | Register name | Required |
| `addr` | string | Address in hex | Auto-assigned |
| `access` | string | `RO`, `WO`, or `RW` | Required |
| `width` | integer | Bit width | `32` |
| `default` | string | Reset value | `0` |
| `description` | string | Documentation | Empty |
| `r_strobe` | string | `"true"` or `"false"` | `"false"` |
| `w_strobe` | string | `"true"` or `"false"` | `"false"` |
| `reg_name` | string | Packed register name | None |
| `bit_offset` | integer | Bit position for packed | `0` |

#### JSON Register Attributes

```json
{
  "name": "reg_name",
  "addr": "0x00",
  "access": "RW",
  "width": 32,
  "default": "0x00",
  "description": "Description text",
  "r_strobe": true,
  "w_strobe": true
}
```

| Attribute | Type | Description | Default |
|-----------|------|-------------|---------|
| `name` | string | Register name | Required |
| `addr` | string | Address in hex | Auto-assigned |
| `access` | string | `RO`, `WO`, or `RW` | Required |
| `width` | integer | Bit width | `32` |
| `default` | string/int | Reset value | `0` |
| `description` | string | Documentation | Empty |
| `r_strobe` | boolean | Generate read strobe | `false` |
| `w_strobe` | boolean | Generate write strobe | `false` |
| `fields` | array | Subregister fields | None |

#### TOML Register Attributes

```toml
[[registers]]
name = "register_name"
addr = "0x00"           # Optional: manual address
access = "RW"           # Required: RO, WO, RW
width = 32              # Optional: bit width (default: 32)
default = "0x00"        # Optional: reset value
description = "text"    # Optional: documentation
r_strobe = true         # Optional: read strobe
w_strobe = true         # Optional: write strobe
reg_name = "packed"     # Optional: packed register name
bit_offset = 0          # Optional: bit position in packed reg
```

| Attribute | Type | Description | Default |
|-----------|------|-------------|---------|
| `name` | string | Register/signal name | Required |
| `addr` | string | Address in hex (e.g., "0x04") | Auto-assigned |
| `access` | string | `"RO"`, `"WO"`, or `"RW"` | Required |
| `width` | integer | Bit width (1-1024) | `32` |
| `default` | string/int | Reset value | `0` |
| `description` | string | Documentation text | Empty |
| `r_strobe` | boolean | Generate read strobe | `false` |
| `w_strobe` | boolean | Generate write strobe | `false` |
| `reg_name` | string | Packed register name | None |
| `bit_offset` | integer | Bit position for packed | `0` |

---

## Advanced Features

### Clock Domain Crossing (CDC)

Enable CDC synchronizers when your AXI bus and register logic use different clocks.

**VHDL:**
```vhdl
-- @axion_def BASE_ADDR=0x1000 CDC_EN CDC_STAGE=3
```

**YAML:**
```yaml
module: my_module
base_addr: "0x1000"
config:
  cdc_en: true
  cdc_stage: 3
```

**XML:**
```xml
<register_map module="my_module" base_addr="0x1000">
    <config cdc_en="true" cdc_stage="3"/>
</register_map>
```

**JSON:**
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

**TOML:**
```toml
module = "my_module"
base_addr = "0x1000"

[config]
cdc_en = true
cdc_stage = 3
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `CDC_EN` / `cdc_en` | Enable CDC synchronizers | `false` |
| `CDC_STAGE` / `cdc_stage` | Number of synchronizer stages | `2` |

---

### Strobe Signals

Strobe signals provide single-cycle pulses on read/write operations.

**VHDL:**
```vhdl
signal irq_status : std_logic_vector(31 downto 0); -- @axion RW R_STROBE W_STROBE DESC="Interrupt status"
```

**YAML:**
```yaml
- name: irq_status
  access: RW
  r_strobe: true
  w_strobe: true
  description: "Interrupt status"
```

**XML:**
```xml
<register name="irq_status" access="RW" r_strobe="true" w_strobe="true" description="Interrupt status"/>
```

**JSON:**
```json
{
  "name": "irq_status",
  "access": "RW",
  "r_strobe": true,
  "w_strobe": true,
  "description": "Interrupt status"
}
```

**TOML:**
```toml
[[registers]]
name = "irq_status"
access = "RW"
r_strobe = true
w_strobe = true
description = "Interrupt status"
```

**Use Cases:**
- `R_STROBE`: Clear-on-read status registers
- `W_STROBE`: Trigger actions on write (start transfer, clear flags)

---

### Subregisters (Packed Fields)

Pack multiple fields into a single 32-bit register address.

**VHDL:**
```vhdl
-- Control register at address 0x00 with packed fields
signal enable : std_logic;                        -- @axion RW REG_NAME=control BIT_OFFSET=0 DESC="Enable bit"
signal mode   : std_logic_vector(1 downto 0);     -- @axion RW REG_NAME=control BIT_OFFSET=4 DESC="Mode select"
signal speed  : std_logic_vector(7 downto 0);     -- @axion RW REG_NAME=control BIT_OFFSET=8 DESC="Speed value"
```

**YAML:**
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

**XML:**
```xml
<register name="enable" reg_name="control" addr="0x00" width="1" access="RW" bit_offset="0" description="Enable bit"/>
<register name="mode" reg_name="control" addr="0x00" width="2" access="RW" bit_offset="4" description="Mode select"/>
<register name="speed" reg_name="control" addr="0x00" width="8" access="RW" bit_offset="8" description="Speed value"/>
```

**JSON:**
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

**TOML:**
```toml
[[registers]]
name = "enable"
reg_name = "control"
addr = "0x00"
width = 1
access = "RW"
bit_offset = 0
description = "Enable bit"

[[registers]]
name = "mode"
reg_name = "control"
addr = "0x00"
width = 2
access = "RW"
bit_offset = 4
description = "Mode select"

[[registers]]
name = "speed"
reg_name = "control"
addr = "0x00"
width = 8
access = "RW"
bit_offset = 8
description = "Speed value"
```

This creates individual signals for each field while sharing one address.

### Advanced Subregister Features

#### Auto-Packing
If `BIT_OFFSET` is not specified, Axion-HDL automatically packs fields sequentially.

```vhdl
signal field_a : std_logic_vector(7 downto 0);  -- @axion RW REG_NAME=ctrl
signal field_b : std_logic_vector(7 downto 0);  -- @axion RW REG_NAME=ctrl
-- field_a becomes bits [7:0]
-- field_b becomes bits [15:8]
```

#### Default Value Aggregation
Individual field default values are combined into the 32-bit register reset value.

```vhdl
signal enable : std_logic; -- @axion RW REG_NAME=cfg DEFAULT=1
signal mode   : std_logic; -- @axion RW REG_NAME=cfg BIT_OFFSET=1 DEFAULT=1
-- Register reset value = 0x00000003
```

#### Strobe Aggregation
If *any* field in a packed register has `R_STROBE` or `W_STROBE` enabled, the entire 32-bit register will be generated with that strobe signal.

#### Mixed Access Modes
A packed register can contain fields with different access modes (e.g., one `RO` field and one `RW` field). In this case, the parent register is treated as `RW` to allow writing to the writable fields, while strict read-only behavior is enforced for `RO` fields at the logic level.

#### Overlap Handling
Overlapping bit ranges trigger a validation warning but are strictly allowed. This can be useful for aliasing fields, but ensure you understand the implications for your specific design.


---

### Wide Signals (>32 bits)

Signals wider than 32 bits automatically span multiple addresses.

**VHDL:**
```vhdl
signal counter : std_logic_vector(63 downto 0); -- @axion RO DESC="64-bit counter"
```

**YAML:**
```yaml
- name: counter
  access: RO
  width: 64
  description: "64-bit counter"
```

**XML:**
```xml
<register name="counter" access="RO" width="64" description="64-bit counter"/>
```

**JSON:**
```json
{
  "name": "counter",
  "access": "RO",
  "width": 64,
  "description": "64-bit counter"
}
```

**TOML:**
```toml
[[registers]]
name = "counter"
access = "RO"
width = 64
description = "64-bit counter"
```

This creates two consecutive 32-bit registers:
- `counter[31:0]` at offset 0x00
- `counter[63:32]` at offset 0x04

---

### Default Values

Set reset values for registers.

**VHDL:**
```vhdl
signal config : std_logic_vector(31 downto 0); -- @axion RW DEFAULT=0xCAFEBABE DESC="Configuration"
```

**YAML:**
```yaml
- name: config
  access: RW
  width: 32
  default: "0xCAFEBABE"
  description: "Configuration"
```

**XML:**
```xml
<register name="config" access="RW" width="32" default="0xCAFEBABE" description="Configuration"/>
```

**JSON:**
```json
{
  "name": "config",
  "access": "RW",
  "width": 32,
  "default": "0xCAFEBABE",
  "description": "Configuration"
}
```

**TOML:**
```toml
[[registers]]
name = "config"
access = "RW"
width = 32
default = "0xCAFEBABE"
description = "Configuration"
```

---

### Manual Address Assignment

Override automatic address allocation.

**VHDL:**
```vhdl
signal debug_reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x100 DESC="Debug register"
```

> **Address Conflict Recovery:** If two registers are assigned the same manual address, the second one is automatically reassigned to the next available address. A warning is recorded in `parsing_errors` but neither register is dropped.

**YAML:**
```yaml
- name: debug_reg
  addr: "0x100"
  access: RW
  description: "Debug register"
```

**XML:**
```xml
<register name="debug_reg" addr="0x100" access="RW" description="Debug register"/>
```

**JSON:**
```json
{
  "name": "debug_reg",
  "addr": "0x100",
  "access": "RW",
  "description": "Debug register"
}
```

**TOML:**
```toml
[[registers]]
name = "debug_reg"
addr = "0x100"
access = "RW"
description = "Debug register"
```

---

## Format Comparison

| Feature | VHDL | YAML | TOML | XML | JSON |
|---------|------|------|------|-----|------|
| Human readable | ✓ | ✓✓ | ✓✓ | ✓ | ✓ |
| Version control friendly | ✓ | ✓✓ | ✓✓ | ✓ | - |
| Embedded in RTL | ✓✓ | - | - | - | - |
| Automation friendly | - | ✓ | ✓ | ✓ | ✓✓ |
| Comment support | ✓ | ✓ | ✓ | ✓ | - |
| IP-XACT compatible | - | - | - | ✓ | - |
| Python ecosystem standard | - | - | ✓ | - | - |

---

## Quick Reference Card

### VHDL Annotation Syntax

```vhdl
-- Module definition (anywhere in file)
-- @axion_def BASE_ADDR=0xNNNN [CDC_EN] [CDC_STAGE=N]

-- Register with full attributes
signal name : type; -- @axion ACCESS [ADDR=0xNN] [DESC="..."] [R_STROBE] [W_STROBE] [DEFAULT=0xNN] [REG_NAME=name] [BIT_OFFSET=N]

-- Bare annotation (all defaults: RW, auto address)
signal name : type; -- @axion
```

### SystemVerilog Annotation Syntax

```systemverilog
// Module definition (anywhere in file)
// @axion_def BASE_ADDR=0xNNNN [CDC_EN] [CDC_STAGE=N]

// Register with full attributes
logic [31:0] name; // @axion ACCESS [ADDR=0xNN] [DESC="..."] [R_STROBE] [W_STROBE] [DEFAULT=0xNN]

// Bare annotation (all defaults: RW, auto address)
logic [31:0] name; // @axion
```

### YAML Structure

```yaml
module: module_name
base_addr: "0x0000"
config:
  cdc_en: false
  cdc_stage: 2
registers:
  - name: reg_name
    addr: "0x00"
    access: RW
    width: 32
    default: 0
    description: "Description"
    r_strobe: false
    w_strobe: false
```

### XML Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<register_map module="module_name" base_addr="0x0000">
    <config cdc_en="false" cdc_stage="2"/>
    <register name="reg_name" addr="0x00" access="RW" width="32" 
              default="0" description="Description" 
              r_strobe="false" w_strobe="false"/>
</register_map>
```

### JSON Structure

```json
{
  "module": "module_name",
  "base_addr": "0x0000",
  "config": {
    "cdc_en": false,
    "cdc_stage": 2
  },
  "registers": [
    {
      "name": "reg_name",
      "addr": "0x00",
      "access": "RW",
      "width": 32,
      "default": 0,
      "description": "Description",
      "r_strobe": false,
      "w_strobe": false
    }
  ]
}
```

### TOML Structure

```toml
module = "module_name"
base_addr = "0x0000"

[config]
cdc_en = false
cdc_stage = 2

[[registers]]
name = "reg_name"
addr = "0x00"
access = "RW"
width = 32
default = 0
description = "Description"
r_strobe = false
w_strobe = false
```

---

## Enumerated Values (`enum_values`)

Bit fields can have named states using `enum_values`. Each value is an integer key mapped to a name string.

### VHDL Annotation

```vhdl
signal status_field : std_logic_vector(1 downto 0);  -- @axion RW ADDR=0x00 REG_NAME=status_reg BIT_OFFSET=0 ENUM="0:IDLE,1:WAITING,3:READY"
```

### SystemVerilog Annotation

```systemverilog
logic [1:0] status_field; // @axion RW ADDR=0x00 ENUM="0:IDLE,1:WAITING,3:READY"
```

### YAML

```yaml
registers:
  - name: status_reg
    addr: "0x00"
    access: RW
    fields:
      - name: status
        bit_offset: 0
        width: 2
        enum_values:
          0: IDLE
          1: WAITING
          3: READY
```

### JSON

```json
{
  "registers": [
    {
      "name": "status_reg",
      "addr": "0x00",
      "access": "RW",
      "fields": [
        {
          "name": "status",
          "bit_offset": 0,
          "width": 2,
          "enum_values": {"0": "IDLE", "1": "WAITING", "3": "READY"}
        }
      ]
    }
  ]
}
```

### TOML

```toml
[[registers]]
name = "status_reg"
addr = "0x00"
access = "RW"

  [[registers.fields]]
  name = "status"
  bit_offset = 0
  width = 2
  [registers.fields.enum_values]
  "0" = "IDLE"
  "1" = "WAITING"
  "3" = "READY"
```

### XML (Simple, Nested)

```xml
<register name="status_reg" addr="0x00" access="RW">
  <field name="status" bit_offset="0" width="2">
    <enum_value value="0" name="IDLE"/>
    <enum_value value="1" name="WAITING"/>
    <enum_value value="3" name="READY"/>
  </field>
</register>
```

### XML (SPIRIT)

```xml
<spirit:field>
  <spirit:name>status</spirit:name>
  <spirit:bitOffset>0</spirit:bitOffset>
  <spirit:bitWidth>2</spirit:bitWidth>
  <spirit:enumeratedValues>
    <spirit:enumeratedValue>
      <spirit:name>IDLE</spirit:name>
      <spirit:value>0</spirit:value>
    </spirit:enumeratedValue>
    <spirit:enumeratedValue>
      <spirit:name>WAITING</spirit:name>
      <spirit:value>1</spirit:value>
    </spirit:enumeratedValue>
  </spirit:enumeratedValues>
</spirit:field>
```

---

## Hierarchy File Format

A hierarchy file maps module instances to base addresses, enabling centralized address management and multi-instance generation via `--hier`. All supported formats (YAML, TOML, JSON, XML) share the same structure and are normalized internally before processing.

### Top-Level Structure

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `instances` | list | Yes | List of module instance definitions |

### Instance Entry Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `module` | string | Yes | Name of the source module (must match a parsed module name) |
| `instance` | string | Required when module appears >1× | Unique instance identifier; used for output file naming |
| `base_addr` | int or hex string | Yes | Base address for this instance (e.g. `0x10000` or `65536`) |

### YAML

```yaml
instances:
  - module: gtwiz_wrapper
    instance: gtwiz_wrapper_0
    base_addr: 0x10000
  - module: gtwiz_wrapper
    instance: gtwiz_wrapper_1
    base_addr: 0x11000
  - module: spi_master
    base_addr: 0x20000
```

> `instance` is optional when a module appears only once.

### TOML

```toml
[[instances]]
module = "gtwiz_wrapper"
instance = "gtwiz_wrapper_0"
base_addr = "0x10000"

[[instances]]
module = "gtwiz_wrapper"
instance = "gtwiz_wrapper_1"
base_addr = "0x11000"

[[instances]]
module = "spi_master"
base_addr = "0x20000"
```

### JSON

```json
{
  "instances": [
    { "module": "gtwiz_wrapper", "instance": "gtwiz_wrapper_0", "base_addr": "0x10000" },
    { "module": "gtwiz_wrapper", "instance": "gtwiz_wrapper_1", "base_addr": "0x11000" },
    { "module": "spi_master", "base_addr": "0x20000" }
  ]
}
```

### XML

```xml
<hierarchy>
  <instance module="gtwiz_wrapper" name="gtwiz_wrapper_0" base_addr="0x10000"/>
  <instance module="gtwiz_wrapper" name="gtwiz_wrapper_1" base_addr="0x11000"/>
  <instance module="spi_master" base_addr="0x20000"/>
</hierarchy>
```

### Output Naming Rules

| Scenario | Output filename |
|----------|----------------|
| Module appears once, no `instance` | `<module>_axion_reg.vhd` (unchanged) |
| Module appears once, `instance` given | `<instance>_axion_reg.vhd` |
| Module appears multiple times | `<instance>_axion_reg.vhd` per entry |
