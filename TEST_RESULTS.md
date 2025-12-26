# Axion-HDL Test Results

**Overall Status:** ❌ FAILING

## Summary

| Metric | Value |
|--------|-------|
| **Total Tests** | 251 |
| ✅ Passed | 250 |
| ❌ Failed | 1 |
| ⏭️ Skipped | 0 |
| ⏱️ Total Time | 3.21s |
| 🕐 Last Run | 2025-12-26 21:33:25 |

## 🐍 Python Tests

### Unit Tests

**7/7 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `python.unit.init` | Initialize AxionHDL | 0.000s |
| ✅ | `python.unit.add_src` | Add Source Directory | 0.000s |
| ✅ | `python.unit.analyze` | Analyze VHDL Files | 0.004s |
| ✅ | `python.unit.gen_vhdl` | Generate VHDL Modules | 0.005s |
| ✅ | `python.unit.gen_c` | Generate C Headers | 0.004s |
| ✅ | `python.unit.gen_xml` | Generate XML Register Map | 0.003s |
| ✅ | `python.unit.gen_doc` | Generate Markdown Documentation | 0.003s |

### Address Conflict Tests

**3/3 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `python.conflict.basic` | Basic Address Conflict Detection | 0.001s |
| ✅ | `python.conflict.no_false_positive` | No False Positive (Unique Addresses) | 0.000s |
| ✅ | `python.conflict.wide_signal` | Wide Signal Address Overlap | 0.000s |

## ⚙️ C Tests

### Compilation Tests

**3/3 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `c.compile.gcc_check` | GCC Available | 0.001s |
| ✅ | `c.compile.headers` | Compile C Header Test | 0.136s |
| ✅ | `c.compile.run` | Run C Header Test Binary | 0.001s |

## 🔧 VHDL Tests

### Simulation Setup

**2/2 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `vhdl.ghdl.check` | GHDL Available | 0.005s |
| ✅ | `vhdl.run.subregister_tb` | SUB-VHDL: Run subregister_test_tb Simulation | 0.109s |

### VHDL Analysis

**13/13 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `vhdl.analyze.sensor_controller` | Analyze sensor_controller.vhd | 0.011s |
| ✅ | `vhdl.analyze.sensor_axion` | Analyze sensor_controller_axion_reg.vhd | 0.015s |
| ✅ | `vhdl.analyze.spi_controller` | Analyze spi_controller.vhd | 0.011s |
| ✅ | `vhdl.analyze.spi_axion` | Analyze spi_controller_axion_reg.vhd | 0.013s |
| ✅ | `vhdl.analyze.mixed_width` | Analyze mixed_width_controller.vhd | 0.011s |
| ✅ | `vhdl.analyze.mixed_axion` | Analyze mixed_width_controller_axion_reg.vhd | 0.016s |
| ✅ | `vhdl.analyze.subregister_test` | SUB-VHDL: Analyze subregister_test.vhd | 0.011s |
| ✅ | `vhdl.analyze.subregister_axion` | SUB-VHDL: Analyze generated subregister_test_axion_reg.vhd | 0.013s |
| ✅ | `vhdl.analyze.subregister_tb` | SUB-VHDL: Analyze subregister_test_tb.vhd | 0.014s |
| ✅ | `vhdl.analyze.sensor_axion` | Analyze sensor_controller_axion_reg.vhd | 0.015s |
| ✅ | `vhdl.analyze.spi_axion` | Analyze spi_controller_axion_reg.vhd | 0.014s |
| ✅ | `vhdl.analyze.mixed_axion` | Analyze mixed_width_controller_axion_reg.vhd | 0.017s |
| ✅ | `vhdl.analyze.testbench` | Analyze multi_module_tb.vhd | 0.026s |

### Generate

**1/1 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `vhdl.generate.subregister` | SUB-VHDL: Generate subregister_test_axion_reg.vhd | 0.005s |

### Elaboration

**1/1 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `vhdl.elaboration.subregister_tb` | SUB-VHDL: Elaborate subregister_test_tb | 0.106s |

### Elaboration

**1/1 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `vhdl.elaborate.testbench` | Elaborate multi_module_tb | 0.201s |

### Xml

