#!/usr/bin/env python3
"""
Test runner with detailed results and markdown report generation for Axion-HDL

This runner executes all tests and generates a detailed TEST_RESULTS.md file
with individual test results for each sub-test.

Covers requirements:
- AXION-001 to AXION-029
- AXI-LITE-001 to AXI-LITE-018
- PARSER-001 to PARSER-008
- GEN-001 to GEN-016
- CDC-001 to CDC-007
- ADDR-001 to ADDR-008
- ERR-001 to ERR-006
- CLI-001 to CLI-010
- STRESS-001 to STRESS-006
"""

import subprocess
import sys
import os
import time
import json
import re
import unittest
import tempfile
import shutil
import atexit
from datetime import datetime
from typing import List, Dict, Any, Tuple
from pathlib import Path

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / ".test_results"
RESULTS_FILE = RESULTS_DIR / "results.json"
MARKDOWN_FILE = PROJECT_ROOT / "TEST_RESULTS.md"
REQUIREMENTS_FILE = PROJECT_ROOT / "instructions" / "requirements.md"

# Create a global temporary directory for generated files
# This ensures that tests do not pollute the source tree (e.g. tests/vhdl or output/)
GEN_OUTPUT_DIR = Path(tempfile.mkdtemp(prefix="axion_test_gen_"))

def cleanup_gen_files():
    """Cleanup generated files directory"""
    if GEN_OUTPUT_DIR.exists():
        shutil.rmtree(GEN_OUTPUT_DIR, ignore_errors=True)

atexit.register(cleanup_gen_files)

print(f"Test generation directory: {GEN_OUTPUT_DIR}")

# Add project root to python path to import axion_hdl
sys.path.insert(0, str(PROJECT_ROOT))
try:
    from axion_hdl.axion import AxionHDL
except ImportError:
    print(f"{YELLOW}Warning: Could not import axion_hdl. Some tests may fail.{RESET}")


class TestResult:
    def __init__(self, test_id: str, name: str, status: str, duration: float, 
                 output: str = "", category: str = "", subcategory: str = ""):
        self.id = test_id
        self.name = name
        self.status = status  # passed, failed, skipped, timeout, error
        self.duration = duration
        self.output = output
        self.category = category
        self.subcategory = subcategory
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "duration": self.duration,
            "output": self.output[-2000:] if len(self.output) > 2000 else self.output,
            "category": self.category,
            "subcategory": self.subcategory,
            "timestamp": self.timestamp
        }


def run_command(command: List[str], cwd: str = None, timeout: int = 300) -> Tuple[bool, float, str]:
    """Run a command and return (success, duration, output)"""
    start = time.time()
    try:
        result = subprocess.run(
            command,
            cwd=cwd or str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout
        )
        duration = time.time() - start
        output = result.stdout + result.stderr
        return result.returncode == 0, duration, output
    except subprocess.TimeoutExpired:
        return False, timeout, "TIMEOUT"
    except Exception as e:
        return False, time.time() - start, str(e)


def run_python_unit_tests() -> List[TestResult]:
    """Run Python unit tests and parse individual results"""
    results = []
    
    # Test 1: Initialize Axion
    test_id = "python.unit.init"
    name = "Initialize AxionHDL"
    start = time.time()
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from axion_hdl import AxionHDL
        axion = AxionHDL()
        results.append(TestResult(test_id, name, "passed", time.time() - start, 
                                  category="python", subcategory="unit"))
    except Exception as e:
        results.append(TestResult(test_id, name, "failed", time.time() - start, 
                                  str(e), category="python", subcategory="unit"))
        return results  # Can't continue without import
    
    # Test 2: Add source directory
    test_id = "python.unit.add_src"
    name = "Add Source Directory"
    start = time.time()
    try:
        axion = AxionHDL(output_dir=str(PROJECT_ROOT / "output"))
        axion.add_src(str(PROJECT_ROOT / "tests" / "vhdl"))
        axion.exclude("error_cases")
        results.append(TestResult(test_id, name, "passed", time.time() - start,
                                  category="python", subcategory="unit"))
    except Exception as e:
        results.append(TestResult(test_id, name, "failed", time.time() - start, 
                                  str(e), category="python", subcategory="unit"))
    
    # Test 3: Analyze VHDL files
    test_id = "python.unit.analyze"
    name = "Analyze VHDL Files"
    start = time.time()
    try:
        axion = AxionHDL(output_dir=str(GEN_OUTPUT_DIR))
        axion.add_src(str(PROJECT_ROOT / "tests" / "vhdl"))
        axion.exclude("error_cases")
        success = axion.analyze()
        if success:
            results.append(TestResult(test_id, name, "passed", time.time() - start,
                                      category="python", subcategory="unit"))
        else:
            results.append(TestResult(test_id, name, "failed", time.time() - start,
                                      "Analysis returned False", category="python", subcategory="unit"))
    except Exception as e:
        results.append(TestResult(test_id, name, "failed", time.time() - start, 
                                  str(e), category="python", subcategory="unit"))
    
    # Test 4: Generate VHDL
    test_id = "python.unit.gen_vhdl"
    name = "Generate VHDL Modules"
    start = time.time()
    try:
        axion = AxionHDL(output_dir=str(GEN_OUTPUT_DIR))
        axion.add_src(str(PROJECT_ROOT / "tests" / "vhdl"))
        axion.exclude("error_cases")
        axion.analyze()
        axion.generate_vhdl()
        # Check output files exist
        vhdl_files = list(GEN_OUTPUT_DIR.glob("*_axion_reg.vhd"))
        if len(vhdl_files) >= 2:
            results.append(TestResult(test_id, name, "passed", time.time() - start,
                                      f"Generated {len(vhdl_files)} VHDL files",
                                      category="python", subcategory="unit"))
        else:
            results.append(TestResult(test_id, name, "failed", time.time() - start,
                                      f"Expected >= 2 VHDL files, got {len(vhdl_files)}",
                                      category="python", subcategory="unit"))
    except Exception as e:
        results.append(TestResult(test_id, name, "failed", time.time() - start, 
                                  str(e), category="python", subcategory="unit"))
    
    # Test 5: Generate C Headers
    test_id = "python.unit.gen_c"
    name = "Generate C Headers"
    start = time.time()
    try:
        axion = AxionHDL(output_dir=str(GEN_OUTPUT_DIR))
        axion.add_src(str(PROJECT_ROOT / "tests" / "vhdl"))
        axion.exclude("error_cases")
        axion.analyze()
        axion.generate_c_header()
        c_files = list(GEN_OUTPUT_DIR.glob("*_regs.h"))
        if len(c_files) >= 2:
            results.append(TestResult(test_id, name, "passed", time.time() - start,
                                      f"Generated {len(c_files)} C header files",
                                      category="python", subcategory="unit"))
        else:
            results.append(TestResult(test_id, name, "failed", time.time() - start,
                                      f"Expected >= 2 C headers, got {len(c_files)}",
                                      category="python", subcategory="unit"))
    except Exception as e:
        results.append(TestResult(test_id, name, "failed", time.time() - start, 
                                  str(e), category="python", subcategory="unit"))
    
    # Test 6: Generate XML
    test_id = "python.unit.gen_xml"
    name = "Generate XML Register Map"
    start = time.time()
    try:
        axion = AxionHDL(output_dir=str(GEN_OUTPUT_DIR))
        axion.add_src(str(PROJECT_ROOT / "tests" / "vhdl"))
        axion.exclude("error_cases")
        axion.analyze()
        axion.generate_xml()
        xml_files = list(GEN_OUTPUT_DIR.glob("*_regs.xml"))
        if len(xml_files) >= 2:
            results.append(TestResult(test_id, name, "passed", time.time() - start,
                                      f"Generated {len(xml_files)} XML files",
                                      category="python", subcategory="unit"))
        else:
            results.append(TestResult(test_id, name, "failed", time.time() - start,
                                      f"Expected >= 2 XML files, got {len(xml_files)}",
                                      category="python", subcategory="unit"))
    except Exception as e:
        results.append(TestResult(test_id, name, "failed", time.time() - start, 
                                  str(e), category="python", subcategory="unit"))
    
    # Test 7: Generate Documentation
    test_id = "python.unit.gen_doc"
    name = "Generate Markdown Documentation"
    start = time.time()
    try:
        axion = AxionHDL(output_dir=str(GEN_OUTPUT_DIR))
        axion.add_src(str(PROJECT_ROOT / "tests" / "vhdl"))
        axion.exclude("error_cases")
        axion.analyze()
        axion.generate_documentation(format="md")
        doc_file = GEN_OUTPUT_DIR / "register_map.md"
        if doc_file.exists():
            results.append(TestResult(test_id, name, "passed", time.time() - start,
                                      "Generated register_map.md",
                                      category="python", subcategory="unit"))
        else:
            results.append(TestResult(test_id, name, "failed", time.time() - start,
                                      "register_map.md not found",
                                      category="python", subcategory="unit"))
    except Exception as e:
        results.append(TestResult(test_id, name, "failed", time.time() - start, 
                                  str(e), category="python", subcategory="unit"))
    
    return results


