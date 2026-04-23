# Core Requirements

This document tracks all functional and non-functional requirements for the Axion-HDL core tool.
Testing and verification are automated via `make test`, which maps tests back to these requirement IDs.

## Requirement Categories

| Prefix | Category | Definition |
|--------|----------|------------|
| **AXION** | Core Protocol | Core AXI4/AXI4-Lite register interaction and compliance. |
| **AXI-LITE** | Bus Protocol | Specific AXI4-Lite handshake and signaling rules. |
| **PARSER** | VHDL Parsing | Parsing of VHDL entities, signals, and `@axion` annotations. |
| **XML-INPUT** | XML Parsing | Parsing of XML register definition files. |
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
| **VAL** | Validation | Validation of inputs, error visibility, and diagnostics. |
| **EQUIV** | Format Equivalence | Cross-format parsing and output equivalence. |
| **AXION-TYPES** | Typed AXI Ports | Optional typed AXI4-Lite port generation using `axion_common_pkg` record types. |

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
| PARSER-009 | signal_type Format Compatibility | The `signal_type` field in the register dict produced by VHDLParser must be parseable by downstream generators (CHeaderGenerator, DocGenerator) to extract the correct bit width. | Python Unit Test (`parser.test_parser_009`) |

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
| GEN-019 | C Header Width Propagation (YAML) | `CHeaderGenerator._get_signal_width` must correctly extract width from `signal_type` strings produced by the YAML parser (`std_logic`, `std_logic_vector(N downto 0)`). WIDTH and NUM_REGS macros must reflect the declared width. | Python Unit Test (`gen.test_gen_019`) |
| GEN-020 | C Header Width Propagation (VHDL Annotation) | Same as GEN-019 but for `signal_type` strings produced by the VHDL-annotation parser (`[N:0]` format). WIDTH and NUM_REGS macros must reflect the declared width. | Python Unit Test (`gen.test_gen_020`) |
| GEN-021 | C Header Struct Layout for Wide Signals | Registers wider than 32 bits must appear as multiple `_reg0`, `_reg1` … members in the generated struct. Registers ≤ 32 bits must appear as a single member with no suffix. | Python Unit Test (`gen.test_gen_021`) |
| GEN-022 | Markdown Width Column Accuracy (YAML) | The Width column in the generated `register_map.md` table must show the actual declared register width, not a hardcoded value, for registers defined via YAML. | Python Unit Test (`gen.test_gen_022`) |
| GEN-023 | Markdown Width Column Accuracy (VHDL Annotation) | Same as GEN-022 but for registers defined via VHDL `@axion` annotations. | Python Unit Test (`gen.test_gen_023`) |
| GEN-024 | Packed Register MASK/SHIFT Macros (YAML) | For packed (subregister) fields defined via YAML, the generated header must contain correct MASK and SHIFT `#define` macros matching each field's `bit_offset` and `width`. | Python Unit Test (`gen.test_gen_024`) |
| GEN-025 | Packed Register MASK/SHIFT Macros (VHDL Annotation) | Same as GEN-024 but for packed fields defined via VHDL `@axion` annotations with `REG_NAME`/`BIT_OFFSET`. | Python Unit Test (`gen.test_gen_025`) |
| GEN-026 | Packed Register Container is 32-bit | A packed register container must appear as exactly one `uint32_t` member in the struct (no `_reg0` split). | Python Unit Test (`gen.test_gen_026`) |
| GEN-027 | VHDL Entity Port Width – YAML source | For registers defined via YAML, the generated VHDL entity port must use the declared width (e.g. `std_logic` for 1-bit, `std_logic_vector(4 downto 0)` for 5-bit). Must not default to 32-bit. | Python Unit Test (`gen.test_gen_027`) |
| GEN-028 | VHDL Entity Port Width – VHDL-annotation source | Same as GEN-027 but for registers defined via VHDL `@axion` annotations. | Python Unit Test (`gen.test_gen_028`) |

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
| SUB-007 | Subregister Field Width in Header (VHDL) | MASK and SHIFT macros generated for packed fields defined via VHDL `@axion` annotations must match the declared `BIT_OFFSET` and signal width exactly. | Python Unit Test (`sub.test_sub_007`) |
| SUB-008 | Subregister Field Width in Header (YAML) | MASK and SHIFT macros generated for packed fields defined via YAML `reg_name` / `bit_offset` must match the declared `bit_offset` and `width` exactly. | Python Unit Test (`sub.test_sub_008`) |
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
| VAL-006 | Numeric Attribute Validation | Invalid numeric values for `base_addr`, `addr`, `width`, `bit_offset`, and `cdc_stage` must be reported as Parsing Errors. | Python Unit Test |
| VAL-007 | Generation Safety Lock | The tool must block all code and documentation generation if any analyzed module contains parsing errors. | Python Unit Test |