**5/5 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `vhdl.xml.generate` | XML: Generate VHDL from tests/xml/subregister_test.xml | 0.003s |
| ✅ | `vhdl.xml.analyze_gen` | XML: Analyze generated subregister_test_xml_axion_reg.vhd | 0.013s |
| ✅ | `vhdl.xml.analyze_tb` | XML: Analyze subregister_xml_test_tb.vhd | 0.014s |
| ✅ | `vhdl.xml.elaborate` | XML: Elaborate subregister_xml_test_tb | 0.105s |
| ✅ | `vhdl.xml.run` | XML: Run subregister_xml_test_tb | 0.107s |

### Requirements Verification (AXION/AXI-LITE)

**53/53 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `vhdl.req.axion_001` | AXION-001: Read-Only Register Read Access | 0.000s |
| ✅ | `vhdl.req.axion_002` | AXION-002: Read-Only Register Write Protection | 0.000s |
| ✅ | `vhdl.req.axion_003` | AXION-003: Write-Only Register Write Access | 0.000s |
| ✅ | `vhdl.req.axion_004` | AXION-004: Write-Only Register Read Protection | 0.000s |
| ✅ | `vhdl.req.axion_005` | AXION-005: Read-Write Register Full Access | 0.000s |
| ✅ | `vhdl.req.axion_006` | AXION-006: Register Address Mapping | 0.000s |
| ✅ | `vhdl.req.axion_007` | AXION-007: Base Address Offset Calculation | 0.000s |
| ✅ | `vhdl.req.axion_008` | AXION-008: Module Address Space Isolation | 0.000s |
| ✅ | `vhdl.req.axion_009` | AXION-009: AXI Write Response Error Signaling | 0.000s |
| ✅ | `vhdl.req.axion_010` | AXION-010: AXI Read Response Error Signaling | 0.000s |
| ✅ | `vhdl.req.axion_011` | AXION-011: AXI Write Transaction Handshake | 0.000s |
| ✅ | `vhdl.req.axion_012` | AXION-012: AXI Read Transaction Handshake | 0.000s |
| ✅ | `vhdl.req.axion_013` | AXION-013: Read Strobe Signal Generation | 0.000s |
| ✅ | `vhdl.req.axion_014` | AXION-014: Write Strobe Signal Generation | 0.000s |
| ✅ | `vhdl.req.axion_015` | AXION-015: Write Enable Signal Generation | 0.000s |
| ✅ | `vhdl.req.axion_016` | AXION-016: Byte-Level Write Strobe Support | 0.000s |
| ✅ | `vhdl.req.axion_017` | AXION-017: Synchronous Reset | 0.000s |
| ✅ | `vhdl.req.axion_018` | AXION-018: Clock Domain Crossing | 0.000s |
| ✅ | `vhdl.req.axion_019` | AXION-019: Documentation Generation | 0.000s |
| ✅ | `vhdl.req.axion_020` | AXION-020: Unaligned Address Access | 0.000s |
| ✅ | `vhdl.req.axion_021` | AXION-021: Out-of-Range Address Access | 0.000s |
| ✅ | `vhdl.req.axion_022` | AXION-022: Concurrent Read and Write Operations | 0.000s |
| ✅ | `vhdl.req.axion_023` | AXION-023: Default Register Values | 0.000s |
| ✅ | `vhdl.req.axion_024` | AXION-024: Register Bit Field Support | 0.000s |
| ✅ | `vhdl.req.axion_025a` | AXION-025a: Wide signal support (48-bit) - lower 32 bits | 0.000s |
| ✅ | `vhdl.req.axion_025b` | AXION-025b: Wide signal support (64-bit) - lower 32 bits | 0.000s |
| ✅ | `vhdl.req.axion_025c` | AXION-025c: Wide signal support (100-bit) - lower 32 bits | 0.000s |
| ✅ | `vhdl.req.axion_025d` | AXION-025d: Wide signal support (200-bit) - lower 32 bits | 0.000s |
| ✅ | `vhdl.req.axion_025e` | AXION-025e: Narrow signal support (1-bit) | 0.000s |
| ✅ | `vhdl.req.axion_025f` | AXION-025f: Narrow signal support (6-bit) | 0.000s |
| ✅ | `vhdl.req.axion_025g` | AXION-025g: Narrow signal support (16-bit) | 0.000s |
| ✅ | `vhdl.req.axion_026a` | AXION-026a: Multi-register access (48-bit) - upper bits | 0.000s |
| ✅ | `vhdl.req.axion_026b` | AXION-026b: Multi-register access (64-bit) - upper bits | 0.000s |
| ✅ | `vhdl.req.axion_026c` | AXION-026c: Multi-register access (100-bit) - bits [63:32] | 0.000s |
| ✅ | `vhdl.req.axion_026d` | AXION-026d: Multi-register access (100-bit) - highest bits | 0.000s |
| ✅ | `vhdl.req.axion_026e` | AXION-026e: Multi-register access (200-bit) - highest bits | 0.000s |
| ✅ | `vhdl.req.axion_026f` | AXION-026f: Address map integrity after wide signals | 0.000s |
| ✅ | `vhdl.req.axi_lite_001` | AXI-LITE-001: Reset State Requirements | 0.000s |
| ✅ | `vhdl.req.axi_lite_003` | AXI-LITE-003: VALID Before READY Dependency | 0.000s |
| ✅ | `vhdl.req.axi_lite_004` | AXI-LITE-004: VALID Stability Rule | 0.000s |
| ✅ | `vhdl.req.axi_lite_005a` | AXI-LITE-005a: Write Address/Data Independence (Addr First) | 0.000s |
| ✅ | `vhdl.req.axi_lite_005b` | AXI-LITE-005b: Write Address/Data Independence (Data First) | 0.000s |
| ✅ | `vhdl.req.axi_lite_006` | AXI-LITE-006: Back-to-Back Transaction Support | 0.000s |
| ✅ | `vhdl.req.axi_lite_007` | AXI-LITE-007: Write Response Timing | 0.000s |
| ✅ | `vhdl.req.axi_lite_008` | AXI-LITE-008: Read Response Timing | 0.000s |
| ✅ | `vhdl.req.axi_lite_014a` | AXI-LITE-014a: Response Code Compliance (OKAY) | 0.000s |
| ✅ | `vhdl.req.axi_lite_014b` | AXI-LITE-014b: Response Code Compliance (SLVERR) | 0.000s |
| ✅ | `vhdl.req.axi_lite_016a` | AXI-LITE-016a: Delayed READY Handling (Write) | 0.000s |
| ✅ | `vhdl.req.axi_lite_016b` | AXI-LITE-016b: Delayed READY Handling (Read) | 0.000s |
| ✅ | `vhdl.req.axi_lite_017a` | AXI-LITE-017a: Early READY Handling (Write) | 0.000s |
| ✅ | `vhdl.req.axi_lite_017b` | AXI-LITE-017b: Early READY Handling (Read) | 0.000s |
| ✅ | `vhdl.req.axi_lite_015` | AXI-LITE-015: Clock Edge Alignment | 0.000s |
| ✅ | `vhdl.req.axi_lite_002` | AXI-LITE-002: Single Transfer Per Transaction | 0.000s |

