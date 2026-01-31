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

# Generate from TOML file
axion-hdl -s registers.toml -o ./output --all

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
# Single file (YAML, JSON, XML, or TOML)
axion-hdl -s controller.yaml -o ./output --all
axion-hdl -s controller.toml -o ./output --all

# Multiple files
axion-hdl -s cpu_regs.yaml -s dma_regs.xml -s spi_regs.toml -o ./output --all

# Entire directory (recursive scan)
axion-hdl -s ./rtl -o ./generated --all

# Mixed files and directories
axion-hdl -s ./rtl -s extra_regs.toml -o ./output --all
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
---

## CI/CD Integration

Axion-HDL integrates seamlessly with continuous integration pipelines.

### GitHub Actions

Create `.github/workflows/generate-regs.yml`:

```yaml
name: Generate Register Files

on:
  push:
    paths:
      - 'regs/**'
      - 'rtl/**/*.vhd'
  pull_request:
    paths:
      - 'regs/**'
      - 'rtl/**/*.vhd'

jobs:
  generate:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install Axion-HDL
        run: pip install axion-hdl
      
      - name: Generate Register Files
        run: |
          axion-hdl -s ./regs -s ./rtl -o ./generated --all -e "*_tb.vhd"
      
      - name: Upload Generated Files
        uses: actions/upload-artifact@v4
        with:
          name: generated-registers
          path: generated/
      
      - name: Commit Generated Files (optional)
        if: github.ref == 'refs/heads/main'
        run: |
          git config user.name github-actions
          git config user.email github-actions@github.com
          git add generated/
          git diff --staged --quiet || git commit -m "chore: regenerate register files"
          git push
```

### GitLab CI

Create `.gitlab-ci.yml`:

```yaml
stages:
  - generate
  - test

generate-registers:
  stage: generate
  image: python:3.11
  script:
    - pip install axion-hdl
    - axion-hdl -s ./regs -o ./generated --all
  artifacts:
    paths:
      - generated/
    expire_in: 1 week
  only:
    changes:
      - regs/**/*
      - rtl/**/*.vhd

validate-registers:
  stage: test
  image: python:3.11
  script:
    - pip install axion-hdl
    - |
      python3 << 'EOF'
      from axion_hdl import AxionHDL
      from axion_hdl.rule_checker import RuleChecker
      
      axion = AxionHDL()
      axion.add_source("./regs")
      modules = axion.analyze()
      
      checker = RuleChecker()
      results = checker.run_all_checks(modules)
      
      if results["errors"]:
          for e in results["errors"]:
              print(f"ERROR: {e['message']}")
          exit(1)
      print("✓ Validation passed")
      EOF
  only:
    - merge_requests
```

### Makefile Integration

Add to your project's `Makefile`:

```makefile
# Register generation targets
REGS_SRC := ./regs
REGS_OUT := ./generated
AXION := axion-hdl

.PHONY: regs regs-clean regs-check

# Generate all register files
regs:
	$(AXION) -s $(REGS_SRC) -o $(REGS_OUT) --all -e "*_tb.vhd"
	@echo "✓ Register files generated in $(REGS_OUT)"

# Clean generated files
regs-clean:
	rm -rf $(REGS_OUT)
	@echo "✓ Cleaned $(REGS_OUT)"

# Validate without generating
regs-check:
	@python3 -c "\
from axion_hdl import AxionHDL; \
from axion_hdl.rule_checker import RuleChecker; \
a = AxionHDL(); a.add_source('$(REGS_SRC)'); m = a.analyze(); \
r = RuleChecker().run_all_checks(m); \
exit(1) if r['errors'] else print('✓ Validation passed')"

# Watch for changes and regenerate
regs-watch:
	@echo "Watching $(REGS_SRC) for changes..."
	@while true; do \
		inotifywait -qr -e modify $(REGS_SRC) && $(MAKE) regs; \
	done
```

Usage:

```bash
make regs          # Generate all
make regs-clean    # Clean output
make regs-check    # Validate only
```

### Shell Script

Create `scripts/generate_regs.sh`:

```bash
#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="${PROJECT_DIR}/generated"

echo "=== Axion-HDL Register Generation ==="

# Check if axion-hdl is installed
if ! command -v axion-hdl &> /dev/null; then
    echo "ERROR: axion-hdl not found. Install with: pip install axion-hdl"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Run generation
echo "Generating from: ${PROJECT_DIR}/regs"
echo "Output to: ${OUTPUT_DIR}"

axion-hdl \
    -s "${PROJECT_DIR}/regs" \
    -s "${PROJECT_DIR}/rtl" \
    -o "$OUTPUT_DIR" \
    --all \
    -e "*_tb.vhd" \
    -e "deprecated"

# Check result
if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Generation successful!"
    echo "Generated files:"
    ls -la "$OUTPUT_DIR"
else
    echo ""
    echo "✗ Generation failed!"
    exit 1
fi
```

---

## Configuration File

Create `.axion_conf` for project-specific settings:

```json
{
    "src_dirs": ["./rtl"],
    "src_files": ["./top.vhd"],
    "yaml_src_dirs": ["./regs"],
    "exclude_patterns": ["*_tb.vhd", "test_*", "deprecated"],
    "output_dir": "./generated"
}
```

```bash
# Use config file explicitly
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
5. **CI/CD artifacts** - upload generated files for downstream jobs

