# CLI Reference

The Axion-HDL command-line interface is the primary way to interact with the tool.

## Usage

```bash
axion-hdl [OPTIONS]
```

## Options

### Basic Inputs & Outputs

-   **`-s, --source <PATH>`**
    Specifies the input source. Can be a:
    -   Directory: Scans for `.vhd`, `.yaml`, `.json`, `.xml` files.
    -   File: Parses a single file.
    -   *Multiple sources:* You can use this flag multiple times (e.g., `-s ./lib_a -s ./lib_b`).
    
    ```bash
    axion-hdl -s ./src/vhdl -o ./output
    ```

-   **`-o, --output <PATH>`**
    Directory where generated files will be written. Defaults to the current directory.

-   **`-e, --exclude <PATTERN>`**
    Exclude files or directories matching the given pattern (glob). Can be used multiple times.
    
    ```bash
    axion-hdl -s ./src -e "test_*" -e "*.bak"
    ```

### Output Formats

By default, Axion only analyzes files. Use these flags to generate outputs:

-   **`--all`**
    Generate ALL supported formats (VHDL, C Header, Documentation, XML, YAML, JSON).

-   **`--vhdl`**
    Generate only the AXI4-Lite slave VHDL modules (`*_axion_reg.vhd`).

-   **`--c-header`**
    Generate C header files (`*_regs.h`).

-   **`--doc`**
    Generate Markdown documentation (`register_map.md`).

-   **`--xml`**
    Export register map to XML format.

-   **`--yaml`**
    Export register map to YAML format.

-   **`--json`**
    Export register map to JSON format.

### Other Commands

-   **`--version`**
    Show the version number and exit.

-   **`--help`**
    Show the help message and exit.
