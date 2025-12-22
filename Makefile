# Makefile for Axion-HDL
# Automated AXI4-Lite Register Interface Generator

.PHONY: all build install dev-install test test-vhdl test-c test-python clean dist upload-test upload help

# Python interpreter
PYTHON := python3
PIP := pip3

# Directories
PROJECT_ROOT := $(shell pwd)
TESTS_DIR := tests
OUTPUT_DIR := output
WORK_DIR := work
WAVEFORMS_DIR := waveforms
DIST_DIR := dist

# GHDL options
GHDL := ghdl
GHDL_STD := --std=08
GHDL_WORKDIR := --workdir=$(WORK_DIR)

# GCC options
GCC := gcc
GCC_FLAGS := -Wall -Wextra -Werror -pedantic -std=c11

# Default target
all: build

#------------------------------------------------------------------------------
# Build & Install
#------------------------------------------------------------------------------

## Build the package (sdist + wheel)
build: clean-dist
	@echo "Building package..."
	$(PYTHON) -m build
	@echo "Build complete. Files in $(DIST_DIR)/"

## Install package locally
install:
	@echo "Installing axion-hdl..."
	$(PIP) install .

## Install in development/editable mode
dev-install:
	@echo "Installing axion-hdl in development mode..."
	$(PIP) install -e ".[dev]"

## Uninstall package
uninstall:
	@echo "Uninstalling axion-hdl..."
	$(PIP) uninstall -y axion-hdl || true

#------------------------------------------------------------------------------
# Testing
#------------------------------------------------------------------------------

## Run all tests with tabular results
test:
	@$(PYTHON) $(TESTS_DIR)/run_tests.py

## Run all tests (legacy format)
test-legacy: test-python test-address-conflict test-c test-vhdl
	@echo ""
	@echo "========================================"
	@echo "  All tests completed successfully!"
	@echo "========================================"

## Run Python tests
test-python:
	@echo "Running Python tests..."
	@$(PYTHON) $(TESTS_DIR)/python/test_axion.py
	@echo "Python tests passed!"

## Run address conflict detection tests
test-address-conflict:
	@echo "Running address conflict detection tests..."
	@$(PYTHON) $(TESTS_DIR)/python/test_address_conflict.py
	@echo "Address conflict detection tests passed!"

## Run C header tests (requires gcc)
test-c: generate
	@echo "Running C header tests..."
	@if command -v $(GCC) &> /dev/null; then \
		$(GCC) $(GCC_FLAGS) -o $(TESTS_DIR)/c/test_c_headers $(TESTS_DIR)/c/test_c_headers.c && \
		./$(TESTS_DIR)/c/test_c_headers && \
		rm -f $(TESTS_DIR)/c/test_c_headers && \
		echo "C header tests passed!"; \
	else \
		echo "Warning: gcc not found, skipping C tests"; \
	fi

## Run VHDL simulation tests (requires ghdl)
## Run VHDL simulation tests (requires ghdl)
test-vhdl: generate
	@echo "Running VHDL simulation tests..."
	@if command -v $(GHDL) &> /dev/null; then \
		mkdir -p $(WORK_DIR) $(WAVEFORMS_DIR) && \
		$(GHDL) -a $(GHDL_STD) $(GHDL_WORKDIR) $(TESTS_DIR)/vhdl/sensor_controller.vhd && \
		$(GHDL) -a $(GHDL_STD) $(GHDL_WORKDIR) $(TESTS_DIR)/vhdl/spi_controller.vhd && \
		$(GHDL) -a $(GHDL_STD) $(GHDL_WORKDIR) $(TESTS_DIR)/vhdl/mixed_width_controller.vhd && \
		$(GHDL) -a $(GHDL_STD) $(GHDL_WORKDIR) $(OUTPUT_DIR)/sensor_controller_axion_reg.vhd && \
		$(GHDL) -a $(GHDL_STD) $(GHDL_WORKDIR) $(OUTPUT_DIR)/spi_controller_axion_reg.vhd && \
		$(GHDL) -a $(GHDL_STD) $(GHDL_WORKDIR) $(OUTPUT_DIR)/mixed_width_controller_axion_reg.vhd && \
		$(GHDL) -a $(GHDL_STD) $(GHDL_WORKDIR) $(TESTS_DIR)/vhdl/multi_module_tb.vhd && \
		$(GHDL) -e $(GHDL_STD) $(GHDL_WORKDIR) multi_module_tb && \
		echo "Running simulation (logging to $(OUTPUT_DIR)/ghdl_run.log)..." && \
		if ! $(GHDL) -r $(GHDL_STD) $(GHDL_WORKDIR) multi_module_tb \
			--assert-level=error --wave=$(WAVEFORMS_DIR)/multi_module_tb_wave.ghw --stop-time=10ms > $(OUTPUT_DIR)/ghdl_run.log 2>&1; then \
			echo "VHDL simulation FAILED. Log output:" ; \
			cat $(OUTPUT_DIR)/ghdl_run.log ; \
			exit 1; \
		else \
			echo "VHDL simulation tests passed!"; \
		fi \
	else \
		echo "Warning: ghdl not found, skipping VHDL tests"; \
	fi

