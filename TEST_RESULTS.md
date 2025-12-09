# Axion-HDL Test Results

**Overall Status:** ⚠️ SOME SKIPPED

## Summary

| Metric | Value |
|--------|-------|
| **Total Tests** | 107 |
| ✅ Passed | 105 |
| ❌ Failed | 0 |
| ⏭️ Skipped | 2 |
| ⏱️ Total Time | 2.57s |
| 🕐 Last Run | 2025-12-09 08:16:21 |

## 🐍 Python Tests

### Unit Tests

**7/7 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `python.unit.init` | Initialize AxionHDL | 0.009s |
| ✅ | `python.unit.add_src` | Add Source Directory | 0.000s |
| ✅ | `python.unit.analyze` | Analyze VHDL Files | 0.004s |
| ✅ | `python.unit.gen_vhdl` | Generate VHDL Modules | 0.007s |
| ✅ | `python.unit.gen_c` | Generate C Headers | 0.005s |
| ✅ | `python.unit.gen_xml` | Generate XML Register Map | 0.004s |
| ✅ | `python.unit.gen_doc` | Generate Markdown Documentation | 0.003s |

### Address Conflict Tests

**3/3 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `python.conflict.basic` | Basic Address Conflict Detection | 0.003s |
| ✅ | `python.conflict.no_false_positive` | No False Positive (Unique Addresses) | 0.001s |
| ✅ | `python.conflict.wide_signal` | Wide Signal Address Overlap | 0.000s |

## ⚙️ C Tests

### Compilation Tests

**3/3 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `c.compile.gcc_check` | GCC Available | 0.006s |
| ✅ | `c.compile.headers` | Compile C Header Test | 0.512s |
| ✅ | `c.compile.run` | Run C Header Test Binary | 0.002s |

## 🔧 VHDL Tests

### Simulation Setup

**0/1 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ⏭️ | `vhdl.ghdl.check` | GHDL Available | 0.000s |

## 📜 Parser Tests (PARSER-xxx)

### PARSER Requirements

