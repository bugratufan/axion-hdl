# Interactive GUI

Axion-HDL includes a web-based graphical user interface for managing your register maps visually.

## Starting the GUI

```bash
axion-hdl --gui
```

or with source files:

```bash
axion-hdl -s ./rtl --gui
```

The GUI will start a local web server at `http://127.0.0.1:5000`.

## Configuration File (.axion_conf)

When using the GUI, you can save your configuration (sources, excludes, output directory) to a `.axion_conf` file in your project root. This file is automatically loaded on subsequent runs.

```{note}
The `.axion_conf` file is local to your project and should be added to `.gitignore`.
```

## Pages

### Dashboard (/)

The main dashboard shows:

- **Statistics Cards**: Modules count, total registers, CDC-enabled modules, source files
- **Module List**: All parsed modules with their properties
- **Register Preview**: Quick view of first 5 registers per module

Click any module to open the editor.

### Module Editor (/module/{name})

Edit module properties:

- **Base Address**: Set the module's base address in hex
- **CDC Settings**: Enable/disable clock domain crossing with stage count
- **Register Table**: View, add, edit, and delete registers

### Generate (/generate)

Generate output files:

| Format | Description |
|--------|-------------|
| VHDL Modules | AXI4-Lite wrapper modules |
| JSON Map | Machine-readable register specs |
| C Headers | Driver definitions |
| Markdown Docs | Register map documentation |
| HTML Docs | Styled web page documentation |

### Rule Check (/rule-check)

Validate your register map:

- Address overlap detection
- CDC configuration warnings
- Width and access mode validation

### Configuration (/config)

Manage sources and settings:

- Add/remove source directories and files
- Configure exclude patterns
- Set output directory
- Apply changes and re-analyze

## GUI Port Configuration

```bash
# Use a different port
axion-hdl -s ./rtl --gui --port 8080
```

## Screenshots

The GUI provides a modern, responsive interface with:

- Clean statistics dashboard
- Interactive register tables
- Live activity logs
- Bootstrap-based styling with Inter font