## 📜 Parser Tests (PARSER-xxx)

### PARSER Requirements

**20/20 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `parser.test_parser_001_basic_entity_extraction` | PARSER-001-BASIC-ENTITY-EXTRACTION: PARSER-001: Basic entity name extraction | 0.000s |
| ✅ | `parser.test_parser_001_entity_with_whitespace` | PARSER-001-ENTITY-WITH-WHITESPACE: PARSER-001: Entity extraction with varying whitespace | 0.000s |
| ✅ | `parser.test_parser_001_no_entity` | PARSER-001-NO-ENTITY: PARSER-001: File without entity declaration | 0.000s |
| ✅ | `parser.test_parser_002_std_logic` | PARSER-002-STD-LOGIC: PARSER-002: Parse std_logic as 1-bit | 0.000s |
| ✅ | `parser.test_parser_002_std_logic_vector_downto` | PARSER-002-STD-LOGIC-VECTOR-DOWNTO: PARSER-002: Parse std_logic_vector(N downto M) | 0.000s |
| ✅ | `parser.test_parser_002_std_logic_vector_with_spaces` | PARSER-002-STD-LOGIC-VECTOR-WITH-SPACES: PARSER-002: Parse std_logic_vector with extra spaces | 0.000s |
| ✅ | `parser.test_parser_003_access_modes` | PARSER-003-ACCESS-MODES: PARSER-003: Parse RO, RW, WO access modes | 0.000s |
| ✅ | `parser.test_parser_003_multiple_attributes_same_line` | PARSER-003-MULTIPLE-ATTRIBUTES-SAME-LINE: PARSER-003: Multiple attributes on single line | 0.000s |
| ✅ | `parser.test_parser_003_strobe_flags` | PARSER-003-STROBE-FLAGS: PARSER-003: Parse R_STROBE and W_STROBE flags | 0.000s |
| ✅ | `parser.test_parser_004_base_addr_hex` | PARSER-004-BASE-ADDR-HEX: PARSER-004: Parse BASE_ADDR in hex format | 0.000s |
| ✅ | `parser.test_parser_004_cdc_enable` | PARSER-004-CDC-ENABLE: PARSER-004: Parse CDC_EN flag | 0.000s |
| ✅ | `parser.test_parser_004_cdc_stage` | PARSER-004-CDC-STAGE: PARSER-004: Parse CDC_STAGE attribute | 0.000s |
| ✅ | `parser.test_parser_004_missing_axion_def_defaults` | PARSER-004-MISSING-AXION-DEF-DEFAULTS: PARSER-004: Default values when @axion_def missing | 0.000s |
| ✅ | `parser.test_parser_005_decimal_address` | PARSER-005-DECIMAL-ADDRESS: PARSER-005: Parse decimal address (16) | 0.000s |
| ✅ | `parser.test_parser_005_hex_address` | PARSER-005-HEX-ADDRESS: PARSER-005: Parse hex address (0x10) | 0.000s |
| ✅ | `parser.test_parser_005_upper_case_hex` | PARSER-005-UPPER-CASE-HEX: PARSER-005: Parse uppercase hex (0X10) | 0.000s |
| ✅ | `parser.test_parser_006_desc_with_special_chars` | PARSER-006-DESC-WITH-SPECIAL-CHARS: PARSER-006: Parse description with special characters | 0.000s |
| ✅ | `parser.test_parser_006_double_quoted_desc` | PARSER-006-DOUBLE-QUOTED-DESC: PARSER-006: Parse double-quoted description | 0.000s |
| ✅ | `parser.test_parser_007_exclude_directory` | PARSER-007-EXCLUDE-DIRECTORY: PARSER-007: Exclude directory by name | 0.001s |
| ✅ | `parser.test_parser_008_recursive_scan` | PARSER-008-RECURSIVE-SCAN: PARSER-008: Recursively scan subdirectories | 0.001s |

