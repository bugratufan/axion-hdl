# Axion-HDL Requirements

This document tracks all functional and non-functional requirements for the Axion-HDL project.
Testing and verification are automated via `make test`, which maps tests back to these requirement IDs.

## Requirement Categories

| Prefix | Category | Definition |
|--------|----------|------------|
| **AXION** | Core Protocol | Core AXI4/AXI4-Lite register interaction and compliance. |
| **AXI-LITE** | Bus Protocol | Specific AXI4-Lite handshake and signaling rules. |
| **PARSER** | VHDL Parsing | Parsing of VHDL entities, signals, and `@axion` annotations. |
| **YAML-INPUT** | YAML Parsing | Parsing of YAML register definition files. |
| **JSON-INPUT** | JSON Parsing | Parsing of JSON register definition files. |
| **GEN** | Code Generation | Generation of VHDL register wrappers, C headers, and data formats. |
| **ERR** | Error Handling | Detection and reporting of invalid configurations or conflicts. |
| **CLI** | Interface | Command-line interface arguments and behavior. |
| **CDC** | Clock Crossing | Clock Domain Crossing synchronization logic. |
| **ADDR** | Addressing | Automatic and manual register address assignment. |
| **STRESS** | Performance | Handling of large modules, wide signals, and massive generation. |
| **SUB** | Subregisters | Support for packed registers (multiple fields in one 32-bit word). |
| **DEF** | Default Values | Support for reset values via `DEFAULT` attribute. |
| **EQUIV** | Format Equivalence | Cross-format parsing and output equivalence. |

---

## 1. Core Protocol (AXION)