## Run full test script (legacy)
test-full:
	@echo "Running full test script..."
	@bash $(TESTS_DIR)/run_full_test.sh

## Run GUI tests (requires playwright) - Chrome only for speed
test-gui:
	@echo "Running GUI tests on Chrome (4 parallel workers)..."
	@if $(PYTHON) -c "import playwright" 2>/dev/null; then \
		$(PYTHON) -m pytest $(TESTS_DIR)/python/test_gui.py $(TESTS_DIR)/python/test_file_modification.py $(TESTS_DIR)/python/test_gui_property_changes.py -v --tb=short --browser chromium -n 4 --reruns 2 --reruns-delay 1; \
	else \
		echo "Warning: playwright not installed, skipping GUI tests"; \
		echo "Install with: pip install pytest-playwright playwright pytest-xdist pytest-rerunfailures && playwright install"; \
	fi

## Run GUI tests on all browsers (Chrome, Firefox, WebKit)
test-gui-full:
	@echo "Running GUI tests on all browsers (4 parallel workers)..."
	@if $(PYTHON) -c "import playwright" 2>/dev/null; then \
		$(PYTHON) -m pytest $(TESTS_DIR)/python/test_gui.py $(TESTS_DIR)/python/test_file_modification.py $(TESTS_DIR)/python/test_gui_property_changes.py -v --tb=short --browser chromium --browser firefox --browser webkit -n 4 --reruns 2 --reruns-delay 1; \
	else \
		echo "Warning: playwright not installed, skipping GUI tests"; \
		echo "Install with: pip install pytest-playwright playwright pytest-xdist pytest-rerunfailures && playwright install"; \
	fi

#------------------------------------------------------------------------------
# Code Generation
#------------------------------------------------------------------------------

## Generate all outputs from example VHDL files
generate:
	@echo "Generating register modules..."
	@mkdir -p $(OUTPUT_DIR)
	@$(PYTHON) -c "\
from axion_hdl import AxionHDL; \
axion = AxionHDL(output_dir='$(OUTPUT_DIR)'); \
axion.add_src('$(TESTS_DIR)/vhdl'); \
axion.exclude('error_cases'); \
axion.analyze(); \
axion.generate_all()"
	@echo "Generation complete. Files in $(OUTPUT_DIR)/"

## Generate only VHDL modules
generate-vhdl:
	@echo "Generating VHDL modules..."
	@mkdir -p $(OUTPUT_DIR)
	@$(PYTHON) -c "\
from axion_hdl import AxionHDL; \
axion = AxionHDL(output_dir='$(OUTPUT_DIR)'); \
axion.add_src('$(TESTS_DIR)/vhdl'); \
axion.exclude('error_cases'); \
axion.analyze(); \
axion.generate_vhdl()"

## Generate only C headers
generate-headers:
	@echo "Generating C headers..."
	@mkdir -p $(OUTPUT_DIR)
	@$(PYTHON) -c "\
from axion_hdl import AxionHDL; \
axion = AxionHDL(output_dir='$(OUTPUT_DIR)'); \
axion.add_src('$(TESTS_DIR)/vhdl'); \
axion.exclude('error_cases'); \
axion.analyze(); \
axion.generate_c_header()"

## Generate only documentation
generate-docs:
	@echo "Generating documentation..."
	@mkdir -p $(OUTPUT_DIR)
	@$(PYTHON) -c "\
from axion_hdl import AxionHDL; \
axion = AxionHDL(output_dir='$(OUTPUT_DIR)'); \
axion.add_src('$(TESTS_DIR)/vhdl'); \
axion.exclude('error_cases'); \
axion.analyze(); \
axion.generate_documentation(); \
axion.generate_xml()"

