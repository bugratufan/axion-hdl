# Data Formats

Axion-HDL supports multiple input formats. Choose based on your workflow.

## VHDL Annotations

Define registers directly in your VHDL source code using `@axion` comments:

```vhdl
-- @axion_def BASE_ADDR=0x1000 CDC_EN CDC_STAGE=3
signal status_reg : std_logic_vector(31 downto 0); -- @axion RO DESC="Status"
signal control_reg : std_logic_vector(31 downto 0); -- @axion RW W_STROBE
```

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
    description: "Status register"
  - name: control_reg
    access: RW
    w_strobe: true
```

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
    {"name": "status_reg", "access": "RO"},
    {"name": "control_reg", "access": "RW", "w_strobe": true}
  ]
}
```

## XML Format

```xml
<register_map module="my_module" base_addr="0x1000">
    <config cdc_en="true" cdc_stage="3"/>
    <register name="status_reg" access="RO"/>
    <register name="control_reg" access="RW" w_strobe="true"/>
</register_map>
```

## Complete Examples

See the [examples directory](https://github.com/bugratufan/axion-hdl/tree/develop/docs/examples) for working examples in all formats.