| ID | Definition | Acceptance Criteria | Test Method |
|----|------------|---------------------|-------------|
| AXION-001 | Read-Only Register Read Access | A read transaction to a RO register address must return the signal value. | VHDL Simulation (`vhdl.req.axion_001`) |
| AXION-002 | Read-Only Register Write Protection | A write transaction to a RO register address must be ignored (no signal change). | VHDL Simulation (`vhdl.req.axion_002`) |
| AXION-003 | Write-Only Register Write Access | A write transaction to a WO register address must update the signal value. | VHDL Simulation (`vhdl.req.axion_003`) |
| AXION-004 | Write-Only Register Read Protection | A read transaction to a WO register address must return 0x00000000 (or predictable value). | VHDL Simulation (`vhdl.req.axion_004`) |
| AXION-005 | Read-Write Register Full Access | RW registers must be readable (return current value) and writable (update value). | VHDL Simulation (`vhdl.req.axion_005`) |
| AXION-006 | Register Address Mapping | Registers must be mapped to their assigned offset addresses relative to base. | VHDL Simulation (`vhdl.req.axion_006`) |
| AXION-007 | Base Address Offset Calculation | The module base address must be added to the register offset for final addressing. | VHDL Simulation (`vhdl.req.axion_007`) |
| AXION-008 | Module Address Space Isolation | Transactions outside the module's address range must be ignored or pass-through. | VHDL Simulation (`vhdl.req.axion_008`) |
| AXION-009 | AXI Write Response Error Signaling | Write errors (e.g. invalid address) must assert BRESP with SLVERR. | VHDL Simulation (`vhdl.req.axion_009`) |
| AXION-010 | AXI Read Response Error Signaling | Read errors must assert RRESP with SLVERR. | VHDL Simulation (`vhdl.req.axion_010`) |
| AXION-011 | AXI Write Transaction Handshake | AWVALID/AWREADY, WVALID/WREADY, BVALID/BREADY handshakes must complete correctly. | VHDL Simulation (`vhdl.req.axion_011`) |
| AXION-012 | AXI Read Transaction Handshake | ARVALID/ARREADY, RVALID/RREADY handshakes must complete correctly. | VHDL Simulation (`vhdl.req.axion_012`) |
| AXION-013 | Read Strobe Signal Generation | Read strobe must assert for 1 cycle when a register is read. | VHDL Simulation (`vhdl.req.axion_013`) |
| AXION-014 | Write Strobe Signal Generation | Write strobe must assert for 1 cycle when a register is written. | VHDL Simulation (`vhdl.req.axion_014`) |
| AXION-015 | Write Enable Signal Generation | Write enable must assert on valid write data. | VHDL Simulation (`vhdl.req.axion_015`) |
| AXION-016 | Byte-Level Write Strobe Support | Partial writes (via WSTRB) must update only appropriate bytes. | VHDL Simulation (`vhdl.req.axion_016`) |
| AXION-017 | Synchronous Reset | Signal reset must occur synchronously on rising clock edge when reset_n is low. | VHDL Simulation (`vhdl.req.axion_017`) |
| AXION-018 | Clock Domain Crossing | Signals crossing domains must pass through synchronizers (if enabled). | VHDL Simulation (`vhdl.req.axion_018`) |
| AXION-019 | Documentation Generation | Helper documentation must be generated for register map. | VHDL Simulation (`vhdl.req.axion_019`) |
| AXION-020 | Unaligned Address Access | Access to unaligned addresses (not 4-byte boundaries) should error or align. | VHDL Simulation (`vhdl.req.axion_020`) |
| AXION-021 | Out-of-Range Address Access | Access to undefined offsets within base range returns SLVERR or DECERR. | VHDL Simulation (`vhdl.req.axion_021`) |
| AXION-022 | Concurrent Read and Write Operations | Simultaneous Read and Write channels must operate independently. | VHDL Simulation (`vhdl.req.axion_022`) |
| AXION-023 | Default Register Values | Registers must initialize to defined default values on reset. | VHDL Simulation (`vhdl.req.axion_023`) |
| AXION-024 | Register Bit Field Support | Partial field updates must preserve other bits in the register. | VHDL Simulation (`vhdl.req.axion_024`) |
| AXION-025 | Wide Signal Support | Signals >32 bits must span multiple consecutive registers. | VHDL Simulation (`vhdl.req.axion_025x`) |
| AXION-026 | Multi-register access | Reads/Writes to parts of wide signals must correctly update specific bits. | VHDL Simulation (`vhdl.req.axion_026x`) |
| AXION-027 | Existing File Overwrite | The tool must overwrite existing files in the output directory. | Python Unit Test (`python.gen.overwrite`) |

## 2. Bus Protocol (AXI-LITE)

| ID | Definition | Acceptance Criteria | Test Method |
|----|------------|---------------------|-------------|
| AXI-LITE-001 | Reset State Requirements | On reset, outgoing valid/ready signals must be deasserted. | VHDL Simulation (`vhdl.req.axi_lite_001`) |
| AXI-LITE-002 | Single Transfer Per Transaction | AXI-Lite does not support burst; burst length is always 1. | VHDL Simulation (`vhdl.req.axi_lite_002`) |
| AXI-LITE-003 | VALID Before READY Dependency | VALID signals must not depend on READY signals to be asserted. | VHDL Simulation (`vhdl.req.axi_lite_003`) |
| AXI-LITE-004 | VALID Stability Rule | Once VALID is asserted, it must remain high until READY is asserted. | VHDL Simulation (`vhdl.req.axi_lite_004`) |
| AXI-LITE-005 | Write Address/Data Independence | Core must accept Address and Data phases in any order. | VHDL Simulation (`vhdl.req.axi_lite_005`) |
| AXI-LITE-006 | Back-to-Back Transaction Support | Core handles transactions arriving immediately after previous one completes. | VHDL Simulation (`vhdl.req.axi_lite_006`) |
| AXI-LITE-007 | Write Response Timing | BRESP must not be asserted until both WVALID and AWVALID have arrived. | VHDL Simulation (`vhdl.req.axi_lite_007`) |
| AXI-LITE-008 | Read Response Timing | RVALID must not be asserted until ARVALID has arrived. | VHDL Simulation (`vhdl.req.axi_lite_008`) |
| AXI-LITE-014 | Response Code Compliance | OKAY for success, SLVERR/DECERR for errors. | VHDL Simulation (`vhdl.req.axi_lite_014`) |
| AXI-LITE-015 | Clock Edge Alignment | All outputs change on rising clock edge. | VHDL Simulation (`vhdl.req.axi_lite_015`) |
| AXI-LITE-016 | Delayed READY Handling | Core waits indefinitely for READY to be asserted by master/slave. | VHDL Simulation (`vhdl.req.axi_lite_016`) |
| AXI-LITE-017 | Early READY Handling | Core can assert READY before VALID is asserted. | VHDL Simulation (`vhdl.req.axi_lite_017`) |

