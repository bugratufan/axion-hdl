# Axion-HDL Test Results

**Overall Status:** ✅ ALL PASSING

## Summary

| Metric | Value |
|--------|-------|
| **Total Tests** | 75 |
| ✅ Passed | 75 |
| ❌ Failed | 0 |
| ⏭️ Skipped | 0 |
| ⏱️ Total Time | 0.90s |
| 🕐 Last Run | 2025-12-04 13:40:06 |

## 🐍 Python Tests

### Unit Tests

**7/7 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `python.unit.init` | Initialize AxionHDL | 0.002s |
| ✅ | `python.unit.add_src` | Add Source Directory | 0.000s |
| ✅ | `python.unit.analyze` | Analyze VHDL Files | 0.003s |
| ✅ | `python.unit.gen_vhdl` | Generate VHDL Modules | 0.003s |
| ✅ | `python.unit.gen_c` | Generate C Headers | 0.002s |
| ✅ | `python.unit.gen_xml` | Generate XML Register Map | 0.002s |
| ✅ | `python.unit.gen_doc` | Generate Markdown Documentation | 0.001s |

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
| ✅ | `c.compile.gcc_check` | GCC Available | 0.002s |
| ✅ | `c.compile.headers` | Compile C Header Test | 0.054s |
| ✅ | `c.compile.run` | Run C Header Test Binary | 0.002s |

## 🔧 VHDL Tests

### Simulation Setup

**1/1 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `vhdl.ghdl.check` | GHDL Available | 0.067s |

### VHDL Analysis

**7/7 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `vhdl.analyze.sensor_controller` | Analyze sensor_controller.vhd | 0.073s |
| ✅ | `vhdl.analyze.spi_controller` | Analyze spi_controller.vhd | 0.071s |
| ✅ | `vhdl.analyze.mixed_width` | Analyze mixed_width_controller.vhd | 0.069s |
| ✅ | `vhdl.analyze.sensor_axion` | Analyze sensor_controller_axion_reg.vhd | 0.073s |
| ✅ | `vhdl.analyze.spi_axion` | Analyze spi_controller_axion_reg.vhd | 0.069s |
| ✅ | `vhdl.analyze.mixed_axion` | Analyze mixed_width_controller_axion_reg.vhd | 0.074s |
| ✅ | `vhdl.analyze.testbench` | Analyze multi_module_tb.vhd | 0.090s |

### Elaboration

**1/1 passed**

| Status | Test ID | Test Name | Duration |
|:------:|:--------|:----------|:--------:|
| ✅ | `vhdl.elaborate.testbench` | Elaborate multi_module_tb | 0.246s |

### Requirements Verification (53 test cases)

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

---
*Generated by `make test` at 2025-12-04 13:40:06*