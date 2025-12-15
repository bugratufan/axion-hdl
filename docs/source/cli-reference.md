# CLI Reference

## Basic Usage

```bash
axion-hdl -s <source> -o <output> [options]
```

## Options

| Option | Description |
|--------|-------------|
| `-s, --source PATH` | Source file or directory (auto-detects type) |
| `-x, --xml-source PATH` | XML source (deprecated, use -s) |
| `-o, --output DIR` | Output directory (default: ./axion_output) |
| `-e, --exclude PATTERN` | Exclude files matching pattern |
| `--gui` | Start interactive web GUI |
| `--port PORT` | GUI port (default: 5000) |
| `--all` | Generate all output types |
| `--vhdl` | Generate VHDL module |
| `--c-header` | Generate C header |
| `--xml` | Generate XML output |
| `--yaml` | Generate YAML output |
| `--json` | Generate JSON output |
| `--doc` | Generate documentation (Markdown) |
| `--doc-format FORMAT` | Documentation format (md, html, pdf) |
| `-v, --version` | Show version |
| `-h, --help` | Show help |

## Examples

### Basic Generation

```bash
# Generate all outputs from a YAML file
axion-hdl -s registers.yaml -o ./output --all

# Generate from VHDL with annotations
axion-hdl -s ./src/my_module.vhd -o ./generated --all

# Generate from XML
axion-hdl -s controller.xml -o ./output --vhdl --c-header
```

### Multiple Sources

```bash
# Combine multiple source files
axion-hdl -s cpu_regs.yaml -s dma_regs.xml -o ./output --all

# Process entire directory
axion-hdl -s ./rtl -o ./generated --all
```

### Filtering

```bash
# Exclude testbenches
axion-hdl -s ./src -e "*_tb.vhd" -o ./output --all

# Exclude multiple patterns
axion-hdl -s ./src -e "*_tb.vhd" -e "test_*" -e "deprecated" --all
```

### Selective Output

```bash
# Only VHDL and C header
axion-hdl -s regs.yaml -o ./output --vhdl --c-header

# Only documentation in HTML
axion-hdl -s regs.yaml -o ./docs --doc --doc-format html
```

## Supported File Types

| Extension | Format | Description |
|-----------|--------|-------------|
| `.vhd`, `.vhdl` | VHDL | Source with @axion annotations |
| `.xml` | XML | IP-XACT style register definitions |
| `.yaml`, `.yml` | YAML | Human-readable register definitions |
| `.json` | JSON | Machine-readable register definitions |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (invalid input, failed generation) |