## 13. XML Input (XML-INPUT)

| ID | Definition | Acceptance Criteria | Test Method |
|----|------------|---------------------|-------------|
| XML-INPUT-001 | XML File Detection | Parser detects and loads `.xml` files from directories. | Python Unit Test (`xml_input.test_xml_input_001`) |
| XML-INPUT-002 | Module Name Extraction | Correctly extracts `module` attribute from root element. | Python Unit Test (`xml_input.test_xml_input_002`) |
| XML-INPUT-003 | Base Address Parsing | Parses `base_addr` as hex string or decimal value. | Python Unit Test (`xml_input.test_xml_input_003`) |
| XML-INPUT-004 | Register Definition Parsing | Parses `<register>` elements with name, addr, access, width attributes. | Python Unit Test (`xml_input.test_xml_input_004`) |
| XML-INPUT-005 | Access Mode Support | Handles RO, RW, WO access modes (case-insensitive). | Python Unit Test (`xml_input.test_xml_input_005`) |
| XML-INPUT-006 | Strobe Signal Support | Parses `r_strobe` and `w_strobe` attributes ("true"/"false"). | Python Unit Test (`xml_input.test_xml_input_006`) |
| XML-INPUT-007 | CDC Configuration Parsing | Parses `<config>` element for `cdc_en` and `cdc_stage` settings. | Python Unit Test (`xml_input.test_xml_input_007`) |
| XML-INPUT-008 | Description Support | Parses `description` attribute on register elements. | Python Unit Test (`xml_input.test_xml_input_008`) |
| XML-INPUT-009 | Address Auto-Assignment | Assigns sequential 4-byte addresses if `addr` is omitted. | Python Unit Test (`xml_input.test_xml_input_009`) |
| XML-INPUT-010 | Error Handling | Returns None for malformed XML or missing files, populates errors list. | Python Unit Test (`xml_input.test_xml_input_010`) |
| XML-INPUT-011 | CLI Integration | Works with `AxionHDL.add_source()` and `-s` CLI flag. | Python Unit Test (`xml_input.test_xml_input_011`) |
| XML-INPUT-012 | Output Equivalence | XML with same content as VHDL produces equivalent VHDL output. | Python Unit Test (`xml_input.test_xml_input_012`) |
| XML-INPUT-013 | Generator Compatibility | Parses XML files generated by XMLGenerator (SPIRIT format). | Python Unit Test (`xml_input.test_xml_input_013`) |
| XML-INPUT-014 | Roundtrip Integrity | Parse → Generate → Parse produces identical module dictionary. | Python Unit Test (`xml_input.test_xml_input_014`) |
| XML-INPUT-015 | Unified Attribute Naming | Uses consistent attribute names between parser and generator. | Python Unit Test (`xml_input.test_xml_input_015`) |

## 14. YAML Input (YAML-INPUT)