**20/20 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `parser.test_parser_001_basic_entity_extraction` | PARSER-001-BASIC-ENTITY-EXTRACTION: PARSER-001: Basic entity name extraction | 0.001s |
| ✅ | `parser.test_parser_001_entity_with_whitespace` | PARSER-001-ENTITY-WITH-WHITESPACE: PARSER-001: Entity extraction with varying whitespace | 0.001s |
| ✅ | `parser.test_parser_001_no_entity` | PARSER-001-NO-ENTITY: PARSER-001: File without entity declaration | 0.000s |
| ✅ | `parser.test_parser_002_std_logic` | PARSER-002-STD-LOGIC: PARSER-002: Parse std_logic as 1-bit | 0.000s |
| ✅ | `parser.test_parser_002_std_logic_vector_downto` | PARSER-002-STD-LOGIC-VECTOR-DOWNTO: PARSER-002: Parse std_logic_vector(N downto M) | 0.001s |
| ✅ | `parser.test_parser_002_std_logic_vector_with_spaces` | PARSER-002-STD-LOGIC-VECTOR-WITH-SPACES: PARSER-002: Parse std_logic_vector with extra spaces | 0.001s |
| ✅ | `parser.test_parser_003_access_modes` | PARSER-003-ACCESS-MODES: PARSER-003: Parse RO, RW, WO access modes | 0.000s |
| ✅ | `parser.test_parser_003_multiple_attributes_same_line` | PARSER-003-MULTIPLE-ATTRIBUTES-SAME-LINE: PARSER-003: Multiple attributes on single line | 0.000s |
| ✅ | `parser.test_parser_003_strobe_flags` | PARSER-003-STROBE-FLAGS: PARSER-003: Parse R_STROBE and W_STROBE flags | 0.001s |
| ✅ | `parser.test_parser_004_base_addr_hex` | PARSER-004-BASE-ADDR-HEX: PARSER-004: Parse BASE_ADDR in hex format | 0.000s |
| ✅ | `parser.test_parser_004_cdc_enable` | PARSER-004-CDC-ENABLE: PARSER-004: Parse CDC_EN flag | 0.000s |
| ✅ | `parser.test_parser_004_cdc_stage` | PARSER-004-CDC-STAGE: PARSER-004: Parse CDC_STAGE attribute | 0.001s |
| ✅ | `parser.test_parser_004_missing_axion_def_defaults` | PARSER-004-MISSING-AXION-DEF-DEFAULTS: PARSER-004: Default values when @axion_def missing | 0.001s |
| ✅ | `parser.test_parser_005_decimal_address` | PARSER-005-DECIMAL-ADDRESS: PARSER-005: Parse decimal address (16) | 0.001s |
| ✅ | `parser.test_parser_005_hex_address` | PARSER-005-HEX-ADDRESS: PARSER-005: Parse hex address (0x10) | 0.000s |
| ✅ | `parser.test_parser_005_upper_case_hex` | PARSER-005-UPPER-CASE-HEX: PARSER-005: Parse uppercase hex (0X10) | 0.001s |
| ✅ | `parser.test_parser_006_desc_with_special_chars` | PARSER-006-DESC-WITH-SPECIAL-CHARS: PARSER-006: Parse description with special characters | 0.001s |
| ✅ | `parser.test_parser_006_double_quoted_desc` | PARSER-006-DOUBLE-QUOTED-DESC: PARSER-006: Parse double-quoted description | 0.001s |
| ✅ | `parser.test_parser_007_exclude_directory` | PARSER-007-EXCLUDE-DIRECTORY: PARSER-007: Exclude directory by name | 0.002s |
| ✅ | `parser.test_parser_008_recursive_scan` | PARSER-008-RECURSIVE-SCAN: PARSER-008: Recursively scan subdirectories | 0.003s |

## 🏭 Code Generation Tests (GEN-xxx)

### GEN Requirements