def run_address_conflict_tests() -> List[TestResult]:
    """Run address conflict detection tests"""
    results = []
    
    sys.path.insert(0, str(PROJECT_ROOT))
    from axion_hdl import AxionHDL, AddressConflictError
    import tempfile
    import shutil
    
    # Test 1: Basic address conflict detection
    test_id = "python.conflict.basic"
    name = "Basic Address Conflict Detection"
    start = time.time()
    try:
        test_vhdl_dir = PROJECT_ROOT / "tests" / "vhdl" / "error_cases"
        conflict_file = test_vhdl_dir / "address_conflict_test.vhd"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_vhdl = Path(temp_dir) / "address_conflict_test.vhd"
            shutil.copy(conflict_file, temp_vhdl)
            
            axion = AxionHDL()
            axion.add_src(temp_dir)
            axion.set_output_dir(Path(temp_dir) / "output")
            axion.analyze()
            
            # Check if parsing_errors contains address conflict
            found_conflict = False
            for module in axion.analyzed_modules:
                errors = module.get('parsing_errors', [])
                for err in errors:
                    if 'Address Conflict' in err.get('msg', ''):
                        found_conflict = True
                        break
            
            if found_conflict:
                results.append(TestResult(test_id, name, "passed", time.time() - start,
                                          "Address conflict correctly detected in parsing_errors",
                                          category="python", subcategory="conflict"))
            else:
                results.append(TestResult(test_id, name, "failed", time.time() - start,
                                          "No address conflict detected in parsing_errors",
                                          category="python", subcategory="conflict"))
    except Exception as e:
        results.append(TestResult(test_id, name, "failed", time.time() - start,
                                  str(e), category="python", subcategory="conflict"))
    
    # Test 2: No false positives
    test_id = "python.conflict.no_false_positive"
    name = "No False Positive (Unique Addresses)"
    start = time.time()
    try:
        valid_vhdl = '''
library ieee;
use ieee.std_logic_1164.all;

-- @axion_def BASE_ADDR=0x0000

entity valid_module is
    port (clk : in std_logic);
end entity;

architecture rtl of valid_module is
    signal reg_a : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
    signal reg_b : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x04
    signal reg_c : std_logic_vector(31 downto 0); -- @axion WO ADDR=0x08
begin
end architecture;
'''
        with tempfile.TemporaryDirectory() as temp_dir:
            vhdl_file = Path(temp_dir) / "valid_module.vhd"
            vhdl_file.write_text(valid_vhdl)
            
            axion = AxionHDL()
            axion.add_src(temp_dir)
            axion.set_output_dir(Path(temp_dir) / "output")
            
            try:
                axion.analyze()
                results.append(TestResult(test_id, name, "passed", time.time() - start,
                                          "No error with unique addresses",
                                          category="python", subcategory="conflict"))
            except AddressConflictError as e:
                results.append(TestResult(test_id, name, "failed", time.time() - start,
                                          f"False positive: {e}",
                                          category="python", subcategory="conflict"))
    except Exception as e:
        results.append(TestResult(test_id, name, "failed", time.time() - start,
                                  str(e), category="python", subcategory="conflict"))
    
    # Test 3: Wide signal overlap detection
    test_id = "python.conflict.wide_signal"
    name = "Wide Signal Address Overlap"
    start = time.time()
    try:
        overlap_vhdl = '''
library ieee;
use ieee.std_logic_1164.all;

-- @axion_def BASE_ADDR=0x0000

entity wide_overlap_test is
    port (clk : in std_logic);
end entity;

architecture rtl of wide_overlap_test is
    signal wide_reg : std_logic_vector(63 downto 0); -- @axion RO ADDR=0x00
    signal conflict_reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x04
begin
end architecture;
'''
        with tempfile.TemporaryDirectory() as temp_dir:
            vhdl_file = Path(temp_dir) / "wide_overlap_test.vhd"
            vhdl_file.write_text(overlap_vhdl)
            
            axion = AxionHDL()
            axion.add_src(temp_dir)
            axion.set_output_dir(Path(temp_dir) / "output")
            axion.analyze()
            
            # Check for overlap error in parsing_errors
            found_overlap = False
            for module in axion.analyzed_modules:
                errors = module.get('parsing_errors', [])
                for err in errors:
                    if 'Address Conflict' in err.get('msg', '') or 'overlap' in err.get('msg', '').lower():
                        found_overlap = True
                        break
            
            if found_overlap:
                results.append(TestResult(test_id, name, "passed", time.time() - start,
                                          "Wide signal overlap correctly detected",
                                          category="python", subcategory="conflict"))
            else:
                results.append(TestResult(test_id, name, "failed", time.time() - start,
                                          "Wide signal overlap not detected",
                                          category="python", subcategory="conflict"))
    except Exception as e:
        results.append(TestResult(test_id, name, "failed", time.time() - start,
                                  str(e), category="python", subcategory="conflict"))
    
    return results


def run_c_tests() -> List[TestResult]:
    """Run C header compilation tests"""
    results = []
    
    # Check if GCC is available
    success, _, _ = run_command(["which", "gcc"])
    if not success:
        results.append(TestResult("c.compile.gcc_check", "GCC Available", "skipped", 0,
                                  "gcc not found", category="c", subcategory="compile"))
        return results
    
    # Test 1: GCC available
    test_id = "c.compile.gcc_check"
    name = "GCC Available"
    start = time.time()
    success, duration, output = run_command(["gcc", "--version"])
    if success:
        version = output.split('\n')[0] if output else "unknown"
        results.append(TestResult(test_id, name, "passed", duration, version,
                                  category="c", subcategory="compile"))
    else:
        results.append(TestResult(test_id, name, "skipped", duration, output,
                                  category="c", subcategory="compile"))
        return results
    
    # Test 2: Compile test_c_headers.c
    test_id = "c.compile.headers"
    name = "Compile C Header Test"
    start = time.time()
    test_file = PROJECT_ROOT / "tests" / "c" / "test_c_headers.c"
    output_binary = PROJECT_ROOT / "tests" / "c" / "test_c_headers"
    
    success, duration, output = run_command([
        "gcc", "-Wall", "-Wextra", "-Werror", "-pedantic", "-std=c11",
        "-I", str(GEN_OUTPUT_DIR),
        "-o", str(output_binary), str(test_file)
    ])
    
    if success:
        results.append(TestResult(test_id, name, "passed", duration,
                                  "Compilation successful", category="c", subcategory="compile"))
    else:
        results.append(TestResult(test_id, name, "failed", duration, output,
                                  category="c", subcategory="compile"))
        return results
    
    # Test 3: Run compiled binary
    test_id = "c.compile.run"
    name = "Run C Header Test Binary"
    success, duration, output = run_command([str(output_binary)])
    
    if success:
        results.append(TestResult(test_id, name, "passed", duration, output,
                                  category="c", subcategory="compile"))
    else:
        results.append(TestResult(test_id, name, "failed", duration, output,
                                  category="c", subcategory="compile"))
    
    # Cleanup
    if output_binary.exists():
        output_binary.unlink()
    
    return results


