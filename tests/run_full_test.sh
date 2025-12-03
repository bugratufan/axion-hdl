#!/bin/bash

################################################################################
# Axion Full Requirements Test Script
# This script generates register modules and runs comprehensive verification
# Including:
#   - VHDL generation and compilation
#   - AXI4-Lite protocol testbench simulation
#   - C header compilation and validation tests
################################################################################

set -e  # Exit on error

# Get script directory (tests/)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Change to project root
cd "$PROJECT_ROOT"

# Color definitions for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Axion HDL Requirements Verification${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Clean previous outputs
echo -e "${YELLOW}[1/7] Cleaning previous outputs...${NC}"
rm -rf output/*.vhd output/*.h output/*.xml output/*.md
rm -f work/*.cf waveforms/*.ghw
rm -f tests/c/test_c_headers
echo -e "${GREEN}✓ Cleanup complete${NC}"
echo ""

# Step 2: Generate register modules using Axion
echo -e "${YELLOW}[2/7] Generating register modules with Axion...${NC}"
python3 << 'PYTHON_SCRIPT'
from axion_hdl import AxionHDL

# Initialize Axion
axion = AxionHDL(output_dir="./output")

# Add source directories (use tests/vhdl for example files)
axion.add_src("./tests/vhdl")

# Analyze source files
print("\n--- Analyzing VHDL files ---")
if axion.analyze():
    print("\n--- Generating outputs ---")
    axion.generate_vhdl()
    axion.generate_documentation(format="md")
    axion.generate_xml()
    axion.generate_c_header()
    print("\n✓ Generation complete")
else:
    print("\n✗ Analysis failed")
    exit(1)
PYTHON_SCRIPT

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Register modules generated successfully${NC}"
else
    echo -e "${RED}✗ Generation failed${NC}"
    exit 1
fi
echo ""

# Step 3: Compile C headers and run C tests
echo -e "${YELLOW}[3/7] Compiling and testing C headers...${NC}"

# Check if gcc is available
if ! command -v gcc &> /dev/null; then
    echo -e "${YELLOW}⚠ gcc not found, skipping C header tests${NC}"
else
    # Compile C test
    gcc -Wall -Wextra -Werror -pedantic -std=c11 \
        -o tests/c/test_c_headers tests/c/test_c_headers.c
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ C header compilation successful${NC}"
        
        # Run C tests
        echo -e "${BLUE}Running C header validation tests...${NC}"
        ./tests/c/test_c_headers
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ C header tests passed${NC}"
        else
            echo -e "${RED}✗ C header tests failed${NC}"
            exit 1
        fi
    else
        echo -e "${RED}✗ C header compilation failed${NC}"
        exit 1
    fi
fi
echo ""

# Step 4: Compile VHDL files
echo -e "${YELLOW}[4/7] Compiling VHDL design and testbench...${NC}"

# Ensure work directory exists
mkdir -p work waveforms

# Compile in correct dependency order
ghdl -a --std=08 --workdir=work tests/vhdl/sensor_controller.vhd
ghdl -a --std=08 --workdir=work tests/vhdl/spi_controller.vhd
ghdl -a --std=08 --workdir=work output/sensor_controller_axion_reg.vhd
ghdl -a --std=08 --workdir=work output/spi_controller_axion_reg.vhd
ghdl -a --std=08 --workdir=work tests/vhdl/multi_module_tb.vhd

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Compilation successful${NC}"
else
    echo -e "${RED}✗ Compilation failed${NC}"
    exit 1
fi
echo ""

# Step 5: Elaborate testbench
echo -e "${YELLOW}[5/7] Elaborating testbench...${NC}"
ghdl -e --std=08 --workdir=work multi_module_tb

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Elaboration successful${NC}"
else
    echo -e "${RED}✗ Elaboration failed${NC}"
    exit 1
fi
echo ""

# Step 6: Run VHDL simulation
echo -e "${YELLOW}[6/7] Running VHDL simulation and verification...${NC}"
echo -e "${BLUE}----------------------------------------${NC}"
ghdl -r --std=08 --workdir=work multi_module_tb --wave=waveforms/multi_module_tb_wave.ghw --stop-time=100us

if [ $? -eq 0 ]; then
    echo -e "${BLUE}----------------------------------------${NC}"
    echo ""
    echo -e "${GREEN}✓ VHDL simulation completed successfully${NC}"
    echo ""
    
    # Step 7: Final Summary
    echo -e "${YELLOW}[7/7] Final Summary...${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}All tests completed successfully!${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "Test Outputs:"
    echo -e "  - VHDL Modules:    ${YELLOW}output/*.vhd${NC}"
    echo -e "  - C Headers:       ${YELLOW}output/*.h${NC}"
    echo -e "  - Documentation:   ${YELLOW}output/*.md, output/*.xml${NC}"
    echo -e "  - Waveform:        ${YELLOW}waveforms/multi_module_tb_wave.ghw${NC}"
    echo ""
    echo -e "View waveform with: ${YELLOW}gtkwave waveforms/multi_module_tb_wave.ghw${NC}"
else
    echo -e "${BLUE}----------------------------------------${NC}"
    echo ""
    echo -e "${RED}✗ VHDL simulation failed${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Test results summary displayed above.${NC}"