**29/30 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `gen.test_gen_001_entity_name_pattern` | GEN-001-ENTITY-NAME-PATTERN: GEN-001: Entity name follows pattern <module>_axion_reg | 0.000s |
| ⏭️ | `gen.test_gen_001_vhdl_compiles` | GEN-001-VHDL-COMPILES: GEN-001: Generated VHDL compiles without errors | 0.017s |
| ✅ | `gen.test_gen_001_vhdl_file_exists` | GEN-001-VHDL-FILE-EXISTS: GEN-001: Generated VHDL file exists | 0.000s |
| ✅ | `gen.test_gen_002_architecture_rtl` | GEN-002-ARCHITECTURE-RTL: GEN-002: Architecture is named 'rtl' | 0.000s |
| ✅ | `gen.test_gen_002_signal_declarations` | GEN-002-SIGNAL-DECLARATIONS: GEN-002: Internal signals are properly declared | 0.000s |
| ✅ | `gen.test_gen_003_axi_clock_reset` | GEN-003-AXI-CLOCK-RESET: GEN-003: Clock and reset signals present | 0.000s |
| ✅ | `gen.test_gen_003_read_address_channel` | GEN-003-READ-ADDRESS-CHANNEL: GEN-003: Read address channel signals present | 0.000s |
| ✅ | `gen.test_gen_003_read_data_channel` | GEN-003-READ-DATA-CHANNEL: GEN-003: Read data channel signals present | 0.000s |
| ✅ | `gen.test_gen_003_write_address_channel` | GEN-003-WRITE-ADDRESS-CHANNEL: GEN-003: Write address channel signals present | 0.000s |
| ✅ | `gen.test_gen_003_write_data_channel` | GEN-003-WRITE-DATA-CHANNEL: GEN-003: Write data channel signals present | 0.000s |
| ✅ | `gen.test_gen_003_write_response_channel` | GEN-003-WRITE-RESPONSE-CHANNEL: GEN-003: Write response channel signals present | 0.000s |
| ✅ | `gen.test_gen_004_ro_register_direction` | GEN-004-RO-REGISTER-DIRECTION: GEN-004: RO registers have 'in' direction | 0.000s |
| ✅ | `gen.test_gen_004_wo_register_direction` | GEN-004-WO-REGISTER-DIRECTION: GEN-004: WO registers have 'out' direction | 0.000s |
| ✅ | `gen.test_gen_005_read_strobe_port` | GEN-005-READ-STROBE-PORT: GEN-005: R_STROBE generates read strobe port | 0.000s |
| ✅ | `gen.test_gen_006_write_strobe_port` | GEN-006-WRITE-STROBE-PORT: GEN-006: W_STROBE generates write strobe port | 0.000s |
| ✅ | `gen.test_gen_007_state_machine_exists` | GEN-007-STATE-MACHINE-EXISTS: GEN-007: State machine logic present | 0.000s |
| ✅ | `gen.test_gen_008_address_decoder` | GEN-008-ADDRESS-DECODER: GEN-008: Address decoder has case statement | 0.000s |
| ✅ | `gen.test_gen_009_base_address_macro` | GEN-009-BASE-ADDRESS-MACRO: GEN-009: Base address macro defined | 0.000s |
| ✅ | `gen.test_gen_009_c_header_compiles` | GEN-009-C-HEADER-COMPILES: GEN-009: C header compiles without warnings | 1.089s |
| ✅ | `gen.test_gen_009_c_header_exists` | GEN-009-C-HEADER-EXISTS: GEN-009: C header file generated | 0.000s |
| ✅ | `gen.test_gen_009_include_guards` | GEN-009-INCLUDE-GUARDS: GEN-009: Header has include guards | 0.000s |
| ✅ | `gen.test_gen_009_offset_macros` | GEN-009-OFFSET-MACROS: GEN-009: Register offset macros defined | 0.000s |
| ✅ | `gen.test_gen_010_struct_definition` | GEN-010-STRUCT-DEFINITION: GEN-010: Struct definition present | 0.000s |
| ✅ | `gen.test_gen_011_xml_exists` | GEN-011-XML-EXISTS: GEN-011: XML file generated | 0.000s |
| ✅ | `gen.test_gen_011_xml_has_registers` | GEN-011-XML-HAS-REGISTERS: GEN-011: XML contains register elements | 0.000s |
| ✅ | `gen.test_gen_011_xml_well_formed` | GEN-011-XML-WELL-FORMED: GEN-011: XML is well-formed | 0.000s |
| ✅ | `gen.test_gen_012_has_module_header` | GEN-012-HAS-MODULE-HEADER: GEN-012: Document has module header | 0.000s |
| ✅ | `gen.test_gen_012_has_register_table` | GEN-012-HAS-REGISTER-TABLE: GEN-012: Document has register table | 0.000s |
| ✅ | `gen.test_gen_012_markdown_exists` | GEN-012-MARKDOWN-EXISTS: GEN-012: Markdown file generated | 0.000s |
| ✅ | `gen.test_gen_012_shows_address` | GEN-012-SHOWS-ADDRESS: GEN-012: Document shows addresses | 0.000s |

## 🚨 Error Handling Tests (ERR-xxx)

### ERR Requirements