def run_vhdl_tests() -> List[TestResult]:
    """Run VHDL simulation tests with GHDL"""
    results = []
    
    # Check if GHDL is available
    success, _, _ = run_command(["which", "ghdl"])
    if not success:
        results.append(TestResult("vhdl.ghdl.check", "GHDL Available", "skipped", 0,
                                  "ghdl not found", category="vhdl", subcategory="simulation"))
        return results
    
    # Test 1: GHDL available
    test_id = "vhdl.ghdl.check"
    name = "GHDL Available"
    start = time.time()
    success, duration, output = run_command(["ghdl", "--version"])
    if success:
        version = output.split('\n')[0] if output else "unknown"
        results.append(TestResult(test_id, name, "passed", duration, version,
                                  category="vhdl", subcategory="simulation"))
    else:
        results.append(TestResult(test_id, name, "skipped", duration, output,
                                  category="vhdl", subcategory="simulation"))
        return results
    
    work_dir = PROJECT_ROOT / "work"
    # Clean work directory to force reanalysis of all VHDL files
    # This prevents "file has changed and must be reanalysed" errors
    if work_dir.exists():
        import shutil
        shutil.rmtree(work_dir)
    work_dir.mkdir(exist_ok=True)
    
    ghdl_opts = ["--std=08", f"--workdir={work_dir}"]
    
    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    # Generate needed VHDL files for analysis tests
    # -------------------------------------------------------------------------
    # Use global temp directory for generated files
    gen_output_dir = GEN_OUTPUT_DIR
    
    try:
        start_gen = time.time()
        axion = AxionHDL(output_dir=str(gen_output_dir))
        axion.add_src(str(PROJECT_ROOT / "tests" / "vhdl"))
        axion.exclude("address_conflict_test.vhd", "test_parser_*.vhd", "error_cases", "*_tb.vhd")
        
        # We need to analyze and generate for standard controllers
        axion.analyze()
        axion.generate_vhdl()
        
        # Verify generation
        expected_files = [
            "sensor_controller_axion_reg.vhd",
            "spi_controller_axion_reg.vhd",
            "mixed_width_controller_axion_reg.vhd"
        ]
        
        missing = [f for f in expected_files if not (gen_output_dir / f).exists()]
        if missing:
            print(f"Warning: Failed to generate {missing}")
            
    except Exception as e:
        print(f"Error during VHDL generation setup: {e}")
        
    # -------------------------------------------------------------------------
    
    # Test 2: Analyze sensor_controller.vhd
    test_id = "vhdl.analyze.sensor_controller"
    name = "Analyze sensor_controller.vhd"
    vhdl_file = PROJECT_ROOT / "tests" / "vhdl" / "sensor_controller.vhd"
    success, duration, output = run_command(["ghdl", "-a"] + ghdl_opts + [str(vhdl_file)])
    status = "passed" if success else "failed"
    results.append(TestResult(test_id, name, status, duration, output,
                              category="vhdl", subcategory="analyze"))
                              
    # Test 11: Analyze generated sensor_controller_axion_reg.vhd
    test_id = "vhdl.analyze.sensor_axion"
    name = "Analyze sensor_controller_axion_reg.vhd"
    # Look for generated file in temp directory
    vhdl_file = gen_output_dir / "sensor_controller_axion_reg.vhd"
    if vhdl_file.exists():
        success, duration, output = run_command(["ghdl", "-a"] + ghdl_opts + [str(vhdl_file)])
        status = "passed" if success else "failed"
    else:
        success, duration, output = False, 0, "Skipped because file not found in temp dir"
        status = "failed"
    results.append(TestResult(test_id, name, status, duration, output,
                              category="vhdl", subcategory="analyze"))
                              
    # Test 3: Analyze spi_controller.vhd
    test_id = "vhdl.analyze.spi_controller"
    name = "Analyze spi_controller.vhd"
    vhdl_file = PROJECT_ROOT / "tests" / "vhdl" / "spi_controller.vhd"
    success, duration, output = run_command(["ghdl", "-a"] + ghdl_opts + [str(vhdl_file)])
    status = "passed" if success else "failed"
    results.append(TestResult(test_id, name, status, duration, output,
                              category="vhdl", subcategory="analyze"))
                              
    # Test 12: Analyze generated spi_controller_axion_reg.vhd
    test_id = "vhdl.analyze.spi_axion"
    name = "Analyze spi_controller_axion_reg.vhd"
    vhdl_file = gen_output_dir / "spi_controller_axion_reg.vhd"
    if vhdl_file.exists():
        success, duration, output = run_command(["ghdl", "-a"] + ghdl_opts + [str(vhdl_file)])
        status = "passed" if success else "failed"
    else:
        success, duration, output = False, 0, "Skipped because file not found"
        status = "failed"
    results.append(TestResult(test_id, name, status, duration, output,
                              category="vhdl", subcategory="analyze"))
    
    # Test 4: Analyze mixed_width_controller.vhd
    test_id = "vhdl.analyze.mixed_width"
    name = "Analyze mixed_width_controller.vhd"
    vhdl_file = PROJECT_ROOT / "tests" / "vhdl" / "mixed_width_controller.vhd"
    success, duration, output = run_command(["ghdl", "-a"] + ghdl_opts + [str(vhdl_file)])
    status = "passed" if success else "failed"
    results.append(TestResult(test_id, name, status, duration, output,
                              category="vhdl", subcategory="analyze"))
                              
    # Test 13: Analyze generated mixed_width_controller_axion_reg.vhd
    test_id = "vhdl.analyze.mixed_axion"
    name = "Analyze mixed_width_controller_axion_reg.vhd"
    vhdl_file = gen_output_dir / "mixed_width_controller_axion_reg.vhd"
    if vhdl_file.exists():
        success, duration, output = run_command(["ghdl", "-a"] + ghdl_opts + [str(vhdl_file)])
        status = "passed" if success else "failed"
    else:
        success, duration, output = False, 0, "Skipped because file not found"
        status = "failed"
    results.append(TestResult(test_id, name, status, duration, output,
                              category="vhdl", subcategory="analyze"))
        
    # Test 5: Generate VHDL for subregister_test.vhd
    test_id = "vhdl.generate.subregister"
    name = "SUB-VHDL: Generate subregister_test_axion_reg.vhd"
    start = time.time()
    try:
        # Generate VHDL dynamically
        # Use global temp dir
        axion = AxionHDL(output_dir=str(GEN_OUTPUT_DIR))
        axion.add_src(str(PROJECT_ROOT / "tests" / "vhdl"))
        axion.exclude("address_conflict_test.vhd", "test_parser_*.vhd", "error_cases")
        # Only analyze subregister_test.vhd for this test to be fast
        axion.analyze() 
        # But specifically we want to make sure subregister_test_axion_reg.vhd is generated
        # axion.analyze() parses all files in the dir
        
        # Manually filter to only generate the one we want if needed, or just generate all
        # To be safe and compliant with Axion flow, we'll just generate everything in that dir
        axion.generate_vhdl()
        
        gen_file = GEN_OUTPUT_DIR / "subregister_test_axion_reg.vhd"
        if gen_file.exists():
            duration = time.time() - start
            results.append(TestResult(test_id, name, "passed", duration, f"Generated {gen_file}",
                                      category="vhdl", subcategory="generate"))
            success_gen = True
        else:
            duration = time.time() - start
            results.append(TestResult(test_id, name, "failed", duration, "File not generated",
                                      category="vhdl", subcategory="generate"))
            success_gen = False
    except Exception as e:
        duration = time.time() - start
        results.append(TestResult(test_id, name, "failed", duration, str(e),
                                  category="vhdl", subcategory="generate"))
        success_gen = False

    # Test 6: Analyze subregister_test.vhd (SUB/DEF features)
    test_id = "vhdl.analyze.subregister_test"
    name = "SUB-VHDL: Analyze subregister_test.vhd"
    vhdl_file = PROJECT_ROOT / "tests" / "vhdl" / "subregister_test.vhd"
    success, duration, output = run_command(["ghdl", "-a"] + ghdl_opts + [str(vhdl_file)])
    status = "passed" if success else "failed"
    results.append(TestResult(test_id, name, status, duration, output,
                              category="vhdl", subcategory="analyze"))
    
    # Test 7: Analyze generated subregister_test_axion_reg.vhd
    test_id = "vhdl.analyze.subregister_axion"
    name = "SUB-VHDL: Analyze generated subregister_test_axion_reg.vhd"
    vhdl_file = GEN_OUTPUT_DIR / "subregister_test_axion_reg.vhd"
    if success_gen and vhdl_file.exists():
        success, duration, output = run_command(["ghdl", "-a"] + ghdl_opts + [str(vhdl_file)])
        status = "passed" if success else "failed"
    else:
        success, duration, output = False, 0, "Skipped because generation failed"
        status = "failed"
    results.append(TestResult(test_id, name, status, duration, output,
                              category="vhdl", subcategory="analyze"))

    # Test 8: Analyze subregister_test_tb.vhd
    test_id = "vhdl.analyze.subregister_tb"
    name = "SUB-VHDL: Analyze subregister_test_tb.vhd"
    vhdl_file = PROJECT_ROOT / "tests" / "vhdl" / "subregister_test_tb.vhd"
    success, duration, output = run_command(["ghdl", "-a"] + ghdl_opts + [str(vhdl_file)])
    status = "passed" if success else "failed"
    results.append(TestResult(test_id, name, status, duration, output,
                              category="vhdl", subcategory="analyze"))

    # Test 9: Elaborate subregister_test_tb
    test_id = "vhdl.elaboration.subregister_tb"
    name = "SUB-VHDL: Elaborate subregister_test_tb"
    success, duration, output = run_command(["ghdl", "-e"] + ghdl_opts + ["subregister_test_tb"])
    status = "passed" if success else "failed"
    results.append(TestResult(test_id, name, status, duration, output,
                              category="vhdl", subcategory="elaboration"))

    # Test 10: Run subregister_test_tb
    test_id = "vhdl.run.subregister_tb"
    name = "SUB-VHDL: Run subregister_test_tb Simulation"
    success, duration, output = run_command(["ghdl", "-r"] + ghdl_opts + ["subregister_test_tb", "--assert-level=error"])
    
    # Parse output for PASS/FAIL counts
    if success:
        if "FAIL" in output or "error" in output.lower():
            status = "failed"
            # Extract failure message if possible
            fail_line = next((line for line in output.split('\n') if "FAIL" in line), "Unknown failure")
            output = f"Simulation failed: {fail_line}\n{output}"
        else:
            status = "passed"
    else:
        status = "failed"
        
    results.append(TestResult(test_id, name, status, duration, output,
                              category="vhdl", subcategory="simulation"))
    
    # Test 11: Analyze generated sensor_controller_axion_reg.vhd
    test_id = "vhdl.analyze.sensor_axion"
    name = "Analyze sensor_controller_axion_reg.vhd"
    vhdl_file = GEN_OUTPUT_DIR / "sensor_controller_axion_reg.vhd"
    if vhdl_file.exists():
        success, duration, output = run_command(["ghdl", "-a"] + ghdl_opts + [str(vhdl_file)])
        status = "passed" if success else "failed"
    else:
        success, duration, output = False, 0, "File not found"
        status = "failed"
    results.append(TestResult(test_id, name, status, duration, output,
                              category="vhdl", subcategory="analyze"))
    
    # Test 12: Analyze generated spi_controller_axion_reg.vhd
    test_id = "vhdl.analyze.spi_axion"
    name = "Analyze spi_controller_axion_reg.vhd"
    vhdl_file = GEN_OUTPUT_DIR / "spi_controller_axion_reg.vhd"
    if vhdl_file.exists():
        success, duration, output = run_command(["ghdl", "-a"] + ghdl_opts + [str(vhdl_file)])
        status = "passed" if success else "failed"
    else:
        success, duration, output = False, 0, "File not found"
        status = "failed"
    results.append(TestResult(test_id, name, status, duration, output,
                              category="vhdl", subcategory="analyze"))
    
    # Test 13: Analyze generated mixed_width_controller_axion_reg.vhd
    test_id = "vhdl.analyze.mixed_axion"
    name = "Analyze mixed_width_controller_axion_reg.vhd"
    vhdl_file = GEN_OUTPUT_DIR / "mixed_width_controller_axion_reg.vhd"
    if vhdl_file.exists():
        success, duration, output = run_command(["ghdl", "-a"] + ghdl_opts + [str(vhdl_file)])
        status = "passed" if success else "failed"
    else:
        success, duration, output = False, 0, "File not found"
        status = "failed"
    results.append(TestResult(test_id, name, status, duration, output,
                              category="vhdl", subcategory="analyze"))
    
    # Test 8: Analyze testbench
    test_id = "vhdl.analyze.testbench"
    name = "Analyze multi_module_tb.vhd"
    vhdl_file = PROJECT_ROOT / "tests" / "vhdl" / "multi_module_tb.vhd"
    success, duration, output = run_command(["ghdl", "-a"] + ghdl_opts + [str(vhdl_file)])
    status = "passed" if success else "failed"
    results.append(TestResult(test_id, name, status, duration, output,
                              category="vhdl", subcategory="analyze"))
    
    # Test 9: Elaborate testbench
    test_id = "vhdl.elaborate.testbench"
    name = "Elaborate multi_module_tb"
    # Ensure clean elaboration
    if (PROJECT_ROOT / "multi_module_tb").exists():
        (PROJECT_ROOT / "multi_module_tb").unlink()
    
    # Reanalyze all generated files to prevent "file has changed" errors
    # This is needed because axion.generate_vhdl() may regenerate files mid-test
    for gen_file in ["sensor_controller_axion_reg.vhd", "spi_controller_axion_reg.vhd", "mixed_width_controller_axion_reg.vhd"]:
        gen_path = GEN_OUTPUT_DIR / gen_file
        if gen_path.exists():
            run_command(["ghdl", "-a"] + ghdl_opts + [str(gen_path)])
    # Also reanalyze the testbench
    run_command(["ghdl", "-a"] + ghdl_opts + [str(PROJECT_ROOT / "tests" / "vhdl" / "multi_module_tb.vhd")])
    
    success, duration, output = run_command(["ghdl", "-e"] + ghdl_opts + ["multi_module_tb"])
    status = "passed" if success else "failed"
    results.append(TestResult(test_id, name, status, duration, output,
                              category="vhdl", subcategory="elaborate"))

    # ==========================================
    # XML VHDL Verification Steps
    # ==========================================

    # Test XML-1: Generate VHDL from XML
    test_id = "vhdl.xml.generate"
    name = "XML: Generate VHDL from tests/xml/subregister_test.xml"
    start = time.time()
    try:
        # Generate into temp dir
        axion = AxionHDL(output_dir=str(GEN_OUTPUT_DIR))
        axion.add_xml_src(str(PROJECT_ROOT / "tests" / "xml"))
        axion.analyze()
        axion.analyze()
        axion.generate_vhdl()
        axion.generate_c_header()
        
        gen_file = GEN_OUTPUT_DIR / "subregister_test_xml_axion_reg.vhd"
        if gen_file.exists():
            duration = time.time() - start
            results.append(TestResult(test_id, name, "passed", duration, f"Generated {gen_file}",
                                      category="vhdl", subcategory="xml"))
            success_xml_gen = True
        else:
            duration = time.time() - start
            results.append(TestResult(test_id, name, "failed", duration, "File not generated",
                                      category="vhdl", subcategory="xml"))
            success_xml_gen = False
    except Exception as e:
        duration = time.time() - start
        results.append(TestResult(test_id, name, "failed", duration, str(e),
                                  category="vhdl", subcategory="xml"))
        success_xml_gen = False

    # Test XML-2: Analyze Generated VHDL
    test_id = "vhdl.xml.analyze_gen"
    name = "XML: Analyze generated subregister_test_xml_axion_reg.vhd"
    vhdl_file = GEN_OUTPUT_DIR / "subregister_test_xml_axion_reg.vhd"
    if success_xml_gen and vhdl_file.exists():
        success, duration, output = run_command(["ghdl", "-a"] + ghdl_opts + [str(vhdl_file)])
        status = "passed" if success else "failed"
    else:
        success, duration, output = False, 0, "Skipped because generation failed"
        status = "failed"
    results.append(TestResult(test_id, name, status, duration, output,
                              category="vhdl", subcategory="xml"))

    # Test XML-3: Analyze XML Testbench
    test_id = "vhdl.xml.analyze_tb"
    name = "XML: Analyze subregister_xml_test_tb.vhd"
    vhdl_file = PROJECT_ROOT / "tests" / "vhdl" / "subregister_xml_test_tb.vhd"
    success, duration, output = run_command(["ghdl", "-a"] + ghdl_opts + [str(vhdl_file)])
    status = "passed" if success else "failed"
    results.append(TestResult(test_id, name, status, duration, output,
                              category="vhdl", subcategory="xml"))

    # Test XML-4: Elaborate XML Testbench
    test_id = "vhdl.xml.elaborate"
    name = "XML: Elaborate subregister_xml_test_tb"
    success, duration, output = run_command(["ghdl", "-e"] + ghdl_opts + ["subregister_xml_test_tb"])
    status = "passed" if success else "failed"
    results.append(TestResult(test_id, name, status, duration, output,
                              category="vhdl", subcategory="xml"))

    # Test XML-5: Run XML Testbench
    test_id = "vhdl.xml.run"
    name = "XML: Run subregister_xml_test_tb"
    success, duration, output = run_command(["ghdl", "-r"] + ghdl_opts + ["subregister_xml_test_tb"])
    
    if success:
        if "FAIL" in output or "error" in output.lower():
            status = "failed"
            fail_line = next((line for line in output.split('\n') if "FAIL" in line), "Unknown failure")
            output = f"Simulation failed: {fail_line}\n{output}"
        else:
            status = "passed"
    else:
        status = "failed"
        
    results.append(TestResult(test_id, name, status, duration, output,
                              category="vhdl", subcategory="xml"))

    # Test 10: Run simulation and parse individual test results
    test_id = "vhdl.simulate.testbench"
    name = "Run multi_module_tb Simulation"
    waveform_dir = PROJECT_ROOT / "waveforms"
    waveform_dir.mkdir(exist_ok=True)
    wave_file = waveform_dir / "multi_module_tb_wave.ghw"
    
    # CRITICAL: Reanalyze and re-elaborate before simulation
    # The XML generation step above may have regenerated files, causing stale analysis
    for gen_file in ["sensor_controller_axion_reg.vhd", "spi_controller_axion_reg.vhd", "mixed_width_controller_axion_reg.vhd"]:
        gen_path = GEN_OUTPUT_DIR / gen_file
        if gen_path.exists():
            run_command(["ghdl", "-a"] + ghdl_opts + [str(gen_path)])
    run_command(["ghdl", "-a"] + ghdl_opts + [str(PROJECT_ROOT / "tests" / "vhdl" / "multi_module_tb.vhd")])
    run_command(["ghdl", "-e"] + ghdl_opts + ["multi_module_tb"])
    
    success, duration, output = run_command([
        "ghdl", "-r"] + ghdl_opts + [
        "multi_module_tb",
        f"--wave={wave_file}",
        "--stop-time=1ms"
    ])
    
    # Parse individual test results from GHDL output
    # Format: "AXION-001      | PASSED | Read-Only Register Read Access"
    test_pattern = re.compile(r'^(AXION-\d+[a-z]?|AXI-LITE-\d+[a-z]?)\s*\|\s*(PASSED|FAILED)\s*\|\s*(.+)$', re.MULTILINE)
    matches = test_pattern.findall(output)
    
    if matches:
        for req_id, status, desc in matches:
            test_id = f"vhdl.req.{req_id.lower().replace('-', '_')}"
            test_status = "passed" if status == "PASSED" else "failed"
            results.append(TestResult(test_id, f"{req_id}: {desc.strip()}", test_status, 0,
                                      f"Requirement {req_id}", category="vhdl", subcategory="requirements"))
    else:
        # Fallback: just record overall simulation result
        status = "passed" if success else "failed"
        # Include full output if failed for debugging
        if status == "failed":
            print(f"\n{'='*80}\nDEBUG: multi_module_tb FAILED - Full output:\n{'='*80}")
            print(output[:5000] if output else "No output captured")
            print(f"{'='*80}\n")
        msg = output if status == "failed" else f"Simulation passed but no requirements matched regex. Output len: {len(output)}"
        results.append(TestResult(test_id, name, status, duration, msg,
                                  category="vhdl", subcategory="simulate"))
    
    return results


