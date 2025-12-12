# Axion-HDL

**Generate production-ready AXI4-Lite register interfaces from VHDL, YAML, XML, or JSON.**

[![PyPI](https://img.shields.io/pypi/v/axion-hdl.svg)](https://pypi.org/project/axion-hdl/)
[![Tests](https://github.com/bugratufan/axion-hdl/actions/workflows/tests.yml/badge.svg)](https://github.com/bugratufan/axion-hdl/actions/workflows/tests.yml)
[![Docs](https://readthedocs.org/projects/axion-hdl/badge/?version=stable)](https://axion-hdl.readthedocs.io/en/stable/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Axion-HDL eliminates the tedious work of hand-crafting AXI register logic. Define your registers once—embedded in VHDL or in standalone config files—and generate synthesizable VHDL, C headers, and documentation automatically.

---

## Installation

```bash
pip install axion-hdl
```

## Quick Start

**1. Define your registers:**

```vhdl
-- Embed directly in your VHDL
-- @axion_def BASE_ADDR=0x1000
signal status  : std_logic_vector(31 downto 0); -- @axion RO DESC="Status register"
signal control : std_logic_vector(31 downto 0); -- @axion RW W_STROBE
```

Or use standalone YAML:

```yaml
module: my_module
base_addr: "0x1000"
registers:
  - name: status
    access: RO
    description: "Status register"
  - name: control
    access: RW
    w_strobe: true
```

**2. Generate:**

```bash
axion-hdl -s my_module.vhd -o output/
```

**3. Get:**
- `my_module_axion_reg.vhd` — Synthesizable AXI4-Lite slave
- `my_module_regs.h` — C header with register macros
- `register_map.md` — Auto-generated documentation

---

## Key Features

**Multi-Format Input**  
VHDL annotations, YAML, XML, or JSON. Pick what fits your workflow. Mix sources freely.

**Clock Domain Crossing**  
Built-in CDC synchronizers with configurable pipeline depth. No external CDC libraries needed.

**Subregisters**  
Pack bit fields into a single address. Define enable bits, mode selectors, and counters in one register.

**Wide Signal Support**  
Signals wider than 32 bits are automatically split across consecutive addresses.

**Read/Write Strobes**  
Generate pulse signals on register access—useful for interrupt clearing or triggering state machines.

**Robust Validation**  
Address overlap detection, access mode checking, and bit field collision warnings before you synthesize.

---

## Tested and Verified

- 230+ automated tests covering parsing, generation, and edge cases
- GHDL simulation verification for generated interfaces
- CI on every commit

---

## Documentation

Full documentation with examples: **[axion-hdl.readthedocs.io](https://axion-hdl.readthedocs.io/en/stable/)**

---

## Contributing

1. Fork the repository
2. Create a feature branch from `develop`
3. Run `make test` to verify
4. Submit a PR to `develop`

---

## License

MIT License — [Bugra Tufan](mailto:bugratufan97@gmail.com)