## 🏭 Code Generation Tests (GEN-xxx)

### GEN Requirements

**44/44 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `gen.test_gen_001_entity_name_pattern` | GEN-001-ENTITY-NAME-PATTERN: GEN-001: Entity name follows pattern <module>_axion_reg | 0.000s |
| ✅ | `gen.test_gen_001_vhdl_compiles` | GEN-001-VHDL-COMPILES: GEN-001: Generated VHDL compiles without errors | 0.014s |
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
| ✅ | `gen.test_gen_009_c_header_compiles` | GEN-009-C-HEADER-COMPILES: GEN-009: C header compiles without warnings | 0.055s |
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
| ✅ | `gen.test_gen_013_yaml_map_exists` | GEN-013-YAML-MAP-EXISTS: GEN-013: YAML register map file generated | 0.001s |
| ✅ | `gen.test_gen_013_yaml_valid_syntax` | GEN-013-YAML-VALID-SYNTAX: GEN-013: YAML file has valid syntax and structure | 0.003s |
| ✅ | `gen.test_gen_014_json_map_exists` | GEN-014-JSON-MAP-EXISTS: GEN-014: JSON register map file generated | 0.000s |
| ✅ | `gen.test_gen_014_json_valid_syntax` | GEN-014-JSON-VALID-SYNTAX: GEN-014: JSON file has valid syntax and structure | 0.000s |
| ✅ | `gen.test_gen_015_html_exists` | GEN-015-HTML-EXISTS: GEN-015: HTML file generated | 0.000s |
| ✅ | `gen.test_gen_015_html_has_doctype` | GEN-015-HTML-HAS-DOCTYPE: GEN-015: HTML has proper DOCTYPE | 0.000s |
| ✅ | `gen.test_gen_015_html_has_module_name` | GEN-015-HTML-HAS-MODULE-NAME: GEN-015: HTML has module name | 0.000s |
| ✅ | `gen.test_gen_015_html_has_style` | GEN-015-HTML-HAS-STYLE: GEN-015: HTML has embedded CSS | 0.000s |
| ✅ | `gen.test_gen_015_html_has_table` | GEN-015-HTML-HAS-TABLE: GEN-015: HTML has register table | 0.000s |
| ✅ | `gen.test_gen_016_pdf_exists_or_skipped` | GEN-016-PDF-EXISTS-OR-SKIPPED: GEN-016: PDF file generated or skipped if weasyprint unavailable | 0.000s |
| ✅ | `gen.test_gen_016_pdf_valid_if_exists` | GEN-016-PDF-VALID-IF-EXISTS: GEN-016: PDF has valid header if generated | 0.000s |
| ✅ | `gen.test_gen_017_address_range_display` | GEN-017-ADDRESS-RANGE-DISPLAY: GEN-017: Address range displayed in documentation | 0.000s |
| ✅ | `gen.test_gen_017_address_range_in_module` | GEN-017-ADDRESS-RANGE-IN-MODULE: GEN-017: Module has calculated address range | 0.000s |
| ✅ | `gen.test_overwrite_existing_file` | AXION-027: Verify that generation overwrites an existing file with the same name. | 0.001s |