| ID | Definition | Acceptance Criteria | Test Method |
|----|------------|---------------------|-------------|
| YAML-INPUT-001 | YAML File Detection | Parser detects and loads `.yaml` and `.yml` files. | Python Unit Test (`yaml_input.test_yaml_input_001`) |
| YAML-INPUT-002 | Module Name Extraction | Correctly extracts `module` field. | Python Unit Test (`yaml_input.test_yaml_input_002`) |
| YAML-INPUT-003 | Hex Base Address Parsing | Parses `base_addr` as hex string. | Python Unit Test (`yaml_input.test_yaml_input_003`) |
| YAML-INPUT-004 | Decimal Base Address Parsing | Parses `base_addr` as decimal integer. | Python Unit Test (`yaml_input.test_yaml_input_004`) |
| YAML-INPUT-005 | Register List Parsing | Parses registers array with name, addr, access, width. | Python Unit Test (`yaml_input.test_yaml_input_005`) |
| YAML-INPUT-006 | Access Mode Support | Handles RO, RW, WO (case-insensitive). | Python Unit Test (`yaml_input.test_yaml_input_006`) |
| YAML-INPUT-007 | Strobe Signal Parsing | Parses `r_strobe` and `w_strobe` boolean flags. | Python Unit Test (`yaml_input.test_yaml_input_007`) |
| YAML-INPUT-008 | CDC Configuration Parsing | Parses `config.cdc_en` and `config.cdc_stage`. | Python Unit Test (`yaml_input.test_yaml_input_008`) |
| YAML-INPUT-009 | Description Field | Parses register description string. | Python Unit Test (`yaml_input.test_yaml_input_009`) |
| YAML-INPUT-010 | Auto Address Assignment | Assigns sequential 4-byte addresses when `addr` omitted. | Python Unit Test (`yaml_input.test_yaml_input_010`) |
| YAML-INPUT-011 | Invalid YAML Handling | Returns None for malformed YAML syntax. | Python Unit Test (`yaml_input.test_yaml_input_011`) |
| YAML-INPUT-012 | Missing Module Name | Returns None when `module` field is absent. | Python Unit Test (`yaml_input.test_yaml_input_012`) |
| YAML-INPUT-013 | Packed Register Parsing | Parses `reg_name` and `bit_offset` for subregister fields. | Python Unit Test (`yaml_input.test_yaml_input_013`) |
| YAML-INPUT-014 | Default Value Parsing | Parses `default` as hex string or decimal integer. | Python Unit Test (`yaml_input.test_yaml_input_014`) |
| YAML-INPUT-015 | Wide Signal Width Storage | Stores `width > 32` correctly in the register dict. | Python Unit Test (`yaml_input.test_yaml_input_015`) |
| YAML-INPUT-016 | signal_type Format Compatibility | The `signal_type` field produced by YAMLInputParser must be parseable by downstream generators (CHeaderGenerator, DocGenerator) to extract the correct bit width for all register widths (1, sub-32, 32, >32). | Python Unit Test (`yaml_input.test_yaml_input_016`) |


## 15. SystemVerilog Generation (SV-GEN)

| ID | Definition | Acceptance Criteria | Test Method |
|----|------------|---------------------|-------------|
| SV-GEN-001 | Valid SystemVerilog Output | Generates syntactically correct `.sv` files compilable by Verilator/Vivado. | Syntax Test (`test_sv_syntax`) |
| SV-GEN-002 | Reset Value Support | Registers initialize to `default` value defined in source (or 0 if undefined) upon reset. | SystemVerilog Test (`test_sv_db_001`) |
| SV-GEN-003 | Wide Register Access | Registers >32 bits are mapped to multiple 32-bit addresses for full access. | SystemVerilog Test (`test_sv_wide_001`) |
| SV-GEN-004 | Native Struct Support | Packed registers are generated as `struct packed` types for bitfield access. | SystemVerilog Test (`test_sv_struct_001`) |
| SV-GEN-005 | Functional Verification | Generated modules support signal driving/sampling in Cocotb simulation. | Cocotb Test (`test_sv_cocotb`) |
| SV-GEN-006 | Lint Compliance | Generated code passes `verilator --lint-only -Wall` with zero errors. | Lint Test (`test_sv_lint`) |
| SV-GEN-007 | Equivalence with VHDL | SystemVerilog behavior (address map, reset, strobe) matches VHDL implementation. | Equivalence Test (`test_sv_equiv`) |
| SV-GEN-008 | Bare Annotation Support | A bare `// @axion` annotation with no attributes is recognized and defaults to RW access, auto-assigned address, no strobes. | SystemVerilog Test (`test_sv_axion_033`, `test_sv_axion_034`) |
| SV-GEN-009 | Address Conflict Recovery | When two signals are manually assigned the same address, the conflicting register is reassigned to the next available address instead of being dropped. A warning is recorded in `parsing_errors`. | SystemVerilog Test (`test_sv_axion_027`) |


