# Developer Guide

Interested in contributing to Axion-HDL? This guide explains the project architecture and how to get started.

## 1. Setup

Clone the repository and install dependencies:

```bash
git clone https://github.com/bugratufan/axion-hdl.git
cd axion-hdl
pip install -r requirements.txt
pip install -e .  # Install in editable mode
```

## 2. Architecture Overview

Axion-HDL follows a pipeline architecture:

1.  **Input Parsing:**
    -   `parser.py`: Parses VHDL `@axion` annotations.
    -   `xml_input_parser.py`: Parses XML.
    -   `yaml_input_parser.py`: Parses YAML.
    -   `json_input_parser.py`: Parses JSON.
    -   These all produce a standard internal `dict` structure representing the module.

2.  **Analysis (`axion.py`):**
    -   `AxionHDL.analyze()`: Orchestrates parsing.
    -   `AddressManager`: Resolves addresses and conflicts.

3.  **Generation:**
    -   `generator.py`: Generates the VHDL AXI Slave (`VHDLGenerator`).
    -   `doc_generators.py`: Handles C headers (`CHeaderGenerator`), Markdown (`DocGenerator`), XML, YAML, and JSON outputs.

## 3. Running Tests

We use `unittest` with a custom runner.

```bash
make test
```

This runs the full suite in `tests/`, covering:
-   Unit tests (Python logic)
-   Integration tests (CLI)
-   VHDL Simulation (requires GHDL)
-   C Compilation (requires GCC)

## 4. Coding Standards

-   Use **Type Hints** for all function signatures.
-   Run `make lint` (if available) or check PEP8 compliance.
-   Add tests for any new feature. Use the `REQUIREMENT-ID` naming convention (e.g., `test_yaml_input_001.py` maps to `YAML-INPUT-001`).

## 5. Adding a New Format

To add support for a new format (e.g., TOML):
1.  Create `toml_input_parser.py` implementing a `parse_file` method.
2.  Update `axion.py` to recognize the file extension.
3.  Add entry to `doc_generators.py` if you want TOML output.
4.  Add tests in `tests/toml/` and `tests/python/test_toml_input.py`.
