# Welcome to the Axion-HDL Wiki

[![PyPI version](https://badge.fury.io/py/axion-hdl.svg)](https://badge.fury.io/py/axion-hdl)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://github.com/bugratufan/axion-hdl/actions/workflows/python-app.yml/badge.svg)](https://github.com/bugratufan/axion-hdl/actions)

**Axion-HDL** is a powerful Python-based automation tool designed to streamline the creation of AXI4-Lite register interfaces for VHDL Modules. It eliminates the manual drudgery of writing register maps, address decoders, and C headers, letting you focus on the core logic of your FPGA designs.

## 🚀 Key Features

- **Multi-Format Input:** Define your registers where you prefer:
    - **VHDL Comments:** Keep documentation close to code with `@axion` tags.
    - **YAML / JSON:** Use modern, human-readable data formats.
    - **XML:** Compatible with legacy workflows.
- **Automated Generation:** One command to generate:
    - Synthesizable **VHDL** AXI4-Lite slaves.
    - **C Header** files for firmware development.
    - **HTML/Markdown** documentation.
- **Advanced Logic:**
    - **CDC:** Automatic Clock Domain Crossing synchronizers.
    - **Auto-Addressing:** Smart conflict detection and address assignment.

## 🔗 Quick Links

- [**Getting Started**](Getting_Started): Install and run your first example in 5 minutes.
- [**CLI Reference**](CLI_Reference): Master the command-line interface.
- [**Data Formats**](Data_Formats): Detail guide on VHDL, YAML, JSON specs.

## 🤔 Why Axion-HDL?

| Feature | Axion-HDL | Traditional Hand-Coding |
| :--- | :--- | :--- |
| **Speed** | ⚡ Instant | 🐢 Slow & Error-prone |
| **Sync** | ✅ Always in sync (Single Source) | ❌ Headers/HDL often diverge |
| **Logic** | ✅ Auto CDC & Strobes | ❌ Manual boilerplate |
| **Docs** | ✅ Auto-generated | ❌ Often missing/stale |

Writing AXI4-Lite slaves manually is error-prone. One typo in an address offset can lead to hours of debugging. Axion-HDL ensures your **VHDL logic**, **C firmware headers**, and **Documentation** are always synchronized.
