# Axion-HDL Documentation

Welcome to the **Axion-HDL** documentation!

Axion-HDL is a powerful Python-based automation tool that generates AXI4-Lite register interfaces for VHDL modules.

## Quick Links

```{toctree}
:maxdepth: 2
:caption: User Guide

getting-started
data-formats
examples
cli-reference
outputs
```

```{toctree}
:maxdepth: 2
:caption: Tools

gui
rule-checker
```

```{toctree}
:maxdepth: 2
:caption: Reference

requirements
developer-guide
api-reference
```

## Features

- **Multi-Format Input**: Define registers in VHDL comments, YAML, JSON, or XML
- **Automated Generation**: One command generates VHDL, C headers, and docs
- **Interactive GUI**: Web-based interface for visual register management
- **Clock Domain Crossing**: Automatic CDC synchronizers
- **Auto-Addressing**: Smart conflict detection and address assignment
- **Rule Checker**: Validate your register definitions before generation

## Installation

```bash
pip install axion-hdl
```

## Indices and tables

* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`