def generate_markdown_report(results: List[TestResult]):
    """Generate detailed TEST_RESULTS.md"""
    
    passed = sum(1 for r in results if r.status == "passed")
    failed = sum(1 for r in results if r.status == "failed")
    skipped = sum(1 for r in results if r.status == "skipped")
    total = len(results)
    total_time = sum(r.duration for r in results)
    
    if failed > 0:
        overall = "❌ FAILING"
    elif passed == total:
        overall = "✅ ALL PASSING"
    elif skipped > 0 and failed == 0:
        overall = "⚠️ SOME SKIPPED"
    else:
        overall = "⚠️ PARTIAL"
    
    last_run = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    md = []
    md.append("# Axion-HDL Test Results")
    md.append("")
    md.append(f"**Overall Status:** {overall}")
    md.append("")
    md.append("## Summary")
    md.append("")
    md.append("| Metric | Value |")
    md.append("|--------|-------|")
    md.append(f"| **Total Tests** | {total} |")
    md.append(f"| ✅ Passed | {passed} |")
    md.append(f"| ❌ Failed | {failed} |")
    md.append(f"| ⏭️ Skipped | {skipped} |")
    md.append(f"| ⏱️ Total Time | {total_time:.2f}s |")
    md.append(f"| 🕐 Last Run | {last_run} |")
    md.append("")
    
    # Group by category
    categories = {}
    for r in results:
        cat = r.category or "other"
        if cat not in categories:
            categories[cat] = {}
        subcat = r.subcategory or "general"
        if subcat not in categories[cat]:
            categories[cat][subcat] = []
        categories[cat][subcat].append(r)
    
    # Category titles and emojis
    cat_info = {
        "python": ("🐍 Python Tests", {
            "unit": "Unit Tests",
            "conflict": "Address Conflict Tests"
        }),
        "c": ("⚙️ C Tests", {
            "compile": "Compilation Tests"
        }),
        "vhdl": ("🔧 VHDL Tests", {
            "simulation": "Simulation Setup",
            "analyze": "VHDL Analysis",
            "elaborate": "Elaboration",
            "simulate": "Simulation Run",
            "requirements": "Requirements Verification (AXION/AXI-LITE)"
        }),
        "parser": ("📜 Parser Tests (PARSER-xxx)", {
            "requirements": "PARSER Requirements",
            "setup": "Setup"
        }),
        "gen": ("🏭 Code Generation Tests (GEN-xxx)", {
            "requirements": "GEN Requirements",
            "setup": "Setup"
        }),
        "err": ("🚨 Error Handling Tests (ERR-xxx)", {
            "requirements": "ERR Requirements",
            "setup": "Setup"
        }),
        "cli": ("🖥️ CLI Tests (CLI-xxx)", {
            "requirements": "CLI Requirements",
            "setup": "Setup"
        }),
        "addr": ("📍 Address Management Tests (ADDR-xxx)", {
            "requirements": "ADDR Requirements"
        }),
        "cdc": ("🔄 CDC Tests (CDC-xxx)", {
            "requirements": "CDC Requirements"
        }),
        "stress": ("🔥 Stress Tests (STRESS-xxx)", {
            "requirements": "STRESS Requirements"
        })
    }
    
    for cat in ["python", "c", "vhdl", "parser", "gen", "err", "cli", "cdc", "addr", "stress"]:
        if cat not in categories:
            continue
        
        cat_title, subcat_titles = cat_info.get(cat, (cat.title(), {}))
        
        md.append(f"## {cat_title}")
        md.append("")
        
        for subcat, tests in categories[cat].items():
            subcat_title = subcat_titles.get(subcat, subcat.title())
            
            # Calculate subcategory stats
            sub_passed = sum(1 for t in tests if t.status == "passed")
            sub_total = len(tests)
            
            md.append(f"### {subcat_title}")
            md.append("")
            md.append(f"**{sub_passed}/{sub_total} passed**")
            md.append("")
            md.append("| Status | Test ID | Test Name | Duration |")
            md.append("|:------:|:--------|:----------|:--------:|")
            
            for t in tests:
                emoji = {"passed": "✅", "failed": "❌", "skipped": "⏭️"}.get(t.status, "❓")
                md.append(f"| {emoji} | `{t.id}` | {t.name} | {t.duration:.3f}s |")
            
            md.append("")
            
            # Add failure details
            failures = [t for t in tests if t.status == "failed"]
            if failures:
                md.append("<details>")
                md.append("<summary>❌ Failure Details</summary>")
                md.append("")
                for t in failures:
                    md.append(f"**{t.id}**: {t.name}")
                    md.append("```")
                    md.append(t.output[:500] if t.output else "No output")
                    md.append("```")
                    md.append("")
                md.append("</details>")
                md.append("")
    
    md.append("---")
    md.append(f"*Generated by `make test` at {last_run}*")
    
    MARKDOWN_FILE.write_text("\n".join(md))


