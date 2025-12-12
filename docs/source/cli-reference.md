# CLI Reference

## Basic Usage

```bash
axion-hdl -s <source> -o <output> [options]
```

## Options

| Option | Description |
|--------|-------------|
| `-s, --source` | Source file or directory (VHDL, XML, YAML, JSON) |
| `-o, --output` | Output directory |
| `-e, --exclude` | Patterns to exclude |
| `--vhdl` | Generate VHDL output |
| `--c-header` | Generate C header |
| `--xml` | Generate XML output |
| `--yaml` | Generate YAML output |
| `--json` | Generate JSON output |
| `--doc` | Generate documentation |
| `--all` | Generate all outputs |
| `-h, --help` | Show help |
| `--version` | Show version |

## Examples

```bash
# Generate all outputs from VHDL
axion-hdl -s ./src -o ./output --all

# Generate only VHDL and C header
axion-hdl -s ./regs.yaml -o ./output --vhdl --c-header

# Exclude test files
axion-hdl -s ./src -o ./output -e "*_tb.vhd" --all
```