## 3. VHDL Parsing (PARSER)

| ID | Definition | Acceptance Criteria | Test Method |
|----|------------|---------------------|-------------|
| PARSER-001 | Basic entity name extraction and whitespace handling | Parser correctly identifies `entity <name>` regardless of whitespace. | Python Unit Test (`parser.test_parser_001`) |
| PARSER-002 | Parse std_logic and std_logic_vector types | Correctly identifies signal width (1 for std_logic, N for vector). | Python Unit Test (`parser.test_parser_002`) |
| PARSER-003 | Parse Access Modes and strobe flags | extracts RW/RO/WO and R_STROBE/W_STROBE from `@axion` comments. | Python Unit Test (`parser.test_parser_003`) |
| PARSER-004 | Parse Attributes | Extracts `BASE_ADDR`, `CDC_EN` (flag/kv), `CDC_STAGE` key-values. | Python Unit Test (`parser.test_parser_004`) |
| PARSER-005 | Parse Hex/Decimal addresses | Handles `0x10` and `16` as valid address inputs. | Python Unit Test (`parser.test_parser_005`) |
| PARSER-006 | Parse Descriptions | Extracts description string from comments, handling quotes. | Python Unit Test (`parser.test_parser_006`) |
| PARSER-007 | Exclude directories | Skips directories specified in exclude list. | Python Unit Test (`parser.test_parser_007`) |
| PARSER-008 | Recursive scanning | Recursively finds `.vhd` files in subfolders. | Python Unit Test (`parser.test_parser_008`) |

## 4. Code Generation (GEN)

| ID | Definition | Acceptance Criteria | Test Method |
|----|------------|---------------------|-------------|
| GEN-001 | VHDL Entity Naming and File Generation | Output file is named `<module>_axion_reg.vhd` and can be compiled. | Python Unit Test (`gen.test_gen_001`) |
| GEN-002 | Architecture RTL and Signal Declarations | Defines `architecture rtl` and declares necessary internal signals. | Python Unit Test (`gen.test_gen_002`) |
| GEN-003 | AXI Channel Signal Generation | Generates all standard AXI4-Lite interface ports. | Python Unit Test (`gen.test_gen_003`) |
| GEN-004 | Register Direction (IN/OUT) | RO signals mapped to inputs, internal regs mapped to outputs. | Python Unit Test (`gen.test_gen_004`) |
| GEN-005 | Read Strobe Port Generation | Generates output port `<signal>_rd_strobe` if requested. | Python Unit Test (`gen.test_gen_005`) |
| GEN-006 | Write Strobe Port Generation | Generates output port `<signal>_wr_strobe` if requested. | Python Unit Test (`gen.test_gen_006`) |
| GEN-007 | State Machine Logic | Includes AXI state machine (Idle, Read, Write, Resp). | Python Unit Test (`gen.test_gen_007`) |
| GEN-008 | Address Decoder Logic | Generates `case` statement for address decoding. | Python Unit Test (`gen.test_gen_008`) |
| GEN-009 | C Header Generation | Generates valid `.h` file with offset macros and structs. | Python Unit Test (`gen.test_gen_009`) |
| GEN-010 | C Struct Definition | Generates typedef struct representing register map. | Python Unit Test (`gen.test_gen_010`) |
| GEN-011 | XML Map Generation | Generates `.xml` file describing the register map. | Python Unit Test (`gen.test_gen_011`) |
| GEN-012 | Markdown Documentation Generation | Generates `.md` file with register tables. | Python Unit Test (`gen.test_gen_012`) |
| GEN-013 | YAML Map Generation | Generates `{module}_regs.yaml` with valid YAML syntax. | Python Unit Test (`gen.test_gen_013`) |
| GEN-014 | JSON Map Generation | Generates `{module}_regs.json` with valid JSON syntax. | Python Unit Test (`gen.test_gen_014`) |
| GEN-015 | HTML Documentation Generation | Generates styled `register_map.html` with embedded CSS. | Python Unit Test (`gen.test_gen_015`) |
| GEN-016 | PDF Documentation Generation | Generates `register_map.pdf` file (optional, requires weasyprint). | Python Unit Test (`gen.test_gen_016`) |
| GEN-017 | Address Range Calculation | Calculates and displays address range (start-end) for each module. | Python Unit Test (`gen.test_gen_017`) |
| GEN-018 | Base Address Generic | VHDL entity includes `BASE_ADDR` generic used for offset calculation. | Python Unit Test (`gen.test_gen_018`) |

