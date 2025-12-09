# Welcome to the Axion-HDL Wiki

**Axion-HDL** is a powerful Python-based automation tool designed to streamline the creation of AXI4-Lite register interfaces for VHDL Modules. It eliminates the manual drudgery of writing register maps, address decoders, and C headers, letting you focus on the core logic of your FPGA designs.

[![PyPI version](https://badge.fury.io/py/axion-hdl.svg)](https://badge.fury.io/py/axion-hdl)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Key Features

- **Multi-Format Input:** Define your registers where you prefer:
    - **VHDL Comments:** Keep documentation close to code with `@axion` tags.
    - **YAML / JSON:** Use modern, human-readable data formats.
    - **XML:** Compatible with legacy workflows.
- **Automated Generation:** One command to generate:
    - Synthesizable **VHDL** AXI4-Lite slaves.
    - **C Header** files for firmware development.
    - **HTML/Markdown** documentation.
    - **IP-XACT** compatible XML.
- **Advanced Capabilities:**
    - **Automatic CDC:** Built-in Clock Domain Crossing handling.
    - **Sub-registers:** Bit-level field definitions and packed registers.
    - **Auto-Addressing:** Conflict detection and automatic address assignment.
    - **Wide Signals:** Support for signals larger than 32 bits (spanning multiple registers).

## 📚 Documentation Index

- **[Getting Started](Getting_Started.md)**: Installation and your first project.
- **[Data Formats](Data_Formats.md)**: Detailed guide to VHDL, YAML, JSON, and XML inputs.
- **[CLI Reference](CLI_Reference.md)**: Command-line options and flags.
- **[Outputs & Integration](Outputs.md)**: How to use the generated VHDL and C files.
- **[Advanced Features](Advanced_Features.md)**: CDC, sub-registers, and address management.
- **[Developer Guide](Developer_Guide.md)**: Contributing to Axion-HDL.

## 🤔 Why Axion-HDL?

Writing AXI4-Lite slaves manually is error-prone. One typo in an address offset can lead to hours of debugging. Axion-HDL ensures your **VHDL logic**, **C firmware headers**, and **Documentation** are always synchronized. Change a register in your source, run `axion-hdl`, and everything updates instantly.
