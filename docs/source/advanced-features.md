# Advanced Features

## Clock Domain Crossing (CDC)

Enable CDC synchronizers when your AXI bus and register logic use different clocks.

### VHDL Syntax
```vhdl
-- @axion_def BASE_ADDR=0x1000 CDC_EN CDC_STAGE=3
```

### YAML/JSON Syntax
```yaml
config:
  cdc_en: true
  cdc_stage: 3
```

### XML Syntax
```xml
<config cdc_en="true" cdc_stage="3"/>
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `CDC_EN` / `cdc_en` | Enable CDC synchronizers | `false` |
| `CDC_STAGE` / `cdc_stage` | Number of synchronizer stages | `2` |

## Strobe Signals

Strobe signals provide single-cycle pulses on read/write operations.

```vhdl
signal reg : std_logic_vector(31 downto 0); -- @axion RW R_STROBE W_STROBE
```

```yaml
- name: irq_status
  access: RW
  r_strobe: true   # Pulse when software reads
  w_strobe: true   # Pulse when software writes
```

**Use Cases:**
- `R_STROBE`: Clear-on-read status registers
- `W_STROBE`: Trigger actions on write (start transfer, clear flags)

## Subregisters (Packed Fields)

Pack multiple fields into a single 32-bit register:

```yaml
- name: control
  addr: "0x00"
  fields:
    - name: enable
      bit_offset: 0
      width: 1
      access: RW
    - name: mode
      bit_offset: 4
      width: 2
      access: RW
    - name: speed
      bit_offset: 8
      width: 8
      access: RW
```

This creates individual signals for each field while sharing one address.

## Wide Signals

Signals wider than 32 bits automatically span multiple addresses:

```vhdl
signal counter : std_logic_vector(63 downto 0); -- @axion RO
```

This creates two consecutive 32-bit registers:
- `counter[31:0]` at offset 0x00
- `counter[63:32]` at offset 0x04

## Default Values

Set reset values for registers:

```yaml
- name: config
  access: RW
  width: 32
  default: "0xCAFEBABE"
```

```xml
<register name="config" access="RW" width="32" default="0xCAFEBABE"/>
```

## Manual Address Assignment

Override automatic address allocation:

```vhdl
signal debug_reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x100
```

```yaml
- name: debug_reg
  addr: "0x100"
  access: RW
```