## 🚨 Error Handling Tests (ERR-xxx)

### Setup

**0/1 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ❌ | `err.import` | ERR: Import test module | 0.000s |

<details>
<summary>❌ Failure Details</summary>

**err.import**: ERR: Import test module
```
No module named 'pytest'
```

</details>

## 🖥️ CLI Tests (CLI-xxx)

### CLI Requirements

**18/18 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `cli.test_cli_001_help_option` | CLI-001-HELP-OPTION: CLI-001: --help displays usage information | 0.073s |
| ✅ | `cli.test_cli_001_help_short_option` | CLI-001-HELP-SHORT-OPTION: CLI-001: -h displays usage information | 0.085s |
| ✅ | `cli.test_cli_002_version_option` | CLI-002-VERSION-OPTION: CLI-002: --version displays version | 0.068s |
| ✅ | `cli.test_cli_003_source_file_vhdl` | CLI-003-SOURCE-FILE-VHDL: CLI-003: -s accepts single VHDL file | 0.070s |
| ✅ | `cli.test_cli_003_source_file_xml` | CLI-003-SOURCE-FILE-XML: CLI-003: -s accepts single XML file | 0.070s |
| ✅ | `cli.test_cli_003_source_option_long` | CLI-003-SOURCE-OPTION-LONG: CLI-003: --source option specifies source directory | 0.080s |
| ✅ | `cli.test_cli_003_source_option_short` | CLI-003-SOURCE-OPTION-SHORT: CLI-003: -s option specifies source directory | 0.090s |
| ✅ | `cli.test_cli_004_mixed_files_and_dirs` | CLI-004-MIXED-FILES-AND-DIRS: CLI-004: -s accepts mix of files and directories | 0.071s |
| ✅ | `cli.test_cli_004_multiple_sources` | CLI-004-MULTIPLE-SOURCES: CLI-004: Multiple -s options accepted | 0.106s |
| ✅ | `cli.test_cli_005_output_option_long` | CLI-005-OUTPUT-OPTION-LONG: CLI-005: --output option specifies output directory | 0.130s |
| ✅ | `cli.test_cli_005_output_option_short` | CLI-005-OUTPUT-OPTION-SHORT: CLI-005: -o option specifies output directory | 0.154s |
| ✅ | `cli.test_cli_006_exclude_option` | CLI-006-EXCLUDE-OPTION: CLI-006: -e option excludes files/directories | 0.173s |
| ✅ | `cli.test_cli_009_invalid_source_error` | CLI-009-INVALID-SOURCE-ERROR: CLI-009: Non-existent source reports error | 0.068s |
| ✅ | `cli.test_cli_010_output_dir_creation` | CLI-010-OUTPUT-DIR-CREATION: CLI-010: Non-existent output directory is created | 0.191s |
| ✅ | `cli.test_cli_011_yaml_output_flag` | CLI-011-YAML-OUTPUT-FLAG: CLI-011: --yaml flag generates YAML register map | 0.162s |
| ✅ | `cli.test_cli_012_json_output_flag` | CLI-012-JSON-OUTPUT-FLAG: CLI-012: --json flag generates JSON register map | 0.143s |
| ✅ | `cli.test_cli_013_config_file_support` | CLI-013-CONFIG-FILE-SUPPORT: CLI-013: --config loads settings from JSON file | 0.234s |
| ✅ | `cli.test_cli_015_auto_load_config` | CLI-015-AUTO-LOAD-CONFIG: CLI-015: Auto-load .axion_conf if no --config specified | 0.071s |

## 🔄 CDC Tests (CDC-xxx)

### CDC Requirements