#------------------------------------------------------------------------------
# Distribution & Publishing
#------------------------------------------------------------------------------

## Check package for PyPI compatibility
check: build
	@echo "Checking package..."
	$(PYTHON) -m twine check $(DIST_DIR)/*

## Upload to TestPyPI
upload-test: check
	@echo "Uploading to TestPyPI..."
	$(PYTHON) -m twine upload --repository testpypi $(DIST_DIR)/*

## Upload to PyPI (production)
upload: check
	@echo "Uploading to PyPI..."
	$(PYTHON) -m twine upload $(DIST_DIR)/*

#------------------------------------------------------------------------------
# Cleanup
#------------------------------------------------------------------------------

## Clean generated outputs
clean:
	@echo "Cleaning generated files..."
	rm -rf $(OUTPUT_DIR)/*.vhd $(OUTPUT_DIR)/*.h $(OUTPUT_DIR)/*.xml $(OUTPUT_DIR)/*.md
	rm -rf $(WORK_DIR)/*.cf
	rm -rf $(WAVEFORMS_DIR)/*.ghw
	rm -f $(TESTS_DIR)/c/test_c_headers
	rm -rf __pycache__ */__pycache__ */*/__pycache__
	rm -rf *.pyc */*.pyc
	rm -rf .pytest_cache
	@echo "Clean complete."

## Clean distribution files
clean-dist:
	@echo "Cleaning distribution files..."
	rm -rf $(DIST_DIR) build *.egg-info

## Clean everything
clean-all: clean clean-dist
	@echo "Deep clean complete."

#------------------------------------------------------------------------------
# Development
#------------------------------------------------------------------------------

## Format code with black
format:
	@echo "Formatting code..."
	$(PYTHON) -m black axion_hdl tests

## Lint code with flake8
lint:
	@echo "Linting code..."
	$(PYTHON) -m flake8 axion_hdl tests

## Show version
version:
	@$(PYTHON) -c "from axion_hdl import __version__; print(f'axion-hdl version {__version__}')"

## Run CLI help
cli-help:
	@axion-hdl --help

#------------------------------------------------------------------------------
# Waveform Viewer
#------------------------------------------------------------------------------

## Open waveform in GTKWave (requires gtkwave)
wave:
	@if [ -f $(WAVEFORMS_DIR)/multi_module_tb_wave.ghw ]; then \
		gtkwave $(WAVEFORMS_DIR)/multi_module_tb_wave.ghw &; \
	else \
		echo "No waveform file found. Run 'make test-vhdl' first."; \
	fi

#------------------------------------------------------------------------------
# Help
#------------------------------------------------------------------------------

## Show this help message
help:
	@echo ""
	@echo "Axion-HDL Makefile"
	@echo "=================="
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Build & Install:"
	@echo "  build         Build the package (sdist + wheel)"
	@echo "  install       Install package locally"
	@echo "  dev-install   Install in development/editable mode"
	@echo "  uninstall     Uninstall the package"
	@echo ""
	@echo "Testing:"
	@echo "  test          Run all tests (Python + C + VHDL)"
	@echo "  test-python   Run Python tests only"
	@echo "  test-c        Run C header tests only"
	@echo "  test-vhdl     Run VHDL simulation tests only"
	@echo "  test-gui      Run GUI tests (requires playwright)"
	@echo "  test-full     Run full test script (legacy)"
	@echo ""
	@echo "Code Generation:"
	@echo "  generate      Generate all outputs from examples"
	@echo "  generate-vhdl Generate VHDL modules only"
	@echo "  generate-headers Generate C headers only"
	@echo "  generate-docs Generate documentation only"
	@echo ""
	@echo "Distribution:"
	@echo "  check         Check package for PyPI compatibility"
	@echo "  upload-test   Upload to TestPyPI"
	@echo "  upload        Upload to PyPI (production)"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean         Clean generated outputs"
	@echo "  clean-dist    Clean distribution files"
	@echo "  clean-all     Clean everything"
	@echo ""
	@echo "Development:"
	@echo "  format        Format code with black"
	@echo "  lint          Lint code with flake8"
	@echo "  version       Show version"
	@echo "  cli-help      Show CLI help"
	@echo "  wave          Open waveform in GTKWave"
	@echo ""
