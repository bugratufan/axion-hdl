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
outputs
```

```{toctree}
:maxdepth: 2
:caption: Usage Modes

cli-usage
python-api
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

- **Multi-Format Input**: Define registers in VHDL comments, YAML, JSON, XML, or TOML
- **Automated Generation**: One command generates VHDL, C headers, and docs
- **Interactive GUI**: Web-based interface for visual register management
- **Clock Domain Crossing**: Automatic CDC synchronizers
- **Auto-Addressing**: Smart conflict detection and address assignment
- **Rule Checker**: Validate your register definitions before generation

## Three Ways to Use

Axion-HDL can be used in three different ways:

| Mode | Best For | Documentation |
|------|----------|---------------|
| **CLI** | Quick generation, CI/CD pipelines, scripts | [CLI Usage](cli-usage) |
| **Python API** | Custom workflows, integration with other tools | [Python API](python-api) |
| **Web GUI** | Visual editing, exploring register maps | [Interactive GUI](gui) |

## Installation

```bash
pip install axion-hdl
```

For GUI support:

```bash
pip install axion-hdl[gui]
```

## Indices and tables

* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`