def print_results(results: List[TestResult]):
    """Print results to terminal"""
    
    # Group by category
    categories = {}
    for r in results:
        cat = r.category or "other"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(r)
    
    cat_names = {
        "python": "🐍 PYTHON",
        "c": "⚙️  C",
        "vhdl": "🔧 VHDL",
        "parser": "📜 PARSER",
        "gen": "⚙️ GENERATION",
        "err": "🚨 ERRORS",
        "cli": "🖥️ CLI",
        "cdc": "🔄 CDC",
        "addr": "📍 ADDR",
        "stress": "🔥 STRESS",
        "sub": "📦 SUB",
        "def": "🔧 DEF",
        "yaml_input": "📄 YAML-INPUT",
        "json_input": "📄 JSON-INPUT",
        "equiv": "🔀 EQUIV"
    }
    
    total_passed = 0
    total_failed = 0
    total_skipped = 0
    total_time = 0.0
    
    print()
    print(f"{CYAN}{BOLD}{'═' * 80}{RESET}")
    print(f"{CYAN}{BOLD}  AXION-HDL TEST RESULTS{RESET}")
    print(f"{CYAN}{BOLD}{'═' * 80}{RESET}")
    
    for cat in ["python", "c", "vhdl", "parser", "gen", "err", "cli", "cdc", "addr", "stress", "sub", "def", "yaml_input", "json_input", "equiv"]:
        if cat not in categories:
            continue
        
        tests = categories[cat]
        cat_passed = sum(1 for t in tests if t.status == "passed")
        cat_failed = sum(1 for t in tests if t.status == "failed")
        cat_skipped = sum(1 for t in tests if t.status == "skipped")
        cat_time = sum(t.duration for t in tests)
        
        total_passed += cat_passed
        total_failed += cat_failed
        total_skipped += cat_skipped
        total_time += cat_time
        
        cat_name = cat_names.get(cat, cat.upper())
        print()
        print(f"{BOLD}{cat_name} ({cat_passed}/{len(tests)} passed, {cat_time:.2f}s){RESET}")
        print(f"{'─' * 80}")
        
        for t in tests:
            if t.status == "passed":
                status = f"{GREEN}✓ PASS{RESET}"
            elif t.status == "failed":
                status = f"{RED}✗ FAIL{RESET}"
            else:
                status = f"{YELLOW}○ SKIP{RESET}"
            
            print(f"  {status}  {t.name:<45} ({t.duration:.3f}s)")
    
    print()
    print(f"{'═' * 80}")
    print(f"{BOLD}TOTAL: {total_passed + total_failed + total_skipped} tests in {total_time:.2f}s{RESET}")
    
    parts = []
    if total_passed > 0:
        parts.append(f"{GREEN}{total_passed} passed{RESET}")
    if total_failed > 0:
        parts.append(f"{RED}{total_failed} failed{RESET}")
    if total_skipped > 0:
        parts.append(f"{YELLOW}{total_skipped} skipped{RESET}")
    
    print(f"       {', '.join(parts)}")
    print()
    print(f"Report: {BOLD}TEST_RESULTS.md{RESET}")
    print(f"{'═' * 80}")
    print()
    
    return total_failed == 0


