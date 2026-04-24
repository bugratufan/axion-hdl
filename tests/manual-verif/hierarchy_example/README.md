# Hierarchy Example

This example demonstrates the `--hier` flag for centralized base address assignment
and multi-instance module generation.

## Source Files

```
src/
├── spi_master.yaml   # SPI Master — appears twice in the hierarchy (two instances)
└── i2c_master.yaml   # I2C Master — appears once (single instance)
```

## Hierarchy File

`address_map.yaml` assigns base addresses and names instances:

```yaml
instances:
  # Two SPI master instances at different base addresses
  - module: spi_master
    instance: spi_master_0
    base_addr: 0x40000000

  - module: spi_master
    instance: spi_master_1
    base_addr: 0x40001000

  # Single I2C master instance (no instance field needed — appears only once)
  - module: i2c_master
    base_addr: 0x40002000
```

**Naming rule:**
- Module appears once → output files use the original module name (`i2c_master_*`)
- Module appears multiple times → output files use the instance name (`spi_master_0_*`, `spi_master_1_*`)

## How to Reproduce

From the repository root:

```bash
axion-hdl \
  -s tests/manual-verif/hierarchy_example/src \
  -o tests/manual-verif/hierarchy_example/output \
  --hier tests/manual-verif/hierarchy_example/address_map.yaml \
  --all
```

## Generated Outputs

```
output/
├── address_map.html              ← Full address map report (all instances)
├── index.html                    ← Documentation index
├── register_map.html             ← Register map documentation
├── html/                         ← Per-module HTML docs
│
├── i2c_master_axion_reg.vhd      ← Single instance → unchanged name
├── i2c_master_axion_reg.sv
├── i2c_master_regs.h
├── i2c_master_regs.yaml
├── i2c_master_regs.json
├── i2c_master_regs.xml
│
├── spi_master_0_axion_reg.vhd    ← Multi-instance → named after instance
├── spi_master_0_axion_reg.sv
├── spi_master_0_regs.h
├── spi_master_0_regs.yaml
├── spi_master_0_regs.json
├── spi_master_0_regs.xml
│
├── spi_master_1_axion_reg.vhd
├── spi_master_1_axion_reg.sv
├── spi_master_1_regs.h
├── spi_master_1_regs.yaml
├── spi_master_1_regs.json
└── spi_master_1_regs.xml
```

The `address_map.html` shows all three instances with their base addresses,
end addresses, and sizes in a sortable table.
