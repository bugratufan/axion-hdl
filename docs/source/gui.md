# Interactive GUI

Axion-HDL includes a web-based graphical user interface for managing your register maps visually. The GUI provides a complete workflow for viewing, editing, validating, and generating register interfaces.

## Installation

The GUI requires Flask. Install with GUI support:

```bash
pip install axion-hdl[gui]
```

Or install Flask separately:

```bash
pip install flask>=2.0
```

---

## Starting the GUI

### Basic Launch

```bash
axion-hdl --gui
```

This starts a local web server at `http://127.0.0.1:5000` and opens your default browser.

### With Source Files

```bash
axion-hdl -s ./rtl --gui
```

Pre-loads source files before starting the GUI.

### Custom Port

```bash
axion-hdl -s ./rtl --gui --port 8080
```

Use a different port (useful when 5000 is occupied).

---

## Dashboard

The main dashboard (`/`) provides an overview of all parsed modules.

### Statistics Cards

| Card | Description |
|------|-------------|
| **Modules** | Total number of parsed modules |
| **Registers** | Total register count across all modules |
| **CDC Enabled** | Number of modules with CDC synchronizers |
| **Source Files** | Number of input files loaded |

### Module Cards

Each module is displayed as a card showing:

- **Module Name** - Click to open editor
- **Base Address** - Hex address (e.g., `0x1000`)
- **Register Count** - Number of registers
- **Source File** - Input file name
- **CDC Badge** - Shown if CDC is enabled
- **Register Preview** - First 5 registers listed

### Empty State

When no modules are loaded, the dashboard shows:
- Instructions for adding sources
- Link to configuration page

---

## Module Editor

The editor page (`/module/<name>`) allows full editing of module properties and registers.

### Module Properties

| Property | Description |
|----------|-------------|
| **Base Address** | Module base address (hex input) |
| **CDC Enable** | Toggle for clock domain crossing |
| **CDC Stages** | Number of sync stages (2-5), visible when CDC enabled |

### Register Table

Interactive table with columns:

| Column | Description | Editable |
|--------|-------------|----------|
| **Name** | Register/signal name | Yes |
| **Width** | Bit width (1-1024) | Yes |
| **Access** | RO, WO, or RW (color-coded dropdown) | Yes |
| **Default** | Reset value (hex format) | Yes |
| **Description** | Documentation text | Yes |
| **Address** | Calculated address | No (auto) |
| **R_STROBE** | Read strobe checkbox | Yes |
| **W_STROBE** | Write strobe checkbox | Yes |
| **Actions** | Edit, Duplicate, Delete buttons | - |

### Register Actions

| Button | Action |
|--------|--------|
| **Add Register** | Add new blank register row |
| **Duplicate** | Copy selected register |
| **Delete** | Remove register (with confirmation) |
| **Review & Save** | Open diff view before saving |

### Validation

Invalid inputs show visual error indication:
- Empty register names
- Invalid width values
- Malformed hex addresses

---

## Diff & Review

Before saving changes, the diff page (`/diff/<module>`) shows:

### Views

| View | Description |
|------|-------------|
| **Unified** | Single view with additions (green) and deletions (red) |
| **Side-by-Side** | Original and modified versions side-by-side |

Toggle between views using the view toggle button.

### Actions

| Button | Action |
|--------|--------|
| **Confirm & Save** | Apply changes to source file |
| **Cancel** | Return to editor without saving |

### Color Coding

| Color | Meaning |
|-------|---------|
| Green | Added lines |
| Red | Deleted lines |
| Default | Unchanged context |

---

## Output Generation

The generate page (`/generate`) allows batch output generation.

### Output Directory

- Text input showing current output path
- Default: `./axion_output`
- Browse button for folder selection (where supported)

### Format Toggles

All formats are enabled by default:

| Toggle | Output |
|--------|--------|
| **VHDL Modules** | `_axion_reg.vhd` files |
| **C Headers** | `_regs.h` files |
| **Markdown Docs** | `register_map.md` |
| **HTML Docs** | HTML pages with styling |
| **XML Map** | `_regs.xml` files |
| **YAML Map** | `_regs.yaml` files |
| **JSON Map** | `_regs.json` files |

### Generation Process

1. Click **Generate Files**
2. Watch the **Activity Log** for progress
3. **Status Badge** shows: Idle → Running → Success/Error
4. Generated files appear in output directory