## 5. Error Handling (ERR)

| ID | Definition | Acceptance Criteria | Test Method |
|----|------------|---------------------|-------------|
| ERR-001 | Address Conflict Detection | Raises `AddressConflictError` if two registers share an address. | Python Unit Test (`err.test_err_001`) |
| ERR-002 | Non-VHDL/Binary File Handling | Gracefully skips non-text files without crashing. | Python Unit Test (`err.test_err_002`) |
| ERR-003 | Skipped Files | Skips files missing `@axion` or valid entities. | Python Unit Test (`err.test_err_003`) |
| ERR-004 | Invalid Hex Address Reporting | Reports error for malformed hex strings. | Python Unit Test (`err.test_err_004`) |
| ERR-005 | No Entity Declaration Handling | Handles files missing entity declarations. | Python Unit Test (`err.test_err_005`) |
| ERR-006 | Duplicate Signal Detection | Detects and reports duplicate signal names within a module. | Python Unit Test (`err.test_err_006`) |
| ERR-007 | Address Overlap Detection | Warns when multiple modules have overlapping address ranges. | Python Unit Test (`err.test_err_007`) |

## 6. Command Line Interface (CLI)

| ID | Definition | Acceptance Criteria | Test Method |
|----|------------|---------------------|-------------|
| CLI-001 | Help Options (-h, --help) | Prints usage information and exits with 0. | Python Unit Test (`cli.test_cli_001`) |
| CLI-002 | Version Option (--version) | Prints tool version and exits with 0. | Python Unit Test (`cli.test_cli_002`) |
| CLI-003 | Source Path Options (-s, --source) | Accepts source files (.vhd, .vhdl, .xml, .yaml, .yml, .json) or directories with auto-detection by extension. | Python Unit Test (`cli.test_cli_003`) |
| CLI-004 | Multiple Source Paths | Accepts multiple `-s` flags for any combination of files and directories. | Python Unit Test (`cli.test_cli_004`) |
| CLI-005 | Output Directory Options (-o, --output) | Accepts output path argument. | Python Unit Test (`cli.test_cli_005`) |
| CLI-006 | Exclude Options (-e) | Excludes matching patterns from processing. | Python Unit Test (`cli.test_cli_006`) |
| CLI-009 | Invalid Source Handling | Returns error code if source path invalid. | Python Unit Test (`cli.test_cli_009`) |
| CLI-010 | Output Directory Creation | Creates output directory if it doesn't exist. | Python Unit Test (`cli.test_cli_010`) |
| CLI-011 | YAML Output Flag (--yaml) | `--yaml` generates YAML register map output. | Python Unit Test (`cli.test_cli_011`) |
| CLI-012 | JSON Output Flag (--json) | `--json` generates JSON register map output. | Python Unit Test (`cli.test_cli_012`) |
| CLI-013 | Configuration File Support (-c, --config) | `--config <file>` loads settings (sources, excludes) from JSON file. | Python Unit Test (`cli.test_cli_013`) |
| CLI-014 | Save Configuration to Persistent File | The tool must provide a mechanism to save the current configuration to a persistent file (e.g., `.axion_conf`). | GUI Integration Test |
| CLI-015 | Auto-load Configuration | The tool must automatically load configuration from `.axion_conf` in the current working directory if it exists and no specific config file is provided via `--config`. | Python Unit Test (`cli.test_cli_015`) |

