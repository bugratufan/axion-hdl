# Data Formats

Axion-HDL supports multiple input formats, allowing you to choose the workflow that best fits your team.

## 1. VHDL Annotations (`.vhd`)
Defining registers directly in your VHDL source code keeps the documentation close to the logic. Axion parses comments starting with `@axion`.

### Syntax
```vhdl
-- @axion_def BASE_ADDR=0x1000
-- @axion_def MODULE_NAME=my_module
```

Register definition:
```vhdl
signal my_reg : std_logic_vector(31 downto 0); -- @axion <ACCESS> ADDR=<ADDRESS> [DESC="<DESCRIPTION>"] [DEFAULT=<VAL>] [CDC]
```

### Examples

**Simple Read-Only Register:**
```vhdl
signal status_reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00 DESC="System Status"
```

**Auto-Addressing:**
If you omit `ADDR`, Axion assigns the next available sequential address.
```vhdl
signal ctrl_reg : std_logic_vector(31 downto 0); -- @axion RW DESC="Control Register"
```

**Clock Domain Crossing:**
Add the `CDC` tag to automatically insert synchronizers.
```vhdl
signal async_input : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x10 CDC DESC="Asynchronous Input"
```

**Strobe Signals:**
For `RW` registers, adding `STROBE` creates a pulse signal when the register is written to.
```vhdl
signal trigger_reg : std_logic_vector(0 downto 0); -- @axion RW ADDR=0x14 STROBE
```

## 2. YAML (`.yaml`)
YAML provides a clean, structured way to define registers, especially useful for complex maps with bit fields.

### Structure
```yaml
module: <module_name>
base_addr: <hex_string>
registers:
  - name: <reg_name>
    addr: <hex_or_int>      # Optional (auto-assigned if missing)
    access: <RO|RW|WO>
    width: <int>            # Default: 32
    default: <int_or_hex>   # Optional default reset value
    description: <string>
    cdc: <bool>             # Optional, default false
    strobe: <bool>          # Optional, default false
    fields:                 # Optional sub-registers
      - name: <field_name>
        bit_offset: <int>
        width: <int>
        access: <RO|RW|WO>
        description: <string>
```

### Example
```yaml
module: sensor_hub
base_addr: 0x40000000
registers:
  - name: config
    addr: 0x00
    access: RW
    description: "Configuration Register"
    fields:
      - name: enable
        bit_offset: 0
        width: 1
        access: RW
      - name: filter_mode
        bit_offset: 4
        width: 2
        access: RW
        description: "Filter selection (0=None, 1=Low, 2=High)"

  - name: data_out
    access: RO
    width: 32
    cdc: true
    description: "Sensor data (CDC synchronized)"
```

## 3. JSON (`.json`)
JSON is ideal for programmatically generating register maps from other tools. The schema matches the YAML structure exactly.

### Example
```json
{
  "module": "sensor_hub",
  "base_addr": "0x40000000",
  "registers": [
    {
      "name": "config",
      "addr": "0x00",
      "access": "RW",
      "description": "Configuration Register",
      "fields": [
        {
          "name": "enable",
          "bit_offset": 0,
          "width": 1,
          "access": "RW"
        }
      ]
    }
  ]
}
```

## 4. XML (`.xml`)
Axion supports a custom XML simple format and allows importing/exporting for compatibility.

### Structure
```xml
<register_map>
    <module>module_name</module>
    <base_addr>0x1000</base_addr>
    <register>
        <name>reg_name</name>
        <address>0x00</address>
        <access>RW</access>
        <width>32</width>
        <description>Description</description>
    </register>
</register_map>
```
