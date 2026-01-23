# Cocotb Makefile for Axion-HDL VHDL Testing
#
# This Makefile runs cocotb tests against generated Axion-HDL modules.
#
# Usage:
#   make                    - Run all tests
#   make test_axi_lite      - Run AXI-Lite protocol tests
#   make test_cdc           - Run CDC tests
#   make WAVES=1            - Generate waveforms
#   make GUI=1              - Open waveform viewer after test

# Check if cocotb is installed
COCOTB_CONFIG := $(shell which cocotb-config 2>/dev/null)

ifeq ($(COCOTB_CONFIG),)
$(warning cocotb not installed. Install with: pip install cocotb cocotb-bus cocotbext-axi)

.PHONY: all test_axi_lite test_cdc test_all
all test_axi_lite test_cdc test_all:
	@echo "ERROR: cocotb is not installed."
	@echo "Install with: pip install cocotb cocotb-bus cocotbext-axi"
	@exit 1

else
# cocotb is installed - proceed with normal setup

# Simulator selection
SIM ?= ghdl
TOPLEVEL_LANG ?= vhdl

# VHDL standard
VHDL_STD ?= 08

# Project paths
PROJECT_ROOT := $(shell cd ../.. && pwd)
OUTPUT_DIR := $(PROJECT_ROOT)/output
VHDL_SRC_DIR := $(PROJECT_ROOT)/tests/vhdl
COMMON_DIR := $(PROJECT_ROOT)/axion-common/src

# DUT selection (default to sensor controller)
DUT ?= sensor_controller
TOPLEVEL ?= $(DUT)_axion_reg

# Source files
VHDL_SOURCES += $(COMMON_DIR)/axion_common_pkg.vhd
VHDL_SOURCES += $(VHDL_SRC_DIR)/$(DUT).vhd
VHDL_SOURCES += $(OUTPUT_DIR)/$(DUT)_axion_reg.vhd

# Cocotb configuration
MODULE ?= test_axi_lite
COCOTB_HDL_TIMEUNIT = 1ns
COCOTB_HDL_TIMEPRECISION = 1ps

# GHDL options
GHDL_ARGS += --std=$(VHDL_STD)
GHDL_ARGS += --ieee=synopsys
GHDL_ARGS += -frelaxed-rules

# Waveform generation
ifeq ($(WAVES),1)
    PLUSARGS += --vcd=waveform.vcd
    GHDL_ARGS += --vcd=waveform.vcd
endif

# Extra args for test selection
TESTCASE ?=
ifneq ($(TESTCASE),)
    PLUSARGS += --testcase=$(TESTCASE)
endif

# Results directory
COCOTB_RESULTS_FILE ?= results.xml

# Include cocotb's make rules
include $(shell cocotb-config --makefiles)/Makefile.sim

# Custom targets
.PHONY: test_axi_lite test_cdc test_all clean_cocotb generate

# Run AXI-Lite protocol tests
test_axi_lite:
	$(MAKE) MODULE=test_axi_lite DUT=sensor_controller

# Run CDC tests
test_cdc:
	$(MAKE) MODULE=test_cdc DUT=sensor_controller

# Run all test modules
test_all: test_axi_lite test_cdc

# Generate VHDL before testing
generate:
	@echo "Generating Axion-HDL outputs..."
	cd $(PROJECT_ROOT) && python3 -c "\
from axion_hdl import AxionHDL; \
axion = AxionHDL(output_dir='$(OUTPUT_DIR)'); \
axion.add_src('$(VHDL_SRC_DIR)'); \
axion.exclude('error_cases'); \
axion.analyze(); \
axion.generate_vhdl()"

# Clean cocotb artifacts
clean_cocotb:
	rm -rf __pycache__ *.vcd *.xml sim_build results.xml

endif

# Help (always available)
.PHONY: help
help:
	@echo "Cocotb Test Targets:"
	@echo "  make                 - Run default test module"
	@echo "  make test_axi_lite   - Run AXI-Lite protocol tests"
	@echo "  make test_cdc        - Run CDC tests"
	@echo "  make test_all        - Run all test modules"
	@echo ""
	@echo "Options:"
	@echo "  DUT=name             - Select DUT (sensor_controller, spi_controller, etc.)"
	@echo "  MODULE=name          - Select test module"
	@echo "  TESTCASE=name        - Run specific test case"
	@echo "  WAVES=1              - Generate waveforms"
	@echo "  GUI=1                - Open waveform viewer"
	@echo ""
	@echo "Examples:"
	@echo "  make DUT=spi_controller MODULE=test_axi_lite"
	@echo "  make test_cdc WAVES=1"
	@echo "  make TESTCASE=test_axion_001_ro_read"