> [!NOTE]
> The `-x/--xml-source` option is deprecated but still supported for backward compatibility. Use `-s/--source` for all source types instead.

## 7. Clock Domain Crossing (CDC)

| ID | Definition | Acceptance Criteria | Test Method |
|----|------------|---------------------|-------------|
| CDC-001 | Configurable Stage Count | `CDC_STAGE=N` setting changes synchronizer depth. | Python Unit Test (`cdc.test_cdc_001`) |
| CDC-002 | Default Stage Count | Defaults to 2 stages if not specified. | Python Unit Test (`cdc.test_cdc_002`) |
| CDC-003 | Sync Signal Declaration | Internal sync signals declared in VHDL. | Python Unit Test (`cdc.test_cdc_003`) |
| CDC-004 | Module Clock Port Generation | Generates `module_clk` port when CDC enabled. | Python Unit Test (`cdc.test_cdc_004`) |
| CDC-005 | CDC Disable Behavior | No sync logic generated if `CDC_EN` is missing/false. | Python Unit Test (`cdc.test_cdc_005`) |
| CDC-006 | Read-Only (RO) Path Synchronization | RO inputs synced to AXI clock domain. | Python Unit Test (`cdc.test_cdc_006`) |
| CDC-007 | Read-Write (RW) Path Synchronization | RW outputs synced to module clock domain. | Python Unit Test (`cdc.test_cdc_007`) |

## 8. Address Management (ADDR)

| ID | Definition | Acceptance Criteria | Test Method |
|----|------------|---------------------|-------------|
| ADDR-001 | Auto-assign Sequential Addresses | Assigns 0x00, 0x04, 0x08... automatically if unspecified. | Python Unit Test (`addr.test_addr_001`) |
| ADDR-002 | Manual Address Assignment | `ADDR=0xNN` allows specific address placement. | Python Unit Test (`addr.test_addr_002`) |
| ADDR-003 | Mixed Auto/Manual Assignment | Auto assignment skips manually assigned addresses. | Python Unit Test (`addr.test_addr_003`) |
| ADDR-004 | Address Alignment | All addresses must be 4-byte aligned. | Python Unit Test (`addr.test_addr_004`) |
| ADDR-005 | Conflict Detection | Manual assignment collision raises error. | Python Unit Test (`addr.test_addr_005`) |
| ADDR-006 | Wide Signal Address Reservation | Signals >32 bits reserve multiple 4-byte slots. | Python Unit Test (`addr.test_addr_006`) |
| ADDR-007 | Gap Preservation | Gaps created by manual addressing are preserved. | Python Unit Test (`addr.test_addr_007`) |
| ADDR-008 | Base Address Offset Addition | Manual addresses are relative to module base. | Python Unit Test (`addr.test_addr_008`) |

## 9. Stress Testing (STRESS)

