# Data Formats

Axion-HDL supports multiple input formats. Choose based on your workflow.

## VHDL Annotations

Define registers directly in your VHDL source code using `@axion` comments:

```vhdl
-- Module-level definition
-- @axion_def BASE_ADDR=0x1000 CDC_EN CDC_STAGE=3

-- Register definitions
signal status_reg : std_logic_vector(31 downto 0);  -- @axion RO DESC="Status"
signal control_reg : std_logic_vector(31 downto 0); -- @axion RW W_STROBE
signal tx_data : std_logic_vector(31 downto 0);     -- @axion WO DESC="TX buffer"
```

---

## YAML Format

```yaml
module: my_module
base_addr: "0x1000"
config:
  cdc_en: true
  cdc_stage: 3
registers:
  - name: status_reg
    access: RO
    description: "Status"
  - name: control_reg
    access: RW
    w_strobe: true
  - name: tx_data
    access: WO
    description: "TX buffer"
```

---

## XML Format

```xml
<?xml version="1.0" encoding="UTF-8"?>
<register_map module="my_module" base_addr="0x1000">
    <config cdc_en="true" cdc_stage="3"/>
    <register name="status_reg" access="RO" description="Status"/>
    <register name="control_reg" access="RW" w_strobe="true"/>
    <register name="tx_data" access="WO" description="TX buffer"/>
</register_map>
```

---

## JSON Format

```json
{
  "module": "my_module",
  "base_addr": "0x1000",
  "config": {
    "cdc_en": true,
    "cdc_stage": 3
  },
  "registers": [
    {"name": "status_reg", "access": "RO", "description": "Status"},
    {"name": "control_reg", "access": "RW", "w_strobe": true},
    {"name": "tx_data", "access": "WO", "description": "TX buffer"}
  ]
}
```

---

## Format Comparison

| Feature | VHDL | YAML | XML | JSON |
|---------|------|------|-----|------|
| Human readable | ✓ | ✓✓ | ✓ | ✓ |
| Version control friendly | ✓ | ✓✓ | ✓ | - |
| Embedded in RTL | ✓✓ | - | - | - |
| Automation friendly | - | ✓ | ✓ | ✓✓ |

## Complete Examples

See the [examples directory](https://github.com/bugratufan/axion-hdl/tree/develop/docs/examples) for working examples in all formats:
- `spi_master.vhd` - VHDL with annotations
- `led_blinker.yaml` - YAML format
- `pwm_controller.xml` - XML format
- `gpio_controller.json` - JSON format
