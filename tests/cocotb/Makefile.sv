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

# Custom target to generate SV
.PHONY: generate
generate:
	@echo "Generating SystemVerilog for $(DUT)..."
	cd $(PROJECT_ROOT) && python3 -c "\
from axion_hdl import AxionHDL; \
axion = AxionHDL(output_dir='$(OUTPUT_DIR)'); \
axion.add_src('$(TESTS_DIR)/vhdl/$(DUT).vhd'); \
axion.exclude('error_cases'); \
axion.analyze(); \
axion.generate_systemverilog()"
