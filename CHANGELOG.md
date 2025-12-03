# Changelog

All notable changes to Axion-HDL will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-12-03

### Added

#### Core Features
- **VHDL Parser**: Parse VHDL files and extract `@axion` annotations from signal declarations
- **AXI4-Lite Generator**: Generate fully protocol-compliant AXI4-Lite slave register interface modules
- **C Header Generator**: Generate C header files with module-prefixed register definitions
- **XML Generator**: Generate IP-XACT compatible XML register map descriptions
- **Documentation Generator**: Generate Markdown register map documentation

#### Annotation System
- `@axion_def` module-level annotation for base address and CDC configuration
- `@axion` signal-level annotation with access mode (RO, WO, RW)
- Automatic address assignment with 4-byte alignment
- Manual address specification with `ADDR=0xXX`
- Read strobe support with `R_STROBE` flag
- Write strobe support with `W_STROBE` flag

#### AXI4-Lite Protocol Compliance
- Independent write address and data channels (AXI-LITE-005)
- Proper VALID/READY handshaking
- BRESP/RRESP response signaling (OKAY/SLVERR)
- Address alignment checking with SLVERR for invalid addresses
- Byte-level write strobe (WSTRB) support
- Single-cycle response capability
- Proper reset behavior (AXI-LITE-001)

#### Clock Domain Crossing (CDC)
- Optional CDC support with `CDC_EN` flag
- Configurable synchronizer stages with `CDC_STAGE=N`
- Default 2-stage synchronization

#### Command Line Interface
- `axion-hdl` CLI command with intuitive options
- Multiple source directory support (`-s` can be repeated)
- Selective output generation (`--vhdl`, `--c-header`, `--xml`, `--doc`)
- All outputs generation with `--all` flag
- Documentation format selection (`--doc-format md|html|pdf`)

#### Python API
- `AxionHDL` main class for programmatic usage
- `VHDLParser` for parsing VHDL files
- `VHDLGenerator` for generating VHDL code
- `CHeaderGenerator`, `XMLGenerator`, `DocGenerator` for other outputs
- `AddressManager` for address allocation
- `AnnotationParser` for parsing annotations
- `VHDLUtils` and `CodeFormatter` utility classes

### Technical Details

- Pure Python implementation with no external dependencies
- Python 3.7+ compatibility
- MIT License
- Comprehensive test suite (Python, C, VHDL)

---

## Future Plans

- [ ] HTML and PDF documentation output
- [ ] Bit-field support within registers
- [ ] Register arrays
- [ ] Interrupt support
- [ ] AXI4-Full interface option
- [ ] SystemVerilog output
- [ ] GUI interface

[0.1.0]: https://github.com/bugratufan/axion-hdl/releases/tag/v0.1.0