**9/9 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `err.test_err_001_address_conflict_exception` | ERR-001-ADDRESS-CONFLICT-EXCEPTION: ERR-001: Duplicate addresses raise AddressConflictError | 0.002s |
| ✅ | `err.test_err_001_exception_has_register_names` | ERR-001-EXCEPTION-HAS-REGISTER-NAMES: ERR-001: Exception includes register names | 0.001s |
| ✅ | `err.test_err_002_binary_file_skipped` | ERR-002-BINARY-FILE-SKIPPED: ERR-002: Binary files are skipped | 0.001s |
| ✅ | `err.test_err_002_nonexistent_file` | ERR-002-NONEXISTENT-FILE: ERR-002: Non-existent file handled gracefully | 0.000s |
| ✅ | `err.test_err_003_no_annotation_skipped` | ERR-003-NO-ANNOTATION-SKIPPED: ERR-003: Files without @axion silently skipped | 0.001s |
| ✅ | `err.test_err_003_only_axion_def_skipped` | ERR-003-ONLY-AXION-DEF-SKIPPED: ERR-003: Files with only @axion_def but no signals skipped | 0.000s |
| ✅ | `err.test_err_004_invalid_hex_address` | ERR-004-INVALID-HEX-ADDRESS: ERR-004: Invalid hex address reports error | 0.001s |
| ✅ | `err.test_err_005_no_entity_skipped` | ERR-005-NO-ENTITY-SKIPPED: ERR-005: Files without entity declaration skipped | 0.001s |
| ✅ | `err.test_err_006_duplicate_signal_detection` | ERR-006-DUPLICATE-SIGNAL-DETECTION: ERR-006: Duplicate signal names detected | 0.001s |

## 🖥️ CLI Tests (CLI-xxx)

### CLI Requirements

**11/11 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `cli.test_cli_001_help_option` | CLI-001-HELP-OPTION: CLI-001: --help displays usage information | 0.098s |
| ✅ | `cli.test_cli_001_help_short_option` | CLI-001-HELP-SHORT-OPTION: CLI-001: -h displays usage information | 0.073s |
| ✅ | `cli.test_cli_002_version_option` | CLI-002-VERSION-OPTION: CLI-002: --version displays version | 0.088s |
| ✅ | `cli.test_cli_003_source_option_long` | CLI-003-SOURCE-OPTION-LONG: CLI-003: --source option specifies source directory | 0.073s |
| ✅ | `cli.test_cli_003_source_option_short` | CLI-003-SOURCE-OPTION-SHORT: CLI-003: -s option specifies source directory | 0.072s |
| ✅ | `cli.test_cli_004_multiple_sources` | CLI-004-MULTIPLE-SOURCES: CLI-004: Multiple -s options accepted | 0.074s |
| ✅ | `cli.test_cli_005_output_option_long` | CLI-005-OUTPUT-OPTION-LONG: CLI-005: --output option specifies output directory | 0.072s |
| ✅ | `cli.test_cli_005_output_option_short` | CLI-005-OUTPUT-OPTION-SHORT: CLI-005: -o option specifies output directory | 0.073s |
| ✅ | `cli.test_cli_006_exclude_option` | CLI-006-EXCLUDE-OPTION: CLI-006: -e option excludes files/directories | 0.075s |
| ✅ | `cli.test_cli_009_invalid_source_error` | CLI-009-INVALID-SOURCE-ERROR: CLI-009: Non-existent source reports error | 0.068s |
| ✅ | `cli.test_cli_010_output_dir_creation` | CLI-010-OUTPUT-DIR-CREATION: CLI-010: Non-existent output directory is created | 0.075s |

## 🔄 CDC Tests (CDC-xxx)

### CDC Requirements