def save_results(results: List[TestResult]):
    """Save results to JSON"""
    RESULTS_DIR.mkdir(exist_ok=True)
    data = {r.id: r.to_dict() for r in results}
    RESULTS_FILE.write_text(json.dumps(data, indent=2))


def run_parser_tests() -> List[TestResult]:
    """Run PARSER-xxx requirement tests"""
    results = []
    
    try:
        from tests.python.test_parser import TestParserRequirements
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestParserRequirements)
        
        for test in suite:
            test_name = str(test).split()[0]
            req_id = test_name.replace('test_parser_', 'PARSER-').replace('_', '-').upper()
            
            start = time.time()
            try:
                test.debug()
                results.append(TestResult(
                    f"parser.{test_name}",
                    f"{req_id}: {test.shortDescription() or test_name}",
                    "passed",
                    time.time() - start,
                    category="parser",
                    subcategory="requirements"
                ))
            except Exception as e:
                results.append(TestResult(
                    f"parser.{test_name}",
                    f"{req_id}: {test.shortDescription() or test_name}",
                    "failed",
                    time.time() - start,
                    str(e),
                    category="parser",
                    subcategory="requirements"
                ))
    except ImportError as e:
        results.append(TestResult(
            "parser.import",
            "PARSER: Import test module",
            "failed",
            0,
            str(e),
            category="parser",
            subcategory="setup"
        ))
    
    return results


def run_generator_tests() -> List[TestResult]:
    """Run GEN-xxx requirement tests"""
    results = []
    
    try:
        from tests.python.test_generator import TestGeneratorRequirements
        from tests.python.test_overwrite import TestGenerationOverwrite
        import io
        import sys
        
        # First run setUpClass manually if needed
        TestGeneratorRequirements.setUpClass()
        
        loader = unittest.TestLoader()
        suite_gen = loader.loadTestsFromTestCase(TestGeneratorRequirements)
        suite_over = loader.loadTestsFromTestCase(TestGenerationOverwrite)
        
        # Combine suites
        suite = unittest.TestSuite()
        suite.addTests(suite_gen)
        suite.addTests(suite_over)
        
        # Run each test
        for test in suite:
            test_name = str(test).split()[0]
            if "overwrite" in test_name:
                req_id = "AXION-027"
            else:
                req_id = test_name.replace('test_gen_', 'GEN-').replace('_', '-').upper()
            
            start = time.time()
            try:
                # Capture output
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()
                try:
                    test.debug()
                finally:
                    sys.stdout = old_stdout
                    
                results.append(TestResult(
                    f"gen.{test_name}",
                    f"{req_id}: {test.shortDescription() or test_name}",
                    "passed",
                    time.time() - start,
                    category="gen",
                    subcategory="requirements"
                ))
            except unittest.SkipTest as e:
                results.append(TestResult(
                    f"gen.{test_name}",
                    f"{req_id}: {test.shortDescription() or test_name}",
                    "skipped",
                    time.time() - start,
                    str(e),
                    category="gen",
                    subcategory="requirements"
                ))
            except Exception as e:
                results.append(TestResult(
                    f"gen.{test_name}",
                    f"{req_id}: {test.shortDescription() or test_name}",
                    "failed",
                    time.time() - start,
                    str(e),
                    category="gen",
                    subcategory="requirements"
                ))
    except ImportError as e:
        results.append(TestResult(
            "gen.import",
            "GEN: Import test module",
            "failed",
            0,
            str(e),
            category="gen",
            subcategory="setup"
        ))
    
    return results


def run_error_handling_tests() -> List[TestResult]:
    """Run ERR-xxx requirement tests"""
    results = []
    
    try:
        from tests.python.test_error_handling import TestErrorHandlingRequirements
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestErrorHandlingRequirements)
        
        for test in suite:
            test_name = str(test).split()[0]
            req_id = test_name.replace('test_err_', 'ERR-').replace('_', '-').upper()
            
            start = time.time()
            try:
                test.debug()
                results.append(TestResult(
                    f"err.{test_name}",
                    f"{req_id}: {test.shortDescription() or test_name}",
                    "passed",
                    time.time() - start,
                    category="err",
                    subcategory="requirements"
                ))
            except Exception as e:
                results.append(TestResult(
                    f"err.{test_name}",
                    f"{req_id}: {test.shortDescription() or test_name}",
                    "failed",
                    time.time() - start,
                    str(e),
                    category="err",
                    subcategory="requirements"
                ))
    except ImportError as e:
        results.append(TestResult(
            "err.import",
            "ERR: Import test module",
            "failed",
            0,
            str(e),
            category="err",
            subcategory="setup"
        ))
    
    return results


def run_cli_tests() -> List[TestResult]:
    """Run CLI-xxx requirement tests"""
    results = []
    
    try:
        from tests.python.test_cli import TestCLIRequirements
        import io
        import sys
        
        # First run setUpClass manually
        TestCLIRequirements.setUpClass()
        
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestCLIRequirements)
        
        for test in suite:
            test_name = str(test).split()[0]
            req_id = test_name.replace('test_cli_', 'CLI-').replace('_', '-').upper()
            
            start = time.time()
            try:
                # Capture output
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()
                try:
                    test.debug()
                finally:
                    sys.stdout = old_stdout
                    
                results.append(TestResult(
                    f"cli.{test_name}",
                    f"{req_id}: {test.shortDescription() or test_name}",
                    "passed",
                    time.time() - start,
                    category="cli",
                    subcategory="requirements"
                ))
            except unittest.SkipTest as e:
                results.append(TestResult(
                    f"cli.{test_name}",
                    f"{req_id}: {test.shortDescription() or test_name}",
                    "skipped",
                    time.time() - start,
                    str(e),
                    category="cli",
                    subcategory="requirements"
                ))
            except Exception as e:
                results.append(TestResult(
                    f"cli.{test_name}",
                    f"{req_id}: {test.shortDescription() or test_name}",
                    "failed",
                    time.time() - start,
                    str(e),
                    category="cli",
                    subcategory="requirements"
                ))
    except ImportError as e:
        results.append(TestResult(
            "cli.import",
            "CLI: Import test module",
            "failed",
            0,
            str(e),
            category="cli",
            subcategory="setup"
        ))
    
    return results