## 16. Enumerated Values Requirements

| ID | Definition | Acceptance Criteria | Test Method |
|----|------------|---------------------|-------------|
| ENUM-001 | BitField Data Model | `BitField` dataclass includes optional `enum_values: Dict[int, str]` field. | Python Unit Test (`test_enum_001_bitfield_model`) |
| ENUM-002 | VHDL Annotation Parsing | `ENUM=` attribute in `@axion` comment is parsed to `Dict[int, str]`. | Python Unit Test (`test_enum_002_vhdl_annotation_parse`) |
| ENUM-003 | SV Annotation Parsing | `ENUM=` attribute in `// @axion` comment is parsed to `Dict[int, str]`. | Python Unit Test (`test_enum_003_sv_annotation_parse`) |
| ENUM-004 | YAML Field Enum | YAML field `enum_values` dict (int or string keys) is parsed to `Dict[int, str]`. | Python Unit Test (`test_enum_004_yaml_field_enum`) |
| ENUM-005 | JSON Field Enum | JSON field `enum_values` dict (string keys) is parsed to `Dict[int, str]`. | Python Unit Test (`test_enum_005_json_field_enum`) |
| ENUM-006 | TOML Field Enum | TOML field `enum_values` dict (string keys) is parsed to `Dict[int, str]`. | Python Unit Test (`test_enum_006_toml_field_enum`) |
| ENUM-007 | XML Flat Enum Attribute | Flat XML `enum` attribute is parsed via `parse_enum_values()`. | Python Unit Test (`test_enum_007_xml_flat_enum_attr`) |
| ENUM-008 | XML Nested Enum Elements | `<enum_value value="..." name="..."/>` children within `<field>` are parsed to enum dict. | Python Unit Test (`test_enum_008_xml_nested_enum_elements`) |
| ENUM-009 | XML SPIRIT Enum | `spirit:enumeratedValues/spirit:enumeratedValue` elements are parsed to enum dict. | Python Unit Test (`test_enum_009_xml_spirit_enum`) |
| ENUM-010 | Markdown/HTML Enum Column | Doc generator adds "Enum Values" column to packed register field table when any field has enum_values. | Python Unit Test (`test_enum_010_markdown_enum_column`) |
| ENUM-011 | C Header Enum Macros | C header generator emits `#define MODULE_REG_FIELD_NAME 0xVAL` for each enum value. | Python Unit Test (`test_enum_011_c_header_macros`) |
| ENUM-012 | YAML Export Round-Trip | YAML generator includes `enum_values` with string keys; re-parsed result matches original. | Python Unit Test (`test_enum_012_yaml_export_roundtrip`) |
| ENUM-013 | JSON Export Round-Trip | JSON generator includes `enum_values` with string keys; re-parsed result matches original. | Python Unit Test (`test_enum_013_json_export_roundtrip`) |
| ENUM-014 | XML SPIRIT Export | XML generator emits `<spirit:enumeratedValues>` block for fields with enum_values. | Python Unit Test (`test_enum_014_xml_spirit_export`) |
| ENUM-015 | VHDL Comment Annotation | VHDL generator appends `-- NAME=VALUE` comment for fields with enum_values. | Python Unit Test (`test_enum_015_vhdl_comment_only`) |
| ENUM-016 | SV Comment Annotation | SV generator appends `// NAME=VALUE` comment for signals with enum_values. | Python Unit Test (`test_enum_016_sv_comment_only`) |
| ENUM-018 | No-Enum Regression | Modules without enum_values generate identical output to pre-feature baseline. | Python Unit Test (`test_enum_018_no_enum_regression`) |
| ENUM-019 | Numeric Notations | Enum values expressed as decimal, hex (`0x`), and binary (`0b`) in source are all parsed correctly. | Python Unit Test (`test_enum_019_numeric_notations`) |
| ENUM-020 | VHDL Pkg Constants | `generate_vhdl_pkg()` produces a `.vhd` package file with `constant C_REG_FIELD_NAME` for each enum value. | Python Unit Test (`test_enum_020_vhdl_pkg_constants`) |
| ENUM-021 | SV Pkg Typedef | `generate_sv_pkg()` produces a `.sv` package file with `typedef enum logic` for each field. | Python Unit Test (`test_enum_021_sv_pkg_typedef`) |
| ENUM-022 | Value Overflow Validation | `add_field()` raises `ValueError` when an enum value exceeds `2**width - 1`; numeric notation length does not affect the check. | Python Unit Test (`test_enum_022_value_overflow_validation`) |
| ENUM-023 | One-Bit Field | 1-bit fields with `{0: 'INACTIVE', 1: 'ACTIVE'}` enum produce correct VHDL `std_logic` constants and SV `typedef enum logic`. | Python Unit Test (`test_enum_023_one_bit_field`) |
| ENUM-024 | Rule Checker Overflow | `RuleChecker.check_enum_value_overflow()` reports an error for each enum value exceeding field width. | Python Unit Test (`test_enum_024_rule_check_reports_overflow`) |
| ENUM-025 | Rule Checker Standalone Overflow | `RuleChecker.check_enum_value_overflow()` detects overflow in standalone (non-packed) registers with `enum_values`. | Python Unit Test (`test_enum_025_rule_checker_standalone_overflow`) |
| ENUM-026 | VHDL Standalone Overflow E2E | A VHDL annotation with an overflowing enum value on a standalone signal triggers a rule-check error in the full parse pipeline. | Python Unit Test (`test_enum_026_vhdl_standalone_overflow_e2e`) |
| ENUM-027 | SV Standalone Overflow E2E | An SV annotation with an overflowing enum value on a standalone signal triggers a rule-check error in the full parse pipeline. | Python Unit Test (`test_enum_027_sv_standalone_overflow_e2e`) |
| ENUM-028 | All Overflows Reported | `add_field()` raises `ValueError` naming every overflowing enum value in a single message, not just the first. | Python Unit Test (`test_enum_028_all_overflows_reported`) |
| ENUM-029 | Negative Value Rejected (BitField) | `add_field()` raises `ValueError` when an enum value is negative. | Python Unit Test (`test_enum_029_negative_value_bitfield`) |
| ENUM-030 | Negative Value Rejected (RuleChecker) | `RuleChecker.check_enum_value_overflow()` reports an error for a negative enum value. | Python Unit Test (`test_enum_030_negative_value_rule_checker`) |
| ENUM-031 | YAML Field Invalid Enum Key | YAML parser records a parsing error when a field-level enum key cannot be parsed as an integer. | Python Unit Test (`test_enum_031_yaml_field_invalid_enum_key`) |
| ENUM-032 | YAML Standalone Invalid Enum Key | YAML parser records a parsing error when a standalone-register enum key cannot be parsed as an integer. | Python Unit Test (`test_enum_032_yaml_standalone_invalid_enum_key`) |
| ENUM-033 | VHDL Pkg Identifier Sanitization | `generate_vhdl_pkg()` replaces non-alphanumeric characters in constant names with `_`, collapses adjacent underscores, and strips leading/trailing underscores. | Python Unit Test (`test_enum_033_vhdl_pkg_identifier_sanitization`) |
| ENUM-034 | SV Pkg Identifier Sanitization | `generate_sv_pkg()` replaces non-alphanumeric characters in typedef/member names with `_`. | Python Unit Test (`test_enum_034_sv_pkg_identifier_sanitization`) |
| ENUM-035 | C Header Identifier Sanitization | C header generator sanitizes enum labels to valid C identifiers in `#define` macros. | Python Unit Test (`test_enum_035_c_header_identifier_sanitization`) |
| ENUM-036 | VHDL Pkg Returns None (No Enum) | `generate_vhdl_pkg()` returns `None` when the module has no fields with `enum_values`. | Python Unit Test (`test_enum_036_vhdl_pkg_returns_none_no_enum`) |
| ENUM-037 | SV Pkg Returns None (No Enum) | `generate_sv_pkg()` returns `None` when the module has no fields with `enum_values`. | Python Unit Test (`test_enum_037_sv_pkg_returns_none_no_enum`) |
| ENUM-038 | VHDL Port Comment No Double Dash | VHDL generator enum port comment uses parentheses format rather than embedding `--` which would create invalid VHDL. | Python Unit Test (`test_enum_038_vhdl_port_comment_no_double_dash`) |
| ENUM-039 | generate_module Co-generates Pkg | `generate_module()` automatically produces `_regs_pkg.vhd` alongside the register module when enum fields are present. | Python Unit Test (`test_enum_039_generate_module_cogenerates_pkg`) |
| ENUM-040 | XML Simple Invalid Enum Value Reported | XML parser records an error when a simple-format `<enum_value>` has a non-integer `value` attribute instead of silently dropping it. | Python Unit Test (`test_enum_040_xml_simple_invalid_enum_value_recorded`) |
| ENUM-041 | XML SPIRIT Invalid Enum Value Reported | XML parser records an error when a SPIRIT `<spirit:value>` element contains a non-integer string instead of silently dropping it. | Python Unit Test (`test_enum_041_xml_spirit_invalid_enum_value_recorded`) |
| ENUM-042 | VHDL Identifier Adjacent Underscores | `_sanitize_vhdl_identifier()` collapses adjacent underscores to one, strips leading and trailing underscores, and prepends `v_` when the result starts with a digit. | Python Unit Test (`test_enum_042_vhdl_identifier_no_adjacent_underscores`) |