### Activity Log

Real-time log showing:
- Files being generated
- Success/error messages
- File paths and sizes

---

## Rule Check

The rule check page (`/rule-check`) validates your register definitions.

### Running Checks

Click **Run Rule Check** to validate all modules.

### Check Categories

| Category | Description |
|----------|-------------|
| **Address Overlap** | Detects overlapping module address ranges |
| **Address Alignment** | Warns on non-4-byte aligned addresses |
| **Naming Convention** | Validates VHDL identifier rules |
| **Reserved Keywords** | Detects VHDL reserved word usage |
| **Duplicate Names** | Finds duplicate register names within modules |
| **Duplicate Modules** | Detects multiple modules with same name |
| **Default Values** | Validates default values fit register width |
| **Format Issues** | Reports YAML/JSON/XML syntax problems |

### Results Display

| Severity | Color | Description |
|----------|-------|-------------|
| **Error** | Red | Must fix before generation |
| **Warning** | Yellow | Should review but may be acceptable |
| **Pass** | Green | All checks passed |

### Summary

Shows total counts:
- Number of errors
- Number of warnings
- Pass/fail indicator

---

## Configuration

The configuration page (`/config`) manages sources and settings.

### Source Management

| Action | Description |
|--------|-------------|
| **Add Directory** | Scan directory recursively for source files |
| **Add File** | Add individual source file |
| **Remove** | Remove source from list |

### Exclude Patterns

Configure glob patterns to exclude files:
- `*_tb.vhd` - Testbenches
- `*_sim.vhd` - Simulation files
- `generated/*` - Generated output

### Settings

| Setting | Description |
|---------|-------------|
| **Output Directory** | Default generation path |
| **Auto-reload** | Automatically refresh on file changes |

### Apply Changes

Click **Apply & Re-analyze** to:
1. Re-scan source directories
2. Parse all source files
3. Update module list
4. Return to dashboard

---

## Configuration File (`.axion_conf`)

The GUI can save/load configuration from `.axion_conf` in your project root.

### File Format (JSON)

```json
{
  "sources": [
    "./rtl",
    "./ip/registers.yaml"
  ],
  "excludes": [
    "*_tb.vhd",
    "*_sim.vhd"
  ],
  "output_dir": "./output"
}
```

### Behavior

- Auto-loaded on GUI startup if present
- Saved when configuration is modified
- Add to `.gitignore` for local-only settings

---

## Navigation

### Navbar Links

| Link | Page |
|------|------|
| **Axion-HDL GUI** | Dashboard (home) |
| **Modules** | Dashboard |
| **Rule Check** | Validation page |
| **Generate** | Output generation |
| **Config** | Configuration settings |

### Breadcrumbs

Editor pages show breadcrumbs for navigation:
- Dashboard > Module Name

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+S` | Save changes (in editor) |
| `Escape` | Cancel current action |

---

## Unsaved Changes

The GUI tracks unsaved changes and provides warnings:

| Scenario | Behavior |
|----------|----------|
| **Navigate away** | Confirmation dialog |
| **Close browser** | `beforeunload` warning |
| **Return from diff** | Changes preserved |
| **After save** | Indicator clears |

Visual indicator appears in navbar when unsaved changes exist.

---

## Troubleshooting

### Flask Not Found

```
Error: Flask is required for GUI mode. Install with: pip install flask
```

**Solution:** Install Flask: `pip install flask>=2.0`

### Port Already in Use

```
Error: Address already in use
```

**Solution:** Use different port: `axion-hdl --gui --port 8080`

### Browser Doesn't Open

**Solution:** Manually navigate to `http://127.0.0.1:5000`

### Changes Not Saving

**Possible causes:**
- File permissions
- File in use by another process
- Invalid VHDL syntax after modification

Check the activity log for error messages.

---

## File Modification Behavior

The GUI modifies source files differently based on format:

| Format | Behavior |
|--------|----------|
| **YAML** | Preserves comments and structure |
| **JSON** | Preserves structure, updates only changed fields |
| **XML** | Preserves comments and attributes |
| **VHDL** | Minimal edits, only changed signals updated |

```{note}
VHDL modification is currently experimental and mainly supports appending new signals. Renaming existing VHDL registers is restricted.
```