def run_cdc_tests() -> List[TestResult]:
    """Run CDC-xxx requirement tests"""
    results = []
    
    try:
        from tests.python.test_cdc import TestCDCRequirements
        import io
        import sys
        
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestCDCRequirements)
        
        for test in suite:
            test_name = str(test).split()[0]
            req_id = test_name.replace('test_cdc_', 'CDC-').replace('_', '-').upper()
            
            start = time.time()
            try:
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()
                try:
                    test.debug()
                finally:
                    sys.stdout = old_stdout
                    
                results.append(TestResult(
                    f"cdc.{test_name}",
                    f"{req_id}: {test.shortDescription() or test_name}",
                    "passed",
                    time.time() - start,
                    category="cdc",
                    subcategory="requirements"
                ))
            except Exception as e:
                results.append(TestResult(
                    f"cdc.{test_name}",
                    f"{req_id}: {test.shortDescription() or test_name}",
                    "failed",
                    time.time() - start,
                    str(e),
                    category="cdc",
                    subcategory="requirements"
                ))
    except ImportError as e:
        results.append(TestResult("cdc.import", "CDC: Import test module", "failed", 0, str(e), category="cdc", subcategory="setup"))
    
    return results


def run_addr_tests() -> List[TestResult]:
    """Run ADDR-xxx requirement tests"""
    results = []
    
    try:
        from tests.python.test_addr import TestAddressManagementRequirements
        import io
        import sys
        
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestAddressManagementRequirements)
        
        for test in suite:
            test_name = str(test).split()[0]
            req_id = test_name.replace('test_addr_', 'ADDR-').replace('_', '-').upper()
            
            start = time.time()
            try:
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()
                try:
                    test.debug()
                finally:
                    sys.stdout = old_stdout
                    
                results.append(TestResult(
                    f"addr.{test_name}",
                    f"{req_id}: {test.shortDescription() or test_name}",
                    "passed",
                    time.time() - start,
                    category="addr",
                    subcategory="requirements"
                ))
            except Exception as e:
                results.append(TestResult(
                    f"addr.{test_name}",
                    f"{req_id}: {test.shortDescription() or test_name}",
                    "failed",
                    time.time() - start,
                    str(e),
                    category="addr",
                    subcategory="requirements"
                ))
    except ImportError as e:
        results.append(TestResult("addr.import", "ADDR: Import test module", "failed", 0, str(e), category="addr", subcategory="setup"))
    
    return results


def run_stress_tests() -> List[TestResult]:
    """Run STRESS-xxx requirement tests"""
    results = []
    
    try:
        from tests.python.test_stress import TestStressRequirements
        import io
        import sys
        
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestStressRequirements)
        
        for test in suite:
            test_name = str(test).split()[0]
            req_id = test_name.replace('test_stress_', 'STRESS-').replace('_', '-').upper()
            
            start = time.time()
            try:
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()
                try:
                    test.debug()
                finally:
                    sys.stdout = old_stdout
                    
                results.append(TestResult(
                    f"stress.{test_name}",
                    f"{req_id}: {test.shortDescription() or test_name}",
                    "passed",
                    time.time() - start,
                    category="stress",
                    subcategory="requirements"
                ))
            except Exception as e:
                results.append(TestResult(
                    f"stress.{test_name}",
                    f"{req_id}: {test.shortDescription() or test_name}",
                    "failed",
                    time.time() - start,
                    str(e),
                    category="stress",
                    subcategory="requirements"
                ))
    except ImportError as e:
        results.append(TestResult("stress.import", "STRESS: Import test module", "failed", 0, str(e), category="stress", subcategory="setup"))
    
    return results


def run_subregister_tests() -> List[TestResult]:
    """Run SUB-xxx requirement tests for subregister support"""
    results = []
    
    try:
        from tests.python.test_subregister import TestSubregisterRequirements
        import io
        import sys
        
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestSubregisterRequirements)
        
        for test in suite:
            test_name = str(test).split()[0]
            req_id = test_name.replace('test_sub_', 'SUB-').replace('test_bit_', 'SUB-BIT-').replace('_', '-').upper()
            
            start = time.time()
            try:
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()
                try:
                    test.debug()
                finally:
                    sys.stdout = old_stdout
                    
                results.append(TestResult(
                    f"sub.{test_name}",
                    f"{req_id}: {test.shortDescription() or test_name}",
                    "passed",
                    time.time() - start,
                    category="sub",
                    subcategory="requirements"
                ))
            except Exception as e:
                results.append(TestResult(
                    f"sub.{test_name}",
                    f"{req_id}: {test.shortDescription() or test_name}",
                    "failed",
                    time.time() - start,
                    str(e),
                    category="sub",
                    subcategory="requirements"
                ))
    except ImportError as e:
        results.append(TestResult("sub.import", "SUB: Import test module", "failed", 0, str(e), category="sub", subcategory="setup"))
    
    return results


def run_default_tests() -> List[TestResult]:
    """Run DEF-xxx requirement tests for DEFAULT attribute support"""
    results = []
    
    try:
        from tests.python.test_default import TestDefaultRequirements
        import io
        import sys
        
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestDefaultRequirements)
        
        for test in suite:
            test_name = str(test).split()[0]
            req_id = test_name.replace('test_def_', 'DEF-').replace('test_single_', 'DEF-SINGLE-').replace('_', '-').upper()
            
            start = time.time()
            try:
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()
                try:
                    test.debug()
                finally:
                    sys.stdout = old_stdout
                    
                results.append(TestResult(
                    f"def.{test_name}",
                    f"{req_id}: {test.shortDescription() or test_name}",
                    "passed",
                    time.time() - start,
                    category="def",
                    subcategory="requirements"
                ))
            except Exception as e:
                results.append(TestResult(
                    f"def.{test_name}",
                    f"{req_id}: {test.shortDescription() or test_name}",
                    "failed",
                    time.time() - start,
                    str(e),
                    category="def",
                    subcategory="requirements"
                ))
    except ImportError as e:
        results.append(TestResult("def.import", "DEF: Import test module", "failed", 0, str(e), category="def", subcategory="setup"))
    
    return results


def run_yaml_input_tests() -> List[TestResult]:
    """Run YAML-INPUT-xxx requirement tests"""
    results = []
    
    try:
        from tests.python.test_yaml_input import TestYAMLInputRequirements
        import io
        import sys
        
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestYAMLInputRequirements)
        
        for test in suite:
            test_name = str(test).split()[0]
            req_id = test_name.replace('test_yaml_input_', 'YAML-INPUT-').replace('_', '-').upper()
            
            start = time.time()
            try:
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()
                try:
                    test.debug()
                finally:
                    sys.stdout = old_stdout
                    
                results.append(TestResult(
                    f"yaml_input.{test_name}",
                    f"{req_id}: {test.shortDescription() or test_name}",
                    "passed",
                    time.time() - start,
                    category="yaml_input",
                    subcategory="requirements"
                ))
            except Exception as e:
                results.append(TestResult(
                    f"yaml_input.{test_name}",
                    f"{req_id}: {test.shortDescription() or test_name}",
                    "failed",
                    time.time() - start,
                    str(e),
                    category="yaml_input",
                    subcategory="requirements"
                ))
    except ImportError as e:
        results.append(TestResult("yaml_input.import", "YAML-INPUT: Import test module", "failed", 0, str(e), category="yaml_input", subcategory="setup"))
    
    return results


def run_json_input_tests() -> List[TestResult]:
    """Run JSON-INPUT-xxx requirement tests"""
    results = []
    
    try:
        from tests.python.test_json_input import TestJSONInputRequirements
        import io
        import sys
        
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestJSONInputRequirements)
        
        for test in suite:
            test_name = str(test).split()[0]
            req_id = test_name.replace('test_json_input_', 'JSON-INPUT-').replace('_', '-').upper()
            
            start = time.time()
            try:
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()
                try:
                    test.debug()
                finally:
                    sys.stdout = old_stdout
                    
                results.append(TestResult(
                    f"json_input.{test_name}",
                    f"{req_id}: {test.shortDescription() or test_name}",
                    "passed",
                    time.time() - start,
                    category="json_input",
                    subcategory="requirements"
                ))
            except Exception as e:
                results.append(TestResult(
                    f"json_input.{test_name}",
                    f"{req_id}: {test.shortDescription() or test_name}",
                    "failed",
                    time.time() - start,
                    str(e),
                    category="json_input",
                    subcategory="requirements"
                ))
    except ImportError as e:
        results.append(TestResult("json_input.import", "JSON-INPUT: Import test module", "failed", 0, str(e), category="json_input", subcategory="setup"))
    
    return results


