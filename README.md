# Axion-HDL

**AXI4-Lite register interfaces from VHDL, YAML, XML, or JSON. One command.**

[![PyPI](https://img.shields.io/pypi/v/axion-hdl.svg)](https://pypi.org/project/axion-hdl/)
[![Tests](https://github.com/bugratufan/axion-hdl/actions/workflows/tests.yml/badge.svg)](https://github.com/bugratufan/axion-hdl/actions/workflows/tests.yml)
[![Docs](https://readthedocs.org/projects/axion-hdl/badge/?version=stable)](https://axion-hdl.readthedocs.io/en/stable/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## Install

```bash
axion-hdl -s my_module.vhd -o output/
```

## Use

```bash
# From VHDL with @axion annotations
axion-hdl -s my_module.vhd -o output/

# From YAML/XML/JSON
axion-hdl -s registers.yaml -o output/
```

**Output:** VHDL module, C header, documentation, XML/YAML/JSON exports.

## Define Registers

**VHDL** — embed in your code:
```vhdl
-- @axion_def BASE_ADDR=0x1000 CDC_EN
signal status  : std_logic_vector(31 downto 0); -- @axion RO
signal control : std_logic_vector(31 downto 0); -- @axion RW W_STROBE
```

**YAML** — standalone file:
```yaml
module: my_module
base_addr: "0x1000"
config:
  cdc_en: true
registers:
  - name: status
    access: RO
  - name: control
    access: RW
    w_strobe: true
```

## Features

- **Multi-format input** — VHDL annotations, YAML, XML, JSON
- **CDC support** — built-in clock domain crossing synchronizers
- **Subregisters** — pack multiple fields into one address
- **Wide signals** — auto-split 64-bit+ signals across addresses
- **Tested** — 230+ tests, GHDL simulation verified

## Documentation

📖 **[axion-hdl.readthedocs.io](https://axion-hdl.readthedocs.io/en/stable/)**

## Contributing

```bash
git checkout develop
git checkout -b feature/your-feature
make test
# PR to develop
```

## License

MIT — [Bugra Tufan](mailto:bugratufan97@gmail.com)