| ID | Definition | Acceptance Criteria | Test Method |
|----|------------|---------------------|-------------|
| STRESS-001 | Support High Register Count | Can generate module with 100+ registers. | Python Unit Test (`stress.test_stress_001`) |
| STRESS-002 | Support Very Wide Signals | Can handle 256-bit+ signals correctly. | Python Unit Test (`stress.test_stress_002`) |
| STRESS-003 | Repeated Analysis Stability | Multiple runs produce consistent results. | Python Unit Test (`stress.test_stress_003`) |
| STRESS-004 | Repeated Generation Stability | Generation is deterministic. | Python Unit Test (`stress.test_stress_004`) |
| STRESS-005 | Random Address Patterns | Handles non-sequential manual addressing without error. | Python Unit Test (`stress.test_stress_005`) |
| STRESS-006 | Boundary Value Handling | Robust to min/max address and width values. | Python Unit Test (`stress.test_stress_006`) |

## 10. Subregisters (SUB)

| ID | Definition | Acceptance Criteria | Test Method |
|----|------------|---------------------|-------------|
| SUB-001 | Parse `REG_NAME` Attribute | Parser identifies `REG_NAME` to group signals. | Python Unit Test (`sub.test_sub_001`) |
| SUB-002 | Parse `BIT_OFFSET` Attribute | Parser identifies start bit for fields. | Python Unit Test (`sub.test_sub_002`) |
| SUB-003 | Group signals by `REG_NAME` | Signals with same `REG_NAME` are grouped into one 32-bit register. | Python Unit Test (`sub.test_sub_003`) |
| SUB-004 | Auto-calculate Register Width | Register width determined by fields (always 32-bit container). | Python Unit Test (`sub.test_sub_004`) |
| SUB-005 | Detect Bit Overlaps | Overlapping bit ranges raise `BitOverlapError`. | Python Unit Test (`sub.test_sub_005`) |
| SUB-006 | Auto-pack signals | Fields without `BIT_OFFSET` pack sequentially. | Python Unit Test (`sub.test_sub_006`) |
| SUB-011 | Backward Compatibility | Standard signals still processed correctly mixed with subregs. | Python Unit Test (`sub.test_sub_011`) |

## 11. Default Values (DEF)

| ID | Definition | Acceptance Criteria | Test Method |
|----|------------|---------------------|-------------|
| DEF-001 | Parse `DEFAULT` Hex Value | `DEFAULT=0x...` parsed correctly. | Python Unit Test (`def.test_def_001`) |
| DEF-002 | Parse `DEFAULT` Decimal Value | `DEFAULT=100` parsed correctly. | Python Unit Test (`def.test_def_002`) |
| DEF-003 | Validate Default fits Width | Value larger than signal width raises error/warning. | Python Unit Test (`def.test_def_003`) |
| DEF-004 | Default to 0 if unspecified | Signals default to 0x0 if no attribute. | Python Unit Test (`def.test_def_004`) |
| DEF-009 | Combine Subregister Defaults | Packed register default is OR-combination of field defaults. | Python Unit Test (`def.test_def_009`) |
| DEF-010 | Backward Compatibility | Existing modules unaffected. | Python Unit Test (`def.test_def_010`) |

## 12. Validation & Diagnostics (VAL)

| ID | Definition | Acceptance Criteria | Test Method |
|----|------------|---------------------|-------------|
| VAL-001 | Required Field Validation | Missing 'module' or other required fields in source files (YAML/JSON/XML) must be reported as Errors. | Python Unit Test (`val.test_val_001`) |
| VAL-002 | Format Error Visibility | Parsing errors (malformed syntax) must be visible in Rule Check results. | Python Unit Test (`val.test_val_002`) |
| VAL-003 | Logical Integrity Check | Validates integrity of loaded modules (e.g. non-empty register lists). | Python Unit Test (`val.test_val_003`) |
| VAL-004 | Description Presence | Warns if registers are missing descriptions/documentation. | Python Unit Test (`val.test_val_004`) |
| VAL-005 | Duplicate Module Name | Error if multiple modules share the same name. | Python Unit Test (`val.test_val_005`) |

