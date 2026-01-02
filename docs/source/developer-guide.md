# Developer Guide

This guide covers the development workflow, project structure, and contribution guidelines for Axion-HDL.

## Project Structure

```
axion-hdl/
├── axion_hdl/              # Main Python package
│   ├── __init__.py         # Package initialization, version
│   ├── axion.py            # Core AxionHDL class
│   ├── cli.py              # Command-line interface
│   ├── parser.py           # VHDL parser (@axion annotations)
│   ├── yaml_parser.py      # YAML register definition parser
│   ├── json_parser.py      # JSON register definition parser  
│   ├── xml_parser.py       # XML register definition parser
│   ├── rule_checker.py     # Design rule validation
│   ├── gui.py              # Flask-based web GUI
│   ├── templates/          # HTML templates for GUI
│   ├── static/             # CSS, JS for GUI
│   └── generators/         # Output generators
│       ├── vhdl_generator.py
│       ├── c_header_generator.py
│       ├── doc_generator.py
│       ├── xml_generator.py
│       ├── yaml_generator.py
│       └── json_generator.py
├── tests/                  # Test suite
│   ├── python/             # Python unit tests
│   ├── vhdl/               # VHDL simulation tests
│   └── run_tests.py        # Test runner
├── docs/                   # Documentation (Sphinx)
│   ├── source/             # Markdown source files
│   ├── requirements/       # Requirements specifications
│   └── examples/           # Example input files
├── pyproject.toml          # Package configuration
├── Makefile                # Build and test automation
└── .version                # Version file
```

---

## Development Setup

### Prerequisites

- Python 3.7+
- pip
- (Optional) GHDL for VHDL simulation tests
- (Optional) Node.js for Playwright GUI tests

### Installation

Clone the repository and install in development mode:

```bash
git clone https://github.com/bugratufan/axion-hdl.git
cd axion-hdl
pip install -e ".[dev]"
```

For GUI development:

```bash
pip install -e ".[dev,gui]"
```

For documentation:

```bash
pip install -e ".[docs]"
```

---

## Running Tests

### All Tests

```bash
make test
```

### Python Unit Tests

```bash
make test-python
```

Runs pytest on `tests/python/`. Tests are organized by requirement category:

- `test_parser.py` - PARSER-xxx requirements
- `test_generator.py` - GEN-xxx requirements
- `test_cli.py` - CLI-xxx requirements
- `test_addressing.py` - ADDR-xxx requirements
- etc.

### VHDL Simulation Tests

```bash
make test-vhdl
```

Requires GHDL. Runs simulation tests in `tests/vhdl/` to verify:

- AXI4-Lite protocol compliance (AXION-xxx, AXI-LITE-xxx)
- Register read/write behavior
- CDC synchronization

### GUI Tests (Playwright)

```bash
make test-gui
```

Requires Playwright. Install browsers first:

```bash
playwright install chromium
```

Tests GUI requirements (GUI-xxx) including:

- Dashboard functionality
- Editor interactions
- Save/diff workflows

---

## Branching Workflow

This project uses a `develop` → `main` branching strategy.

### Feature Development

1. Start from `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   ```

2. Create feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. Make changes and commit:
   ```bash
   git add .
   git commit -m "feat: your commit message"
   ```

4. Push and create PR to `develop`:
   ```bash
   git push -u origin feature/your-feature-name
   ```

### Releases

PyPI publishes happen when `develop` is merged into `main`:

1. Ensure version is updated in:
   - `.version`
   - `pyproject.toml`
   - `setup.py`
   - `axion_hdl/__init__.py`

2. Create PR from `develop` to `main`

3. After merge, CI automatically:
   - Runs tests
   - Builds package
   - Creates GitHub release
   - Publishes to PyPI

---

## Code Style

### Python

- Use [Black](https://black.readthedocs.io/) for formatting
- Line length: 100 characters
- Run before committing:
  ```bash
  black axion_hdl tests
  ```

### Linting

```bash
flake8 axion_hdl tests
```

---

## Adding New Features

### 1. Check Requirements

Review existing requirements in:
- `docs/source/requirements-core.md`
- `docs/source/requirements-gui.md`

Your feature may already be covered or need a new requirement.

### 2. Add Requirement

If new, add to appropriate requirements document:

```markdown
| ID | Definition | Acceptance Criteria | Test Method |
|----|------------|---------------------|-------------|
| CAT-XXX | Feature description | How to verify | Test reference |
```

### 3. Write Tests First

Add tests in `tests/python/` referencing the requirement:

```python
def test_cat_xxx():
    """CAT-XXX: Feature description"""
    # Test implementation
    assert expected_behavior
```

### 4. Implement Feature

Write the implementation in the appropriate module.

### 5. Run Tests

```bash
make test
```

### 6. Update Documentation

If user-facing, update docs in `docs/source/`.

---

## Building Documentation

### Local Build

```bash
cd docs
make html
```

View at `docs/build/html/index.html`.

### ReadTheDocs

Documentation is automatically built on ReadTheDocs when changes are pushed.

---

## Useful Make Targets

| Target | Description |
|--------|-------------|
| `make test` | Run all tests |
| `make test-python` | Python unit tests only |
| `make test-vhdl` | VHDL simulation tests only |
| `make test-gui` | Playwright GUI tests only |
| `make lint` | Run flake8 linting |
| `make format` | Format code with black |
| `make build` | Build distribution package |
| `make clean` | Clean build artifacts |
| `make generate-docs` | Generate HTML documentation |
