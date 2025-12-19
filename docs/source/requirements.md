# Requirements

Axion-HDL follows a requirements-driven development approach. All features are tracked with requirement IDs and mapped to automated tests.

## Core Requirements

The core tool requirements are documented in the project repository:

**📄 [requirements.md](https://github.com/bugratufan/axion-hdl/blob/develop/requirements.md)**

This document covers:

| Category | Prefix | Description |
|----------|--------|-------------|
| **Core Protocol** | `AXION` | AXI4-Lite register interaction and compliance |
| **Bus Protocol** | `AXI-LITE` | AXI4-Lite handshake and signaling rules |
| **VHDL Parsing** | `PARSER` | Parsing of VHDL entities and `@axion` annotations |
| **YAML Input** | `YAML-INPUT` | Parsing of YAML register definition files |
| **JSON Input** | `JSON-INPUT` | Parsing of JSON register definition files |
| **Code Generation** | `GEN` | Generation of VHDL, C headers, and data formats |
| **Error Handling** | `ERR` | Detection and reporting of conflicts |
| **CLI** | `CLI` | Command-line interface arguments |
| **CDC** | `CDC` | Clock Domain Crossing synchronization |
| **Addressing** | `ADDR` | Automatic and manual address assignment |
| **Stress Testing** | `STRESS` | Handling of large modules and wide signals |
| **Subregisters** | `SUB` | Support for packed registers |
| **Default Values** | `DEF` | Support for reset values |
| **Format Equivalence** | `EQUIV` | Cross-format parsing equivalence |
| **Validation** | `VAL` | Input validation and diagnostics |

---

## GUI Requirements

The GUI-specific requirements are documented separately:

**📄 [requirements_gui.md](https://github.com/bugratufan/axion-hdl/blob/develop/requirements_gui.md)**

This document covers:

| Category | Prefix | Description |
|----------|--------|-------------|
| **Server Launch** | `GUI-LAUNCH` | GUI server startup and browser opening |
| **Dashboard** | `GUI-DASH` | Module listing and summary display |
| **Editor** | `GUI-EDIT` | Register editing functionality |
| **Save & Changes** | `GUI-SAVE` | Unsaved changes tracking and warnings |
| **File Modification** | `GUI-MOD` | YAML/JSON/XML/VHDL file modification |
| **Generation** | `GUI-GEN` | Output generation interface |
| **Rule Check** | `GUI-RULE` | Design rule checking interface |
| **Diff/Review** | `GUI-DIFF` | Change preview and confirmation |
| **Navigation** | `GUI-NAV` | Site navigation and layout |

---

## Test Mapping

Each requirement ID maps to automated tests:

### Python Unit Tests

```bash
make test-python
```

Tests are located in `tests/python/` and reference requirement IDs:

```python
def test_parser_001():
    """PARSER-001: Basic entity name extraction"""
    # Test implementation
```

### VHDL Simulation Tests

```bash
make test-vhdl
```

Tests are located in `tests/vhdl/` and verify hardware behavior.

### GUI Tests

```bash
make test-gui
```

Playwright browser tests verify GUI requirements.

---

## Requirement Format

Each requirement follows this structure:

| Field | Description |
|-------|-------------|
| **ID** | Unique identifier (e.g., `AXION-001`) |
| **Definition** | What the requirement specifies |
| **Acceptance Criteria** | How to verify compliance |
| **Test Method** | Reference to automated test |

### Example

```markdown
| ID | Definition | Acceptance Criteria | Test Method |
|----|------------|---------------------|-------------|
| AXION-001 | Read-Only Register Read Access | A read transaction to a RO register address must return the signal value. | VHDL Simulation (`vhdl.req.axion_001`) |
```

---

## Adding New Requirements

When adding new features:

1. **Check existing requirements** - May already be covered
2. **Determine category** - Use appropriate prefix
3. **Assign next ID** - Sequential within category
4. **Write definition** - Clear and testable
5. **Add acceptance criteria** - Measurable outcome
6. **Reference test method** - How it will be verified
7. **Implement feature** - Code the functionality
8. **Write tests** - Map to requirement ID

---

## Viewing Full Requirements

For the complete requirements documentation with all details:

- **Core Requirements:** See [requirements.md](https://github.com/bugratufan/axion-hdl/blob/develop/requirements.md) in the repository
- **GUI Requirements:** See [requirements_gui.md](https://github.com/bugratufan/axion-hdl/blob/develop/requirements_gui.md) in the repository

These files are the authoritative source and are updated alongside the codebase.
