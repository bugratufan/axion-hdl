# Axion-HDL: The AXI4-Lite Register Generator that works *with* you

[![PyPI version](https://img.shields.io/pypi/v/axion-hdl.svg)](https://pypi.org/project/axion-hdl/)
[![Tests](https://github.com/bugratufan/axion-hdl/actions/workflows/tests.yml/badge.svg)](https://github.com/bugratufan/axion-hdl/actions/workflows/tests.yml)
[![Python 3.8+](https://img.shields.io/pypi/pyversions/axion-hdl.svg)](https://pypi.org/project/axion-hdl/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Stop wrestling with register maps defined in spreadsheets or clunky external tools.**

**Axion-HDL** gives you the freedom to define your registers YOUR way: directly inside your VHDL code OR via XML, YAML, or JSON files. Whichever path you choose, you get a fully compliant, rock-solid AXI4-Lite slave interface in seconds.

## 🚀 Two Ways to Play

Axion-HDL is designed to fit *your* workflow, not the other way around.

### Option A: The Developer's Value - Embed in VHDL
Keep your register definitions where they belong: right next to the logic using them. No context switching, no out-of-sync docs.

```vhdl
signal control_reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x04 W_STROBE
```

### Option B: The System Integrator's Choice - Standalone XML
Need a standardized definition that exists outside the RTL? We speak fluent IP-XACT / XML.

```xml
<register name="control_reg" addr="0x04" access="WO" width="32" w_strobe="true"/>
```

### Option C: Human-Readable YAML
Prefer a clean, version-control friendly format?

```yaml
registers:
  - name: control_reg
    addr: "0x04"
    access: WO
    width: 32
    w_strobe: true
```

### Option D: JSON for Automation
Integrating with web tools or APIs?

```json
{"name": "control_reg", "addr": "0x04", "access": "WO", "width": 32, "w_strobe": true}
```

**Axion-HDL bridges the gap.** You can even mix and match sources.

---

## ✨ Why Axion-HDL?

### 1. Flexible Input, Perfect Output
Whether you use `@axion` annotations, XML, YAML, or JSON files, the output is always the same high-quality, readable VHDL code, C headers, and documentation.

### 2. Battle-Tested Reliability
We don't guess; we verify.
*   **200+ Automated Tests**: Every commit runs through a massive test suite.
*   **Covering the Hard Stuff**: We rigorously test Complex Clock Domain Crossing (CDC) scenarios, corner-case addressing, and parser robustness.
*   **Safety First**: Built-in overlap detection and validation ensure you never ship a broken address map.

### 3. Professional Standards
*   **Spec-Driven**: Developed against [strict requirement specifications](requirements.md).
*   **Pure Python**: No heavy JVM or compiled dependencies.
*   **Standard Compliant**: Generates IP-XACT compatible XML and true AXI4-Lite interfaces.

---

## 📦 Installation

```bash
pip install axion-hdl
```

## ⚡ Quick Start

### 1. Define It

**VHDL Style:**
```vhdl
architecture rtl of my_ip is
    -- @axion_def BASE_ADDR=0x1000 CDC_EN
    signal status : std_logic_vector(31 downto 0); -- @axion RO DESC="Status"
begin
    ...
```

**XML Style:**
```xml
<register_map module="my_ip" base_addr="0x1000">
    <config cdc_en="true"/>
    <register name="status" access="RO" width="32" description="Status"/>
</register_map>
```

### 2. Generate It

```bash
axion-hdl -s my_ip.vhd -o ./output
# OR
axion-hdl -s regulations.xml -o ./output
```

### 3. Use It

You get:
*   `my_ip_axion_reg.vhd`: The AXI slave logic.
*   `my_ip_regs.h`: C header for your firmware.
*   `register_map.md`: Beautiful documentation for your users.

---

## 🧩 Feature Highlights

| Feature | Description |
|---------|-------------|
| **Subregisters** | Pack multiple fields (start bit, enable bit, etc.) into one 32-bit register automatically. |
| **CDC Support** | Built-in, parameterizable Clock Domain Crossing synchronizers. safely move data across clocks. |
| **Wide Signals** | Got a 64-bit counter? We automatically map it to multiple 32-bit addresses. |
| **Documentation** | Auto-generated Markdown or HTML documentation keeps your team in sync. |

---

## 💻 CLI Reference

```bash
# Basic usage
axion-hdl -s ./src -o ./output

# Filter inputs
axion-hdl -s ./src -e "*_tb.vhd"

# Specific outputs only
axion-hdl -s ./src --vhdl --c-header
```

## 🧪 Robust Testing & Requirements

We believe in software that works. 
*   **200+ Unit & Integration Tests**: Running on every push.
*   **GHDL Verification**: Generated VHDL is verified against GHDL simulations to ensure correct bus behavior.
*   **Transparent Requirements**: [requirements.md](requirements.md) tracks every feature we implement.

## 🤝 Contributing

We welcome pull requests! Please base your formatting on the `develop` branch.

1. Fork the repo.
2. `git checkout develop`
3. Create your feature branch.
4. `make test` (Ensure you pass the 200+ test suite!)
5. PR to `develop`.

---

## 📄 License

MIT License - see [LICENSE](LICENSE)

## 👤 Author

**Bugra Tufan**  
📧 [bugratufan97@gmail.com](mailto:bugratufan97@gmail.com)  
🔗 [github.com/bugratufan/axion-hdl](https://github.com/bugratufan/axion-hdl)