**8/8 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `cdc.test_cdc_001_stage_count_2` | CDC-001-STAGE-COUNT-2: CDC-001: CDC_STAGE=2 generates 2-stage synchronizer | 0.002s |
| ✅ | `cdc.test_cdc_001_stage_count_3` | CDC-001-STAGE-COUNT-3: CDC-001: CDC_STAGE=3 generates 3-stage synchronizer | 0.001s |
| ✅ | `cdc.test_cdc_002_default_stage_count` | CDC-002-DEFAULT-STAGE-COUNT: CDC-002: CDC_EN without CDC_STAGE defaults to 2 stages | 0.001s |
| ✅ | `cdc.test_cdc_003_sync_signal_declaration` | CDC-003-SYNC-SIGNAL-DECLARATION: CDC-003: CDC-enabled modules declare synchronizer signals | 0.001s |
| ✅ | `cdc.test_cdc_004_module_clock_port` | CDC-004-MODULE-CLOCK-PORT: CDC-004: CDC-enabled modules have module_clk port | 0.002s |
| ✅ | `cdc.test_cdc_005_cdc_disabled` | CDC-005-CDC-DISABLED: CDC-005: Without CDC_EN, no CDC signals generated | 0.001s |
| ✅ | `cdc.test_cdc_006_ro_cdc_path` | CDC-006-RO-CDC-PATH: CDC-006: RO registers synchronized from module to AXI domain | 0.001s |
| ✅ | `cdc.test_cdc_007_rw_cdc_path` | CDC-007-RW-CDC-PATH: CDC-007: Writable registers synchronized from AXI to module domain | 0.001s |

## 📍 Address Management Tests (ADDR-xxx)

### ADDR Requirements

**9/9 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `addr.test_addr_001_auto_assign_sequential` | ADDR-001-AUTO-ASSIGN-SEQUENTIAL: ADDR-001: Auto-assigned addresses are sequential | 0.000s |
| ✅ | `addr.test_addr_001_first_addr_zero` | ADDR-001-FIRST-ADDR-ZERO: ADDR-001: First auto-assigned address is 0x00 | 0.001s |
| ✅ | `addr.test_addr_002_manual_address` | ADDR-002-MANUAL-ADDRESS: ADDR-002: ADDR attribute sets specific address | 0.001s |
| ✅ | `addr.test_addr_003_mixed_assignment` | ADDR-003-MIXED-ASSIGNMENT: ADDR-003: Mixed auto and manual addresses work correctly | 0.000s |
| ✅ | `addr.test_addr_004_alignment` | ADDR-004-ALIGNMENT: ADDR-004: Addresses are 4-byte aligned | 0.000s |
| ✅ | `addr.test_addr_005_conflict_detection` | ADDR-005-CONFLICT-DETECTION: ADDR-005: Duplicate addresses raise AddressConflictError | 0.001s |
| ✅ | `addr.test_addr_006_wide_signal_space` | ADDR-006-WIDE-SIGNAL-SPACE: ADDR-006: Wide signals reserve multiple address slots | 0.001s |
| ✅ | `addr.test_addr_007_gaps_preserved` | ADDR-007-GAPS-PRESERVED: ADDR-007: Gaps between manual addresses preserved | 0.001s |
| ✅ | `addr.test_addr_008_base_address_addition` | ADDR-008-BASE-ADDRESS-ADDITION: ADDR-008: BASE_ADDR added to relative addresses | 0.001s |

## 🔥 Stress Tests (STRESS-xxx)

### STRESS Requirements

**6/6 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `stress.test_stress_001_many_registers` | STRESS-001-MANY-REGISTERS: STRESS-001: Support 100+ registers per module | 0.004s |
| ✅ | `stress.test_stress_002_very_wide_signal` | STRESS-002-VERY-WIDE-SIGNAL: STRESS-002: Support 256-bit signals | 0.001s |
| ✅ | `stress.test_stress_003_repeated_analysis` | STRESS-003-REPEATED-ANALYSIS: STRESS-003: Multiple analysis cycles without errors | 0.002s |
| ✅ | `stress.test_stress_004_repeated_generation` | STRESS-004-REPEATED-GENERATION: STRESS-004: Repeated generation cycles without errors | 0.008s |
| ✅ | `stress.test_stress_005_random_addresses` | STRESS-005-RANDOM-ADDRESSES: STRESS-005: Non-sequential address patterns work correctly | 0.001s |
| ✅ | `stress.test_stress_006_boundary_values` | STRESS-006-BOUNDARY-VALUES: STRESS-006: Generation handles all register types | 0.002s |

---
*Generated by `make test` at 2025-12-09 08:16:21*