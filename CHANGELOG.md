# Changelog

All notable changes to Axion-HDL will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2024-12-04

### Added

#### Comprehensive Test Suite Expansion
- **New Test Categories**: Added 8 new test modules covering all requirement categories
  - `test_parser.py` - PARSER-001 to PARSER-008 (20 tests)
  - `test_generator.py` - GEN-001 to GEN-012 (30 tests)
  - `test_cli.py` - CLI-001 to CLI-010 (11 tests)
  - `test_error_handling.py` - ERR-001 to ERR-006 (9 tests)
  - `test_cdc.py` - CDC-001 to CDC-007 (8 tests)
  - `test_addr.py` - ADDR-001 to ADDR-008 (9 tests)
  - `test_stress.py` - STRESS-001 to STRESS-006 (6 tests)

- **Test Coverage Summary**: 
  - Total tests: 168 (all passing)
  - Requirements covered: 108 unique IDs (including sub-variants)
  - Base requirements: 98 (94% coverage)

#### Enhanced Test Runner
- **Category-based Reporting**: TEST_RESULTS.md now shows tests grouped by category
  - Python, C, VHDL, PARSER, GEN, ERR, CLI, CDC, ADDR, STRESS sections
- **Requirement Coverage Summary**: New summary showing coverage by category
- **Improved Output**: Better terminal output with category-based grouping

#### Parser Improvements
- **Public `parse_file()` Method**: Added for direct file parsing in tests
- **Improved Width Extraction**: Better handling of std_logic_vector parsing

#### API Enhancements  
- **`get_modules()` Method**: New method to retrieve parsed modules for inspection

### Changed
- **Requirements Documentation**: Updated requirements.md with:
  - Expanded to 98 requirements across 19 categories
  - Test Coverage Matrix with status for each requirement
  - Coverage Statistics (94% complete, 92/98 requirements)
  - Updated Next Steps section

### Fixed
- **Test Infrastructure**: Fixed setUpClass handling for generator/cli/stress/cdc/addr tests
- **Category Display**: Fixed CDC and ADDR sections not appearing in TEST_RESULTS.md

## [0.3.0] - 2024-12-04

### Added

#### Register Description Support (DESC Attribute)
- **DESC Attribute**: Add human-readable descriptions to register annotations
  - Syntax: `-- @axion RO DESC="System status flags"`
  - Supports quoted strings with spaces
  - Descriptions appear in all generated outputs

- **Documentation Integration**:
  - Markdown: Description column in register table, italicized in Port Descriptions
  - C Header: Comments on offset definitions and struct members
  - XML (IP-XACT): `<spirit:description>` element for each register
  - VHDL: Comments on port signal declarations

#### Address Conflict Detection
- **AddressConflictError Exception**: New exception class with detailed error reporting
  - Shows conflicting register names (existing and new)
  - Displays module name where conflict occurred
  - Lists violated requirements (AXION-006, AXION-007, AXION-008)
  - Suggests solution with corrected address

- **Wide Signal Overlap Detection**: Detects conflicts when wide signals (>32 bits) overlap with other registers

#### Exclude Patterns (File/Directory Filtering)
- **Python API**: New methods for exclusion management
  - `exclude(*patterns)` - Add exclusion patterns
  - `include(*patterns)` - Remove exclusion patterns  
  - `clear_excludes()` - Clear all exclusions
  - `list_excludes()` - List current exclusions

- **Pattern Types Supported**:
  - File names: `"test.vhd"`
  - Directory names: `"testbenches"`
  - Glob patterns: `"*_tb.vhd"`, `"test_*.vhd"`

- **CLI Support**: New `-e/--exclude` option
  - Example: `axion-hdl -s ./src -e "error_cases" -e "*_tb.vhd"`

#### Test Suite
- **Address Conflict Tests**: New test file `tests/python/test_address_conflict.py`
  - Basic address conflict detection
  - No false positives with unique addresses
  - Wide signal address overlap detection
- **Error Test Cases**: New directory `tests/vhdl/error_cases/` for intentionally broken files

### Changed
- Parser now tracks signal names per address for conflict detection
- AddressManager accepts module_name parameter for better error messages
- Makefile updated with `test-address-conflict` target

## [0.2.0] - 2024-12-04

### Added

#### Mixed Signal Width Support (AXION-025/026)
- **Wide Signal Support**: Full support for signals wider than 32 bits (up to 200+ bits tested)
  - 48-bit, 64-bit, 100-bit, and 200-bit signals verified in simulation
  - Automatic multi-register allocation for wide signals
  - Sequential address assignment for register banks (REG0, REG1, REG2, etc.)
  
- **Narrow Signal Support**: Full support for signals narrower than 32 bits
  - 1-bit, 6-bit, 8-bit, 16-bit signals verified in simulation
  - Proper bit masking in generated code
  
- **Multi-Register Access**: Wide signals accessible via multiple AXI transactions
  - Each 32-bit portion at sequential addresses (BASE+0x00, BASE+0x04, etc.)
  - Lower bits in lower address, upper bits in higher addresses

#### C Header Enhancements
- **Signal Width Definitions**: New macros for multi-register signals
  - `*_WIDTH` - Total signal width in bits
  - `*_NUM_REGS` - Number of 32-bit registers required
- **Register Comments**: Documentation comments indicating signal width and register part
- **Multi-Register Offsets**: Individual offset macros for each register part (REG0, REG1, etc.)

#### VHDL Generator Improvements
- **Address Validation**: Automatic detection of overlapping multi-register addresses
- **Address Map Integrity**: Correct address calculation for registers following wide signals
- **Register Part Comments**: Clear documentation in generated code for multi-register signals

#### Test Suite Expansion
- **13 New AXION Tests**: AXION-025a through AXION-026f for wide/narrow signal support
- **Test Reorganization**: AXION-025/026 tests integrated as AXION requirements (after AXION-024)
- **Total Test Count**: 53 tests (37 AXION requirements + 16 AXI-LITE protocol tests)

### Changed
- Test structure reorganized: AXION tests (1-37), AXI-LITE tests (38-53)
- Mixed-width controller added to test suite for comprehensive signal width testing

### Technical Details
- Wide signals split into ceil(width/32) registers
- Each register occupies 4 bytes (32 bits) in address space
- Unused upper bits in final register are zero-padded
- Multi-register signals maintain atomic read consistency per register

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

[0.2.0]: https://github.com/bugratufan/axion-hdl/releases/tag/v0.2.0
[0.1.1]: https://github.com/bugratufan/axion-hdl/releases/tag/v0.1.1
[0.1.0]: https://github.com/bugratufan/axion-hdl/releases/tag/v0.1.0