**9/9 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `cdc.test_cdc_001_stage_count_2` | CDC-001-STAGE-COUNT-2: CDC-001: CDC_STAGE=2 generates 2-stage synchronizer | 0.001s |
| ✅ | `cdc.test_cdc_001_stage_count_3` | CDC-001-STAGE-COUNT-3: CDC-001: CDC_STAGE=3 generates 3-stage synchronizer | 0.001s |
| ✅ | `cdc.test_cdc_002_default_stage_count` | CDC-002-DEFAULT-STAGE-COUNT: CDC-002: CDC_EN without CDC_STAGE defaults to 2 stages | 0.001s |
| ✅ | `cdc.test_cdc_003_sync_signal_declaration` | CDC-003-SYNC-SIGNAL-DECLARATION: CDC-003: CDC-enabled modules declare synchronizer signals | 0.001s |
| ✅ | `cdc.test_cdc_004_module_clock_port` | CDC-004-MODULE-CLOCK-PORT: CDC-004: CDC-enabled modules have module_clk port | 0.001s |
| ✅ | `cdc.test_cdc_005_cdc_disabled` | CDC-005-CDC-DISABLED: CDC-005: Without CDC_EN, no CDC signals generated | 0.001s |
| ✅ | `cdc.test_cdc_006_ro_cdc_path` | CDC-006-RO-CDC-PATH: CDC-006: RO registers synchronized from module to AXI domain | 0.001s |
| ✅ | `cdc.test_cdc_007_rw_cdc_path` | CDC-007-RW-CDC-PATH: CDC-007: Writable registers synchronized from AXI to module domain | 0.001s |
| ✅ | `cdc.test_cdc_008_equivalence` | CDC-008-EQUIVALENCE: CDC-008: CDC_EN flag is equivalent to CDC_EN=true | 0.002s |

## 📍 Address Management Tests (ADDR-xxx)

### ADDR Requirements

**9/9 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `addr.test_addr_001_auto_assign_sequential` | ADDR-001-AUTO-ASSIGN-SEQUENTIAL: ADDR-001: Auto-assigned addresses are sequential | 0.000s |
| ✅ | `addr.test_addr_001_first_addr_zero` | ADDR-001-FIRST-ADDR-ZERO: ADDR-001: First auto-assigned address is 0x00 | 0.000s |
| ✅ | `addr.test_addr_002_manual_address` | ADDR-002-MANUAL-ADDRESS: ADDR-002: ADDR attribute sets specific address | 0.000s |
| ✅ | `addr.test_addr_003_mixed_assignment` | ADDR-003-MIXED-ASSIGNMENT: ADDR-003: Mixed auto and manual addresses work correctly | 0.000s |
| ✅ | `addr.test_addr_004_alignment` | ADDR-004-ALIGNMENT: ADDR-004: Addresses are 4-byte aligned | 0.000s |
| ✅ | `addr.test_addr_005_conflict_detection` | ADDR-005-CONFLICT-DETECTION: ADDR-005: Duplicate addresses raise AddressConflictError | 0.000s |
| ✅ | `addr.test_addr_006_wide_signal_space` | ADDR-006-WIDE-SIGNAL-SPACE: ADDR-006: Wide signals reserve multiple address slots | 0.000s |
| ✅ | `addr.test_addr_007_gaps_preserved` | ADDR-007-GAPS-PRESERVED: ADDR-007: Gaps between manual addresses preserved | 0.000s |
| ✅ | `addr.test_addr_008_base_address_addition` | ADDR-008-BASE-ADDRESS-ADDITION: ADDR-008: BASE_ADDR added to relative addresses | 0.000s |

## 🔥 Stress Tests (STRESS-xxx)

### STRESS Requirements

**6/6 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `stress.test_stress_001_many_registers` | STRESS-001-MANY-REGISTERS: STRESS-001: Support 100+ registers per module | 0.002s |
| ✅ | `stress.test_stress_002_very_wide_signal` | STRESS-002-VERY-WIDE-SIGNAL: STRESS-002: Support 256-bit signals | 0.000s |
| ✅ | `stress.test_stress_003_repeated_analysis` | STRESS-003-REPEATED-ANALYSIS: STRESS-003: Multiple analysis cycles without errors | 0.001s |
| ✅ | `stress.test_stress_004_repeated_generation` | STRESS-004-REPEATED-GENERATION: STRESS-004: Repeated generation cycles without errors | 0.004s |
| ✅ | `stress.test_stress_005_random_addresses` | STRESS-005-RANDOM-ADDRESSES: STRESS-005: Non-sequential address patterns work correctly | 0.000s |
| ✅ | `stress.test_stress_006_boundary_values` | STRESS-006-BOUNDARY-VALUES: STRESS-006: Generation handles all register types | 0.001s |

---
*Generated by `make test` at 2025-12-26 21:33:25*