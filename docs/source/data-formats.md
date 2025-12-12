# Data Formats

Axion-HDL supports multiple input formats.

## VHDL Annotations

Define registers in your VHDL source code using `@axion` comments:

```vhdl
-- @axion_def BASE_ADDR=0x1000 CDC_EN CDC_STAGE=3
signal status_reg : std_logic_vector(31 downto 0); -- @axion RO DESC="Status"
signal control_reg : std_logic_vector(31 downto 0); -- @axion RW W_STROBE
```

## YAML Format

```yaml
module: my_module
base_addr: 0x1000
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
  "registers": [
    {"name": "status_reg", "access": "RO"},
    {"name": "control_reg", "access": "RW", "w_strobe": true}
  ]
}
```

## XML Format

```xml
<register_map module="my_module" base_addr="0x1000">
    <register name="status_reg" access="RO"/>
    <register name="control_reg" access="RW" w_strobe="true"/>
</register_map>
```