def run_equivalence_tests() -> List[TestResult]:
    """Run EQUIV-xxx format equivalence tests"""
    results = []
    
    try:
        from tests.python.test_format_equivalence import TestFormatEquivalence
        import io
        import sys
        
        # Run setUpClass
        TestFormatEquivalence.setUpClass()
        
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestFormatEquivalence)
        
        for test in suite:
            test_name = str(test).split()[0]
            req_id = test_name.replace('test_equiv_', 'EQUIV-').replace('_', '-').upper()
            
            start = time.time()
            try:
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()
                try:
                    test.debug()
                finally:
                    sys.stdout = old_stdout
                    
                results.append(TestResult(
                    f"equiv.{test_name}",
                    f"{req_id}: {test.shortDescription() or test_name}",
                    "passed",
                    time.time() - start,
                    category="equiv",
                    subcategory="requirements"
                ))
            except Exception as e:
                results.append(TestResult(
                    f"equiv.{test_name}",
                    f"{req_id}: {test.shortDescription() or test_name}",
                    "failed",
                    time.time() - start,
                    str(e),
                    category="equiv",
                    subcategory="requirements"
                ))
        
        # Run tearDownClass
        TestFormatEquivalence.tearDownClass()
    except ImportError as e:
        results.append(TestResult("equiv.import", "EQUIV: Import test module", "failed", 0, str(e), category="equiv", subcategory="setup"))
    
    return results


def main():
    print(f"\n{BOLD}Running Axion-HDL Comprehensive Test Suite...{RESET}\n")
    print(f"Testing requirements: AXION, AXI-LITE, PARSER, GEN, ERR, CLI, ADDR, CDC, STRESS, SUB, DEF, YAML-INPUT, JSON-INPUT, EQUIV\n")
    
    all_results = []
    
    # Run Python unit tests (core functionality)
    print(f"  [1/16] Running Python unit tests...", flush=True)
    all_results.extend(run_python_unit_tests())
    
    # Run address conflict tests (ADDR requirements)
    print(f"  [2/16] Running address conflict tests...", flush=True)
    all_results.extend(run_address_conflict_tests())
    
    # Run Parser tests (PARSER requirements)
    print(f"  [3/16] Running parser tests...", flush=True)
    all_results.extend(run_parser_tests())
    
    # Run Generator tests (GEN requirements)
    print(f"  [4/16] Running generator tests...", flush=True)
    all_results.extend(run_generator_tests())
    
    # Run Error handling tests (ERR requirements)
    print(f"  [5/16] Running error handling tests...", flush=True)
    all_results.extend(run_error_handling_tests())
    
    # Run CLI tests (CLI requirements)
    print(f"  [6/16] Running CLI tests...", flush=True)
    all_results.extend(run_cli_tests())
    
    # Run CDC tests (CDC requirements)
    print(f"  [7/16] Running CDC tests...", flush=True)
    all_results.extend(run_cdc_tests())
    
    # Run ADDR tests (ADDR requirements)
    print(f"  [8/16] Running address management tests...", flush=True)
    all_results.extend(run_addr_tests())
    
    # Run STRESS tests (STRESS requirements)
    print(f"  [9/16] Running stress tests...", flush=True)
    all_results.extend(run_stress_tests())
    
    # Run SUB tests (Subregister requirements)
    print(f"  [10/16] Running subregister tests...", flush=True)
    all_results.extend(run_subregister_tests())
    
    # Run DEF tests (DEFAULT attribute requirements)
    print(f"  [11/16] Running default attribute tests...", flush=True)
    all_results.extend(run_default_tests())
    
    # Run YAML-INPUT tests
    print(f"  [12/16] Running YAML input parser tests...", flush=True)
    all_results.extend(run_yaml_input_tests())
    
    # Run JSON-INPUT tests
    print(f"  [13/16] Running JSON input parser tests...", flush=True)
    all_results.extend(run_json_input_tests())
    
    # Run EQUIV tests (format equivalence)
    print(f"  [14/16] Running format equivalence tests...", flush=True)
    all_results.extend(run_equivalence_tests())
    
    # Run VHDL tests (AXION, AXI-LITE requirements)
    print(f"  [15/16] Running VHDL simulation tests...", flush=True)
    all_results.extend(run_vhdl_tests())
    
    # Run C tests
    print(f"  [16/16] Running C header tests...", flush=True)
    all_results.extend(run_c_tests())
    
    # Save and generate reports
    save_results(all_results)
    generate_markdown_report(all_results)
    
    # Print results
    success = print_results(all_results)
    
    # Generate requirement coverage summary
    print_requirement_coverage(all_results)
    
    return 0 if success else 1


def print_requirement_coverage(results: List[TestResult]):
    """Print requirement coverage summary"""
    
    # Extract requirement IDs from test results
    req_pattern = re.compile(r'(AXION-\d+[a-z]?|AXI-LITE-\d+[a-z]?|PARSER-\d+|GEN-\d+|CDC-\d+|ADDR-\d+|ERR-\d+|CLI-\d+|STRESS-\d+|SUB-\d+|DEF-\d+|YAML-INPUT-\d+|JSON-INPUT-\d+|EQUIV-\d+)', re.IGNORECASE)
    
    covered = set()
    for r in results:
        matches = req_pattern.findall(r.name)
        for m in matches:
            covered.add(m.upper())
    
    # Expected requirements
    expected = set()
    for i in range(1, 30):
        expected.add(f"AXION-{i:03d}")
    for i in range(1, 19):
        expected.add(f"AXI-LITE-{i:03d}")
    for i in range(1, 9):
        expected.add(f"PARSER-{i:03d}")
    for i in range(1, 15):
        expected.add(f"GEN-{i:03d}")
    for i in range(1, 8):
        expected.add(f"CDC-{i:03d}")
    for i in range(1, 9):
        expected.add(f"ADDR-{i:03d}")
    for i in range(1, 7):
        expected.add(f"ERR-{i:03d}")
    for i in range(1, 13):
        expected.add(f"CLI-{i:03d}")
    for i in range(1, 7):
        expected.add(f"STRESS-{i:03d}")
    for i in range(1, 13):
        expected.add(f"SUB-{i:03d}")
    for i in range(1, 11):
        expected.add(f"DEF-{i:03d}")
    for i in range(1, 16):
        expected.add(f"YAML-INPUT-{i:03d}")
    for i in range(1, 16):
        expected.add(f"JSON-INPUT-{i:03d}")
    for i in range(1, 7):
        expected.add(f"EQUIV-{i:03d}")
    
    print(f"\n{CYAN}{BOLD}{'═' * 80}{RESET}")
    print(f"{CYAN}{BOLD}  REQUIREMENT COVERAGE SUMMARY{RESET}")
    print(f"{CYAN}{BOLD}{'═' * 80}{RESET}")
    print(f"  Unique Requirement IDs Tested: {len(covered)}")
    print(f"  Base Requirements (from spec):  134")
    print(f"  Total Test Cases:               {len(results)}")
    
    # Categories
    categories = {
        "AXION": [r for r in covered if r.startswith("AXION-")],
        "AXI-LITE": [r for r in covered if r.startswith("AXI-LITE-")],
        "PARSER": [r for r in covered if r.startswith("PARSER-")],
        "GEN": [r for r in covered if r.startswith("GEN-")],
        "CDC": [r for r in covered if r.startswith("CDC-")],
        "ADDR": [r for r in covered if r.startswith("ADDR-")],
        "ERR": [r for r in covered if r.startswith("ERR-")],
        "CLI": [r for r in covered if r.startswith("CLI-")],
        "STRESS": [r for r in covered if r.startswith("STRESS-")],
        "SUB": [r for r in covered if r.startswith("SUB-")],
        "DEF": [r for r in covered if r.startswith("DEF-")],
        "YAML-INPUT": [r for r in covered if r.startswith("YAML-INPUT-")],
        "JSON-INPUT": [r for r in covered if r.startswith("JSON-INPUT-")],
        "EQUIV": [r for r in covered if r.startswith("EQUIV-")]
    }
    
    print(f"\n  By Category:")
    for cat, reqs in categories.items():
        if reqs:
            print(f"    {cat}: {len(reqs)} requirements")
    
    print(f"{'═' * 80}\n")


if __name__ == "__main__":
    sys.exit(main())
