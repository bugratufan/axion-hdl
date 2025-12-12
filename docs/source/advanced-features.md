# Advanced Features

## Clock Domain Crossing (CDC)

Enable CDC at the module level:

```vhdl
-- @axion_def BASE_ADDR=0x1000 CDC_EN CDC_STAGE=3
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `CDC_EN` | Enable CDC synchronizers | `false` |
| `CDC_STAGE` | Number of synchronizer stages | `2` |

## Strobe Signals

```vhdl
signal reg : std_logic_vector(31 downto 0); -- @axion RW R_STROBE W_STROBE
```

- `R_STROBE`: Pulse on read
- `W_STROBE`: Pulse on write

## Subregisters

Pack multiple fields into one register:

```yaml
- name: control
  fields:
    - name: enable
      bit_offset: 0
      width: 1
    - name: mode
      bit_offset: 4
      width: 2
```

## Wide Signals

Signals >32 bits automatically span multiple addresses.
