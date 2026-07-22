# Makefile for SystemVerilog Verification using Verilator

SIM ?= verilator
TOPLEVEL_LANG ?= verilog

# Project paths
PROJECT_ROOT := $(shell cd ../.. && pwd)
TESTS_DIR := $(PROJECT_ROOT)/tests
OUTPUT_DIR := $(PROJECT_ROOT)/output

# Default DUT
DUT ?= sensor_controller
TOPLEVEL ?= $(DUT)_axion_reg
MODULE ?= test_sv_basic

# Verilator specific flags
# --trace-structs ensures packed structs are visible in waves
EXTRA_ARGS += --trace --trace-structs --Wno-fatal

# Sources
# Note: This assumes 'generate' target has been run to produce the SV file
VERILOG_SOURCES += $(OUTPUT_DIR)/$(DUT)_axion_reg.sv

# Include cocotb makefiles
include $(shell cocotb-config --makefiles)/Makefile.sim

# Custom targets
.PHONY: test_sv_basic test_cdc test_cdc_stage2 test_cdc_packed test_cdc_packed_stage2 generate

# Run basic SV smoke test
test_sv_basic: generate
	$(MAKE) MODULE=test_sv_basic

# Run CDC tests (mirrors tests/cocotb/test_cdc.py against the SV/Verilator DUT)
test_cdc: generate
	$(MAKE) MODULE=test_sv_cdc

# Run CDC tests against a different CDC_STAGE depth (2, vs. sensor_controller's
# 3) to prove the strobe/data synchronizers work correctly regardless of the
# configured stage count, not just the default.
test_cdc_stage2: generate
	$(MAKE) MODULE=test_sv_cdc DUT=sensor_controller_stage2

# Run packed/wide-register CDC tests (SV parity for test_cdc_packed.py).
test_cdc_packed: generate
	$(MAKE) MODULE=test_sv_cdc_packed DUT=cdc_packed_controller

# Same packed/wide CDC tests against the CDC_STAGE=2 DUT variant.
test_cdc_packed_stage2: generate
	$(MAKE) MODULE=test_sv_cdc_packed DUT=cdc_packed_controller_stage2

# Custom target to generate SV
generate:
	@echo "Generating SystemVerilog for $(DUT)..."
	cd $(PROJECT_ROOT) && python3 -c "\
from axion_hdl import AxionHDL; \
axion = AxionHDL(output_dir='$(OUTPUT_DIR)'); \
axion.add_src('$(TESTS_DIR)/vhdl/$(DUT).vhd'); \
axion.exclude('error_cases'); \
axion.analyze(); \
axion.generate_systemverilog()"
