# Axion-HDL Copilot Instructions

## Project Overview
Axion-HDL generates AXI4-Lite register interfaces from VHDL annotations, YAML, XML, or JSON input. One command produces VHDL modules, C headers, and documentation.

## Git Workflow

**IMPORTANT: Always follow this workflow for any changes.**

1. **Create branch from `develop`**:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and test thoroughly** (see Testing section)

3. **Commit with meaningful messages** (see Commit Guidelines)

4. **Create Pull Request to `develop`** - never directly to `main`

## Architecture

### Core Pipeline
```
Input Sources → Parsers → AxionHDL (orchestrator) → Generators → Output Files
```

- **Parsers**: `parser.py` (VHDL), `yaml_input_parser.py`, `xml_input_parser.py`, `json_input_parser.py`
- **Orchestrator**: `axion.py` - Main `AxionHDL` class coordinates parsing and generation
- **Generators**: `generator.py` (VHDL), `doc_generators.py` (HTML/MD/C/XML/YAML/JSON)
- **Utilities**: `address_manager.py`, `bit_field_manager.py`, `annotation_parser.py`, `code_formatter.py`
- **GUI**: `gui.py` - Flask-based web interface for interactive editing

### Key Data Flow
1. Parsers produce standardized module dictionaries with `registers`, `base_address`, `cdc_enabled`, etc.
2. `AxionHDL.analyze()` collects all modules into `analyzed_modules`
3. Generators consume module dictionaries to produce outputs

## VHDL Annotation Syntax

### Module-level (`@axion_def`)
```vhdl
-- @axion_def BASE_ADDR=0x1000 CDC_EN CDC_STAGE=3
```

### Signal-level (`@axion`)
```vhdl
signal status_reg : std_logic_vector(31 downto 0); -- @axion RO DESC="Status flags"
signal control_reg : std_logic_vector(31 downto 0); -- @axion RW W_STROBE ADDR=0x10
signal data_reg : std_logic_vector(31 downto 0); -- @axion WO R_STROBE W_STROBE
```

**Access modes**: `RO` (read-only), `RW` (read-write), `WO` (write-only)
**Options**: `ADDR=0xNN`, `R_STROBE`, `W_STROBE`, `DESC="..."`, `BIT_OFFSET=N`

## GUI (Web Interface)

Start with `axion-hdl --gui` - opens Flask server on port 5000.

**Features:**
- Dashboard with module listing and statistics
- Interactive register editor (add/edit/delete registers)
- Diff preview before saving changes to source files
- Rule checker for design validation
- Output generation with format toggles

**GUI Dependencies**: `pip install axion-hdl[gui]` (requires Flask>=2.0)

**GUI Requirements**: See `requirements_gui.md` for full GUI test requirements (GUI-LAUNCH, GUI-DASH, GUI-EDIT, GUI-SAVE, GUI-MOD, GUI-GEN, GUI-RULE, GUI-DIFF)

## Requirements Documents

- **`requirements.md`**: Core functional requirements (AXION, AXI-LITE, PARSER, GEN, ERR, CLI, CDC, ADDR, SUB, etc.)
- **`requirements_gui.md`**: GUI-specific requirements (GUI-LAUNCH, GUI-DASH, GUI-EDIT, etc.)

**When adding new features:**
1. Check if a requirement ID exists in these documents
2. If not, add a new requirement with proper ID prefix
3. Ensure your implementation has corresponding tests mapped to requirement IDs

## Testing

### Test Commands
```bash
make dev-install    # Install in editable mode with dev dependencies
make test           # Run all tests (Python, C headers, VHDL simulation)
make test-python    # Run Python unit tests only
make test-vhdl      # Run GHDL simulation tests (requires ghdl)
make test-gui       # Run GUI tests (requires playwright)
```

### Before Committing - MANDATORY
1. **Write tests for new functionality** - every new feature needs tests
2. **Run `make test`** - all core tests must pass
3. **Run `make test-gui`** - if GUI changes were made
4. **Verify test coverage** - ensure tests are comprehensive

### Test Structure
- `tests/python/` - Python unit tests (test_axion.py, test_gui.py, etc.)
- `tests/vhdl/` - VHDL test files with `@axion` annotations
- `tests/vhdl/error_cases/` - Intentionally broken files for error testing
- `tests/yaml/`, `tests/xml/`, `tests/json/` - Input format tests
- `tests/c/` - C header compilation tests

Example test file: `tests/vhdl/sensor_controller.vhd`

## Commit Guidelines

**DO:**
- Write meaningful commit messages describing WHAT and WHY
- Group related changes into logical commits
- Commit files separately by purpose (e.g., separate commits for parser changes vs test changes)
- Use conventional commit format: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`

**DON'T:**
- Commit all files in one giant commit
- Commit generated files (output/, *.pyc, __pycache__)
- Commit with vague messages like "fix" or "update"
- Commit untested code

**Example commits:**
```
feat(parser): add support for DEFAULT attribute in @axion annotations
test(parser): add unit tests for DEFAULT attribute parsing
docs: update README with DEFAULT attribute usage
```

## Code Patterns

### Adding a New Parser
1. Create `xxx_input_parser.py` in `axion_hdl/`
2. Implement `parse_file()` returning same dict structure as `VHDLParser`
3. Add parser instantiation in `axion.py`
4. Add requirement ID to `requirements.md`
5. Write tests in `tests/python/`

### Adding a New Requirement
1. Determine category prefix (AXION, PARSER, GEN, GUI, etc.)
2. Add to `requirements.md` or `requirements_gui.md` with:
   - Unique ID (e.g., `PARSER-009`)
   - Definition
   - Acceptance Criteria
   - Test Method reference
3. Implement the feature
4. Write tests that reference the requirement ID

### Module Dictionary Structure
```python
{
    'name': 'module_name',
    'file': '/path/to/source',
    'base_address': 0x1000,
    'cdc_enabled': True,
    'cdc_stages': 3,
    'registers': [
        {
            'signal_name': 'status_reg',
            'signal_type': '[31:0]',
            'access_mode': 'RO',
            'relative_address_int': 0,
            'read_strobe': False,
            'write_strobe': False,
            'description': 'Status flags'
        }
    ]
}
```

### Error Handling
- Use `AddressConflictError` for address collisions (from `address_manager.py`)
- Use `BitOverlapError` for subregister bit conflicts (from `bit_field_manager.py`)
- Parsers collect errors in `self.errors` list

## Important Conventions

- Signal types use internal format `[high:low]` (e.g., `[31:0]`, `[0:0]`)
- Addresses are 4-byte aligned by default
- Wide signals (>32 bits) auto-split across multiple addresses
- Subregisters pack multiple fields into one 32-bit address using `BIT_OFFSET`
- CDC (Clock Domain Crossing) sync stages default to 2 when enabled

## Dependencies
- Required: `PyYAML>=6.0`
- Optional GUI: `flask>=2.0`
- Dev: `pytest`, `pytest-playwright`, `playwright`, `ghdl` (VHDL sim), `gcc` (C header tests)
