# Command Line Interface (CLI)

The CLI is the fastest way to use Axion-HDL for quick generation tasks, CI/CD pipelines, and scripting.

## Installation

```bash
pip install axion-hdl
```

## Basic Usage

```bash
axion-hdl -s <source> -o <output> [options]
```

## Quick Start

```bash
# Generate all outputs from a YAML file
axion-hdl -s registers.yaml -o ./output --all

# Generate from VHDL with annotations
axion-hdl -s ./src/my_module.vhd -o ./generated --all

# Start the interactive GUI
axion-hdl -s ./src --gui
```

---

## Command Reference

### Source Options

| Option | Description |
|--------|-------------|
| `-s, --source PATH` | Source file or directory (auto-detects type by extension) |
| `-x, --xml-source PATH` | XML source (deprecated, use -s instead) |
| `-c, --config FILE` | Load configuration from JSON file |

**Examples:**

```bash
# Single file
axion-hdl -s controller.yaml -o ./output --all

# Multiple files
axion-hdl -s cpu_regs.yaml -s dma_regs.xml -o ./output --all

# Entire directory (recursive scan)
axion-hdl -s ./rtl -o ./generated --all

# Mixed files and directories
axion-hdl -s ./rtl -s extra_regs.json -o ./output --all
```

### Output Options

| Option | Description |
|--------|-------------|
| `-o, --output DIR` | Output directory (default: `./axion_output`) |
| `-e, --exclude PATTERN` | Exclude files matching glob pattern |

**Examples:**

```bash
# Custom output directory
axion-hdl -s ./src -o ./generated_rtl --all

# Exclude testbenches
axion-hdl -s ./src -e "*_tb.vhd" -o ./output --all

# Multiple exclude patterns
axion-hdl -s ./src -e "*_tb.vhd" -e "test_*" -e "deprecated" -o ./output --all
```

### Generation Flags

| Flag | Description |
|------|-------------|
| `--all` | Generate all output types |
| `--vhdl` | Generate VHDL register module |
| `--c-header` | Generate C header file |
| `--xml` | Generate XML register map |
| `--yaml` | Generate YAML register map |
| `--json` | Generate JSON register map |
| `--doc` | Generate Markdown documentation |
| `--doc-format FORMAT` | Documentation format: `md`, `html`, `pdf` |

**Examples:**

```bash
# Generate everything
axion-hdl -s regs.yaml -o ./output --all

# Only VHDL and C header
axion-hdl -s regs.yaml -o ./output --vhdl --c-header

# Only documentation in HTML format
axion-hdl -s regs.yaml -o ./docs --doc --doc-format html

# Multiple formats
axion-hdl -s regs.yaml -o ./output --vhdl --c-header --doc --yaml
```

### GUI Options

| Option | Description |
|--------|-------------|
| `--gui` | Start interactive web GUI |
| `--port PORT` | GUI server port (default: 5000) |

**Examples:**

```bash
# Start GUI with current directory
axion-hdl --gui

# Start GUI with specific source
axion-hdl -s ./rtl --gui

# Start on different port
axion-hdl -s ./rtl --gui --port 8080
```

### Information Options

| Option | Description |
|--------|-------------|
| `-v, --version` | Show version and exit |
| `-h, --help` | Show help message and exit |

---

## Complete Workflow Examples

### 1. Single Module Generation

```bash
# Input: spi_master.vhd with @axion annotations
# Output: VHDL module, C header, Markdown docs

axion-hdl -s spi_master.vhd -o ./output --vhdl --c-header --doc
```

Output files:
```
output/
├── spi_master_axion_reg.vhd    # AXI4-Lite slave module
├── spi_master_regs.h           # C header with macros
└── register_map.md             # Documentation
```

### 2. Multi-Module Project

```bash
# Process entire RTL directory
axion-hdl -s ./rtl -o ./generated --all -e "*_tb.vhd"
```

Output files:
```
generated/
├── module_a_axion_reg.vhd
├── module_a_regs.h
├── module_a_regs.yaml
├── module_b_axion_reg.vhd
├── module_b_regs.h
├── module_b_regs.yaml
├── register_map.md
└── ...
```

### 3. CI/CD Integration

```bash
#!/bin/bash
# ci_generate.sh

# Generate from all YAML definitions
axion-hdl -s ./regs -o ./generated --all

# Check exit code
if [ $? -eq 0 ]; then
    echo "Generation successful"
else
    echo "Generation failed"
    exit 1
fi
```

### 4. Configuration File

Create `.axion_conf` or use `--config`:

```json
{
    "sources": ["./rtl", "./extra_regs.yaml"],
    "excludes": ["*_tb.vhd", "deprecated"],
    "output": "./generated"
}
```

```bash
# Use config file
axion-hdl --config .axion_conf --all

# Auto-loads .axion_conf if present in current directory
axion-hdl --all
```

---

## Supported File Types

| Extension | Format | Description |
|-----------|--------|-------------|
| `.vhd`, `.vhdl` | VHDL | Source with `@axion` annotations |
| `.yaml`, `.yml` | YAML | Human-readable register definitions |
| `.json` | JSON | Machine-readable register definitions |
| `.xml` | XML | IP-XACT style register definitions |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (invalid input, failed generation, conflicts) |

---

## Tips

1. **Use `--all` for quick generation** - generates everything in one command
2. **Exclude patterns** - great for skipping testbenches and deprecated files
3. **Config files** - store project-specific settings for consistent generation
4. **Combine sources** - mix VHDL, YAML, XML, JSON in a single run
