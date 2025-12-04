# Changelog

All notable changes to Axion-HDL will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2024-12-04

### Fixed

#### CDC Implementation
- **CDC Synchronization Process**: Fixed missing CDC synchronization process in generated VHDL code. Previously, CDC sync signals were declared but never used.
- **RO Register CDC**: Read-only registers now properly synchronize input signals through the CDC chain before being read by AXI
- **WO/RW Register CDC**: Write-only and read-write register outputs now properly pass through CDC synchronization before reaching the module

#### Testbench Improvements
- **AXI Write Procedure Fix**: Fixed deadlock issue in testbench AXI write procedures where `awready` and `wready` could be asserted simultaneously but were being waited for sequentially
- **Multiple Procedure Fixes**: Applied same fix to `axi_write_delayed_bready` and `axi_write_early_bready` procedures
- **Simulation Time**: Increased default simulation stop-time from 100us to 20ms to allow all 40 tests to complete

### Technical Details
- Added `_generate_cdc_process()` method to generator for proper CDC synchronization
- CDC now uses 3-stage synchronization by default (configurable via `CDC_STAGE`)
- RO registers: `module_clk → axi_aclk` synchronization
- WO/RW registers: `axi_aclk → module_clk` synchronization

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

[0.1.1]: https://github.com/bugratufan/axion-hdl/releases/tag/v0.1.1
[0.1.0]: https://github.com/bugratufan/axion-hdl/releases/tag/v0.1.0