---

## Typed AXI Ports (AXION-TYPES)

Covers optional generation of typed `t_axi_lite_m2s` / `t_axi_lite_s2m` record ports (VHDL) and struct ports (SystemVerilog) from `axion_common_pkg`, instead of the default flat individual signals.

| ID | Definition | Acceptance Criteria | Test Method |
|----|------------|---------------------|-------------|
| AXION-TYPES-001 | YAML Config Parsing | `use_axion_types: true` in a YAML `config:` block sets `module_data['use_axion_types'] = True`; absence or `false` sets `False`. | Python Unit Test (`test_axion_types_001_yaml_config_parsing`) |
| AXION-TYPES-002 | TOML Config Parsing | `use_axion_types = true` in a TOML `[config]` table sets `module_data['use_axion_types'] = True`. | Python Unit Test (`test_axion_types_002_toml_config_parsing`) |
| AXION-TYPES-003 | XML Config Parsing | `use_axion_types="true"` attribute on the `<config>` element sets `module_data['use_axion_types'] = True`. | Python Unit Test (`test_axion_types_003_xml_config_parsing`) |
| AXION-TYPES-004 | JSON Config Parsing | `"use_axion_types": true` in a JSON `config` object (passed through YAML parser) sets `module_data['use_axion_types'] = True`. | Python Unit Test (`test_axion_types_004_json_config_parsing`) |
| AXION-TYPES-005 | Default Disabled | When `use_axion_types` is absent from all config blocks, `module_data['use_axion_types']` defaults to `False`. | Python Unit Test (`test_axion_types_005_default_disabled`) |
| AXION-TYPES-006 | CLI Flag Override | `--use-axion-types` CLI flag sets `use_axion_types = True` on every analyzed module, overriding any per-module config value. | Python Unit Test (`test_axion_types_006_cli_flag_override`) |
| AXION-TYPES-007 | VHDL Library Clause | When `use_axion_types` is enabled, generated VHDL includes `use work.axion_common_pkg.all;` in the library/use clause section. | Python Unit Test (`test_axion_types_007_vhdl_library_clause`) |
| AXION-TYPES-008 | VHDL Entity Typed Ports | When `use_axion_types` is enabled, the VHDL entity port list contains `axi_m2s : in t_axi_lite_m2s` and `axi_s2m : out t_axi_lite_s2m` instead of the 19 flat individual AXI signals. | Python Unit Test (`test_axion_types_008_vhdl_entity_typed_ports`) |
| AXION-TYPES-009 | VHDL No Flat AXI Ports | When `use_axion_types` is enabled, no flat AXI port names (`axi_awaddr`, `axi_wdata`, etc.) appear in the entity port list. | Python Unit Test (`test_axion_types_009_vhdl_no_flat_axi_ports`) |
| AXION-TYPES-010 | VHDL Intermediate Signal Declarations | When `use_axion_types` is enabled, the architecture declaration region contains `signal axi_awaddr`, `signal axi_wdata`, and all other M2S and S2M intermediate signal declarations. | Python Unit Test (`test_axion_types_010_vhdl_intermediate_signals`) |
| AXION-TYPES-011 | VHDL M2S Unpack Assignments | When `use_axion_types` is enabled, the architecture body contains concurrent signal assignments unpacking every `axi_m2s` record field to the corresponding intermediate signal (e.g. `axi_awaddr <= axi_m2s.awaddr`). | Python Unit Test (`test_axion_types_011_vhdl_m2s_unpack`) |
| AXION-TYPES-012 | VHDL S2M Pack Assignments | When `use_axion_types` is enabled, the architecture body contains concurrent signal assignments packing every intermediate signal into the corresponding `axi_s2m` record field (e.g. `axi_s2m.awready <= axi_awready`). | Python Unit Test (`test_axion_types_012_vhdl_s2m_pack`) |
| AXION-TYPES-013 | VHDL Default Unchanged | When `use_axion_types` is `False`, generated VHDL output is identical to the pre-feature baseline (flat individual AXI ports, no axion_common_pkg clause). | Python Unit Test (`test_axion_types_013_vhdl_default_unchanged`) |
| AXION-TYPES-014 | SV Package Import | When `use_axion_types` is enabled, the generated SystemVerilog file includes `import axion_common_pkg::*;` before the module declaration. | Python Unit Test (`test_axion_types_014_sv_package_import`) |
| AXION-TYPES-015 | SV Module Typed Ports | When `use_axion_types` is enabled, the SystemVerilog module port list contains `input t_axi_lite_m2s axi_m2s` and `output t_axi_lite_s2m axi_s2m` instead of the flat individual AXI signals. | Python Unit Test (`test_axion_types_015_sv_module_typed_ports`) |
| AXION-TYPES-016 | SV No Flat AXI Ports | When `use_axion_types` is enabled, no flat AXI port names (`axi_awaddr`, `axi_wdata`, etc.) appear in the module port list. | Python Unit Test (`test_axion_types_016_sv_no_flat_axi_ports`) |
| AXION-TYPES-017 | SV Intermediate Signal Declarations | When `use_axion_types` is enabled, the SystemVerilog module body contains `logic` declarations for all M2S and S2M intermediate signals. | Python Unit Test (`test_axion_types_017_sv_intermediate_signals`) |
| AXION-TYPES-018 | SV M2S Unpack Assigns | When `use_axion_types` is enabled, the SystemVerilog module body contains `assign axi_awaddr = axi_m2s.awaddr;` and equivalent assigns for all M2S fields. | Python Unit Test (`test_axion_types_018_sv_m2s_unpack`) |
| AXION-TYPES-019 | SV S2M Pack Assigns | When `use_axion_types` is enabled, the SystemVerilog module body contains `assign axi_s2m.awready = axi_awready;` and equivalent assigns for all S2M fields. | Python Unit Test (`test_axion_types_019_sv_s2m_pack`) |
| AXION-TYPES-020 | SV Default Unchanged | When `use_axion_types` is `False`, generated SystemVerilog output is identical to the pre-feature baseline (flat individual AXI ports, no package import). | Python Unit Test (`test_axion_types_020_sv_default_unchanged`) |
| AXION-TYPES-021 | Per-Module Independence | Setting `use_axion_types: true` on one module does not affect sibling modules parsed from the same source directory. | Python Unit Test (`test_axion_types_021_per_module_independence`) |
