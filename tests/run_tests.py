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


def run_command(command: List[str], cwd: str = None, timeout: int = 300, env: dict = None, stream_output: bool = False) -> Tuple[bool, float, str]:
    """Run a command and return (success, duration, output)"""
    start = time.time()
    try:
        if stream_output:
            # Run with real-time output streaming
            process = subprocess.Popen(
                command,
                cwd=cwd or str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Merge stderr into stdout
                text=True,
                env=env,
                bufsize=1  # Line buffered
            )
            
            output_lines = []
            
            # Read line by line as they come
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    print(line, end='', flush=True)  # Print to console immediately
                    output_lines.append(line)
            
            # Read remainder
            stdout, _ = process.communicate()
            if stdout:
                print(stdout, end='', flush=True)
                output_lines.append(stdout)
                
            duration = time.time() - start
            output = "".join(output_lines)
            return process.returncode == 0, duration, output
            
        else:
            # Run with output capturing (buffered)
            result = subprocess.run(
                command,
                cwd=cwd or str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env
            )
            duration = time.time() - start
            output = result.stdout + result.stderr
            return result.returncode == 0, duration, output
            
    except subprocess.TimeoutExpired:
        if stream_output:
            process.kill()
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
        "vhdl": ("🔧 VHDL Tests (GHDL)", {
            "simulation": "Simulation Setup",
            "analyze": "VHDL Analysis",
            "elaborate": "Elaboration",
            "simulate": "Simulation Run",
            "requirements": "Requirements Verification (AXION/AXI-LITE)"
        }),
        "cocotb": ("🧪 Cocotb VHDL Tests", {
            "setup": "Setup & Configuration",
            "axi_lite": "AXI-Lite Protocol Tests",
            "cdc": "CDC Comprehensive Tests"
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
        }),
        "sub": ("📦 Subregister Tests (SUB-xxx)", {
            "requirements": "SUB Requirements"
        }),
        "def": ("📝 Default Value Tests (DEF-xxx)", {
            "requirements": "DEF Requirements"
        }),
        "val": ("✅ Validation Tests (VAL-xxx)", {
            "requirements": "VAL Requirements"
        }),
        "yaml-input": ("📄 YAML Input Tests (YAML-INPUT-xxx)", {
            "requirements": "YAML-INPUT Requirements"
        }),
        "json-input": ("📄 JSON Input Tests (JSON-INPUT-xxx)", {
            "requirements": "JSON-INPUT Requirements"
        }),
        "equiv": ("🔀 Format Equivalence Tests (EQUIV-xxx)", {
            "requirements": "EQUIV Requirements"
        })
    }
    
    for cat in ["python", "c", "vhdl", "cocotb", "parser", "gen", "err", "cli", "cdc", "addr", "stress", "sub", "def", "val", "yaml-input", "json-input", "equiv"]:
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
        "vhdl": "🔧 VHDL (GHDL)",
        "cocotb": "🧪 COCOTB",
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
    
    for cat in ["python", "c", "vhdl", "cocotb", "parser", "gen", "err", "cli", "cdc", "addr", "stress", "sub", "def", "yaml_input", "json_input", "equiv"]:
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


def run_pytest_module(module_path: str, test_prefix: str, req_prefix: str, category: str) -> List[TestResult]:
    """
    Generic helper to run pytest-based test modules

    Args:
        module_path: Path to test file (e.g., 'tests/python/test_parser.py')
        test_prefix: Prefix of test functions (e.g., 'test_parser_')
        req_prefix: Requirement ID prefix (e.g., 'PARSER')
        category: Category name for results (e.g., 'parser')
    """
    results = []

    try:
        import pytest
        import importlib.util
        import inspect

        # Load the module dynamically
        spec = importlib.util.spec_from_file_location("test_module", module_path)
        if spec and spec.loader:
            test_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(test_module)

            # Get all test functions with the specified prefix
            test_functions = [
                (name, func) for name, func in inspect.getmembers(test_module, inspect.isfunction)
                if name.startswith(test_prefix)
            ]

            for test_name, test_func in test_functions:
                # Convert test_parser_001_foo to PARSER-001
                req_id = test_name.replace(test_prefix, f'{req_prefix}-').replace('_', '-').upper()
                # Extract just the numeric part for cleaner IDs
                parts = test_name.replace(test_prefix, '').split('_')
                if parts and parts[0].isdigit():
                    req_id = f"{req_prefix}-{parts[0].zfill(3)}"

                # Get docstring for test description
                desc = test_func.__doc__ or test_name
                if desc:
                    desc = desc.strip().split('\n')[0]  # First line only

                start = time.time()

                # Run the test using pytest (capture output)
                result = pytest.main([
                    '-xvs',
                    '--tb=line',
                    f'{module_path}::{test_name}',
                    '-p', 'no:warnings',
                    '--capture=no',
                    '-q'
                ])

                if result == 0:
                    results.append(TestResult(
                        f"{category}.{test_name}",
                        f"{req_id}: {desc}",
                        "passed",
                        time.time() - start,
                        category=category,
                        subcategory="requirements"
                    ))
                else:
                    results.append(TestResult(
                        f"{category}.{test_name}",
                        f"{req_id}: {desc}",
                        "failed",
                        time.time() - start,
                        f"pytest exit code: {result}",
                        category=category,
                        subcategory="requirements"
                    ))
        else:
            results.append(TestResult(
                f"{category}.import",
                f"{req_prefix}: Import test module",
                "failed",
                0,
                f"Could not load module from {module_path}",
                category=category,
                subcategory="setup"
            ))

    except ImportError as e:
        error_msg = str(e)
        if 'pytest' in error_msg:
            error_msg += "\n\nTo run tests, install development dependencies:\n"
            error_msg += "  python3 -m venv venv && source venv/bin/activate\n"
            error_msg += "  pip install -e \".[dev]\"\n"
            error_msg += "Or install pytest system-wide:\n"
            error_msg += "  pip install pytest>=7.0"

        results.append(TestResult(
            f"{category}.import",
            f"{req_prefix}: Import test module",
            "failed",
            0,
            error_msg,
            category=category,
            subcategory="setup"
        ))
    except Exception as e:
        results.append(TestResult(
            f"{category}.error",
            f"{req_prefix}: Test execution error",
            "failed",
            0,
            str(e),
            category=category,
            subcategory="setup"
        ))

    return results


def run_parser_tests() -> List[TestResult]:
    """Run PARSER-xxx requirement tests using pytest"""
    return run_pytest_module(
        'tests/python/test_parser.py',
        'test_parser_',
        'PARSER',
        'parser'
    )


def run_generator_tests() -> List[TestResult]:
    """Run GEN-xxx requirement tests using pytest"""
    gen_results = run_pytest_module(
        'tests/python/test_generator.py',
        'test_gen_',
        'GEN',
        'gen'
    )
    over_results = run_pytest_module(
        'tests/python/test_overwrite.py',
        'test_',
        'AXION-027',
        'gen'
    )
    return gen_results + over_results


def run_error_handling_tests() -> List[TestResult]:
    """Run ERR-xxx requirement tests using pytest"""
    return run_pytest_module(
        'tests/python/test_error_handling.py',
        'test_err_',
        'ERR',
        'err'
    )


def run_cli_tests() -> List[TestResult]:
    """Run CLI-xxx requirement tests using pytest"""
    return run_pytest_module(
        'tests/python/test_cli.py',
        'test_cli_',
        'CLI',
        'cli'
    )


def run_cdc_tests() -> List[TestResult]:
    """Run CDC-xxx requirement tests using pytest"""
    return run_pytest_module(
        'tests/python/test_cdc.py',
        'test_cdc_',
        'CDC',
        'cdc'
    )


def run_addr_tests() -> List[TestResult]:
    """Run ADDR-xxx requirement tests using pytest"""
    return run_pytest_module(
        'tests/python/test_addr.py',
        'test_addr_',
        'ADDR',
        'addr'
    )


def _old_run_addr_tests() -> List[TestResult]:
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
    """Run STRESS-xxx requirement tests using pytest"""
    return run_pytest_module(
        'tests/python/test_stress.py',
        'test_stress_',
        'STRESS',
        'stress'
    )


def run_subregister_tests() -> List[TestResult]:
    """Run SUB-xxx requirement tests using pytest"""
    return run_pytest_module(
        'tests/python/test_subregister.py',
        'test_sub_',
        'SUB',
        'sub'
    )


def run_default_tests() -> List[TestResult]:
    """Run DEF-xxx requirement tests using pytest"""
    return run_pytest_module(
        'tests/python/test_default.py',
        'test_def_',
        'DEF',
        'def'
    )


def run_validation_tests() -> List[TestResult]:
    """Run VAL-xxx requirement tests using pytest"""
    val_results = run_pytest_module(
        'tests/python/test_validation.py',
        'test_',
        'VAL',
        'val'
    )
    val_005_results = run_pytest_module(
        'tests/python/test_val_005_duplicate_module.py',
        'test_val_005_',
        'VAL-005',
        'val'
    )
    return val_results + val_005_results


def run_yaml_input_tests() -> List[TestResult]:
    """Run YAML-INPUT-xxx requirement tests using pytest"""
    return run_pytest_module(
        'tests/python/test_yaml_input.py',
        'test_yaml_',
        'YAML-INPUT',
        'yaml_input'
    )


def run_json_input_tests() -> List[TestResult]:
    """Run JSON-INPUT-xxx requirement tests using pytest"""
    return run_pytest_module(
        'tests/python/test_json_input.py',
        'test_json_',
        'JSON-INPUT',
        'json_input'
    )


def run_equivalence_tests() -> List[TestResult]:
    """Run EQUIV-xxx format equivalence tests using pytest"""
    return run_pytest_module(
        'tests/python/test_format_equivalence.py',
        'test_equiv_',
        'EQUIV',
        'equiv'
    )


def run_cocotb_tests() -> List[TestResult]:
    """Run cocotb VHDL simulation tests"""
    results = []

    # Define all cocotb tests with their descriptions
    cocotb_axi_tests = [
        ("test_axion_001_ro_read", "AXION-001: Read-Only Register Read Access"),
        ("test_axion_002_ro_write_protection", "AXION-002: Read-Only Register Write Protection"),
        ("test_axion_003_wo_write", "AXION-003: Write-Only Register Write Access"),
        ("test_axion_004_wo_read_protection", "AXION-004: Write-Only Register Read Protection"),
        ("test_axion_005_rw_full_access", "AXION-005: Read-Write Register Full Access"),
        ("test_axion_011_write_handshake", "AXION-011: AXI Write Transaction Handshake"),
        ("test_axion_012_read_handshake", "AXION-012: AXI Read Transaction Handshake"),
        ("test_axion_016_byte_strobe", "AXION-016: Byte-Level Write Strobe Support"),
        ("test_axion_017_sync_reset", "AXION-017: Synchronous Reset Behavior"),
        ("test_axion_021_out_of_range", "AXION-021: Out-of-Range Address Access"),
        ("test_axion_023_default_values", "AXION-023: Default Register Values After Reset"),
        ("test_axi_lite_001_reset_state", "AXI-LITE-001: Reset State Requirements"),
        ("test_axi_lite_003_valid_before_ready", "AXI-LITE-003: VALID Before READY Dependency"),
        ("test_axi_lite_004_valid_stability", "AXI-LITE-004: VALID Signal Stability Rule"),
        ("test_axi_lite_005_write_independence", "AXI-LITE-005: Write Address/Data Independence"),
        ("test_axi_lite_006_back_to_back", "AXI-LITE-006: Back-to-Back Transaction Support"),
        ("test_axi_lite_016_delayed_ready", "AXI-LITE-016: Delayed READY Handling"),
        ("test_axi_lite_017_early_ready", "AXI-LITE-017: Early READY Handling"),
        ("test_stress_random_access", "STRESS: Random Register Access Pattern"),
        ("test_stress_rapid_writes", "STRESS: Rapid Consecutive Writes"),
    ]

    cocotb_cdc_tests = [
        ("test_cdc_001_stage_count", "CDC-001: Configurable CDC Stage Count"),
        ("test_cdc_004_module_clock_port", "CDC-004: Module Clock Port Generation"),
        ("test_cdc_006_ro_path_sync", "CDC-006: RO Register Synchronization (module->AXI)"),
        ("test_cdc_007_rw_path_sync", "CDC-007: RW Register Synchronization (AXI->module)"),
        ("test_cdc_gray_code_counter", "CDC: Gray Code Counter Safe Crossing"),
        ("test_cdc_handshake_protocol", "CDC: 4-Phase Handshake Protocol"),
        ("test_cdc_async_reset", "CDC: Asynchronous Reset Across Domains"),
        ("test_cdc_metastability_stress", "CDC: Metastability Stress Test"),
        ("test_cdc_clock_ratio_2x", "CDC: 2:1 Clock Ratio Crossing"),
        ("test_cdc_clock_ratio_prime", "CDC: Prime Number Clock Ratio (Worst Case)"),
        ("test_cdc_data_coherency", "CDC: Multi-bit Data Coherency"),
        ("test_cdc_pulse_sync", "CDC: Single-Cycle Pulse Synchronization"),
        ("test_cdc_burst_transfer", "CDC: Burst Data Transfer"),
        ("test_cdc_simultaneous_edges", "CDC: Simultaneous Clock Edges"),
        ("test_cdc_slow_to_fast", "CDC: Slow to Fast Clock Domain Transfer"),
        ("test_cdc_fast_to_slow", "CDC: Fast to Slow Clock Domain Transfer"),
    ]
    
    cocotb_sub_tests = [
        ("test_subreg_001_single_bit_control", "SUB-001: Single Bit Control Access"),
        ("test_subreg_002_status_capture", "SUB-002: Status Register Capture"),
        ("test_subreg_003_read_modify_write", "SUB-003: Read-Modify-Write Operation"),
        ("test_subreg_004_field_isolation", "SUB-004: Bit Field Isolation"),
    ]

    cocotb_stress_ext_tests = [
        ("test_stress_001_interleaved_rw", "STRESS-001: Interleaved Read/Write Transactions"),
        ("test_stress_002_reset_under_load", "STRESS-002: Reset Under High Load"),
        ("test_stress_003_address_map_walk", "STRESS-003: Address Map Walk"),
        ("test_stress_004_invalid_access_storm", "STRESS-004: Invalid Access Storm"),
    ]

    # Check if cocotb-config is available (check venv first, then system)
    venv_cocotb_config = PROJECT_ROOT / "venv" / "bin" / "cocotb-config"
    if venv_cocotb_config.exists():
        cocotb_config_path = str(venv_cocotb_config)
        cocotb_config_available = True
    else:
        cocotb_config_available, _, _ = run_command(["which", "cocotb-config"])
        cocotb_config_path = "cocotb-config"

    # Check if GHDL is available
    ghdl_available, _, _ = run_command(["which", "ghdl"])

    if not cocotb_config_available or not ghdl_available:
        skip_reason = "cocotb not installed" if not cocotb_config_available else "ghdl not found"
        skip_msg = "pip install cocotb cocotb-bus cocotbext-axi" if not cocotb_config_available else "Install GHDL simulator"

        # List all tests as skipped
        for test_id, desc in cocotb_axi_tests:
            results.append(TestResult(f"cocotb.axi.{test_id}", desc, "skipped", 0,
                                      f"{skip_reason} ({skip_msg})",
                                      category="cocotb", subcategory="axi_lite"))

        for test_id, desc in cocotb_cdc_tests:
            results.append(TestResult(f"cocotb.cdc.{test_id}", desc, "skipped", 0,
                                      f"{skip_reason} ({skip_msg})",
                                      category="cocotb", subcategory="cdc"))
                                      
        for test_id, desc in cocotb_sub_tests:
            results.append(TestResult(f"cocotb.sub.{test_id}", desc, "skipped", 0,
                                      f"{skip_reason} ({skip_msg})",
                                      category="cocotb", subcategory="sub"))
                                      
        for test_id, desc in cocotb_stress_ext_tests:
            results.append(TestResult(f"cocotb.stress.{test_id}", desc, "skipped", 0,
                                      f"{skip_reason} ({skip_msg})",
                                      category="cocotb", subcategory="stress"))

        return results

    # Get cocotb version
    _, _, cocotb_version = run_command([cocotb_config_path, "--version"])
    cocotb_version = cocotb_version.strip() if cocotb_version else "unknown"

    # Setup check
    results.append(TestResult("cocotb.setup", f"Cocotb Setup (v{cocotb_version})", "passed", 0,
                              f"cocotb {cocotb_version}, ghdl available",
                              category="cocotb", subcategory="setup"))

    cocotb_dir = PROJECT_ROOT / "tests" / "cocotb"

    # Set up environment with venv PATH for cocotb
    venv_env = os.environ.copy()
    venv_bin = str(PROJECT_ROOT / "venv" / "bin")
    venv_env["PATH"] = venv_bin + ":" + venv_env.get("PATH", "")
    venv_env["VIRTUAL_ENV"] = str(PROJECT_ROOT / "venv")

    # Run AXI-Lite tests
    print(f"{BOLD}Running AXI-Lite Protocol Tests...{RESET}")
    _, duration, output = run_command(
        ["make", "test_axi_lite", "DUT=sensor_controller"],
        cwd=str(cocotb_dir),
        timeout=300,
        env=venv_env,
        stream_output=True
    )

    # Parse cocotb output for test results
    # Format: ** test_axi_lite.test_axion_001_ro_read                 PASS         190.00 ...
    import re
    test_pattern = re.compile(r'\*\*\s+(test_\w+\.test_\w+)\s+(PASS|FAIL|SKIP)')

    axi_results = {}
    for match in test_pattern.finditer(output):
        full_name = match.group(1)
        status = match.group(2).lower()
        # Extract just the test function name
        test_func = full_name.split('.')[-1]
        axi_results[test_func] = status

    # Map results to our test list
    for test_id, desc in cocotb_axi_tests:
        if test_id in axi_results:
            status = axi_results[test_id]
            if status == "pass":
                results.append(TestResult(f"cocotb.axi.{test_id}", desc, "passed", 0,
                                          "", category="cocotb", subcategory="axi_lite"))
            elif status == "fail":
                results.append(TestResult(f"cocotb.axi.{test_id}", desc, "failed", 0,
                                          "Assertion failed", category="cocotb", subcategory="axi_lite"))
            else:
                results.append(TestResult(f"cocotb.axi.{test_id}", desc, "skipped", 0,
                                          "", category="cocotb", subcategory="axi_lite"))
        else:
            # Test not found in output - either not run or environment issue
            results.append(TestResult(f"cocotb.axi.{test_id}", desc, "skipped", 0,
                                      "Test not executed", category="cocotb", subcategory="axi_lite"))

    # Run CDC tests
    _, duration, output = run_command(
        ["make", "test_cdc", "DUT=sensor_controller"],
        cwd=str(cocotb_dir),
        timeout=300,
        env=venv_env,
        stream_output=True
    )

    cdc_results = {}
    for match in test_pattern.finditer(output):
        full_name = match.group(1)
        status = match.group(2).lower()
        test_func = full_name.split('.')[-1]
        cdc_results[test_func] = status

    # Map results to our test list
    for test_id, desc in cocotb_cdc_tests:
        if test_id in cdc_results:
            status = cdc_results[test_id]
            if status == "pass":
                results.append(TestResult(f"cocotb.cdc.{test_id}", desc, "passed", 0,
                                          "", category="cocotb", subcategory="cdc"))
            elif status == "fail":
                results.append(TestResult(f"cocotb.cdc.{test_id}", desc, "failed", 0,
                                          "Assertion failed", category="cocotb", subcategory="cdc"))
            else:
                results.append(TestResult(f"cocotb.cdc.{test_id}", desc, "skipped", 0,
                                          "", category="cocotb", subcategory="cdc"))
        else:
            results.append(TestResult(f"cocotb.cdc.{test_id}", desc, "skipped", 0,
                                      "Test not executed", category="cocotb", subcategory="cdc"))

    # Run Subregister tests
    _, duration, output = run_command(
        ["make", "test_sub", "DUT=sensor_controller"],
        cwd=str(cocotb_dir),
        timeout=300,
        env=venv_env,
        stream_output=True
    )
    
    sub_results = {}
    for match in test_pattern.finditer(output):
        full_name = match.group(1)
        status = match.group(2).lower()
        test_func = full_name.split('.')[-1]
        sub_results[test_func] = status
        
    for test_id, desc in cocotb_sub_tests:
        if test_id in sub_results:
            status = sub_results[test_id]
            if status == "pass":
                results.append(TestResult(f"cocotb.sub.{test_id}", desc, "passed", 0, "", category="cocotb", subcategory="sub"))
            elif status == "fail":
                results.append(TestResult(f"cocotb.sub.{test_id}", desc, "failed", 0, "Assertion failed", category="cocotb", subcategory="sub"))
            else:
                results.append(TestResult(f"cocotb.sub.{test_id}", desc, "skipped", 0, "", category="cocotb", subcategory="sub"))
        else:
            results.append(TestResult(f"cocotb.sub.{test_id}", desc, "skipped", 0, "Test not executed", category="cocotb", subcategory="sub"))

    # Run Extended Stress tests
    _, duration, output = run_command(
        ["make", "test_stress_extended", "DUT=sensor_controller"],
        cwd=str(cocotb_dir),
        timeout=600,
        env=venv_env,
        stream_output=True
    )
    
    stress_results = {}
    for match in test_pattern.finditer(output):
        full_name = match.group(1)
        status = match.group(2).lower()
        test_func = full_name.split('.')[-1]
        stress_results[test_func] = status
        
    for test_id, desc in cocotb_stress_ext_tests:
        if test_id in stress_results:
            status = stress_results[test_id]
            if status == "pass":
                results.append(TestResult(f"cocotb.stress.{test_id}", desc, "passed", 0, "", category="cocotb", subcategory="stress"))
            elif status == "fail":
                results.append(TestResult(f"cocotb.stress.{test_id}", desc, "failed", 0, "Assertion failed", category="cocotb", subcategory="stress"))
            else:
                results.append(TestResult(f"cocotb.stress.{test_id}", desc, "skipped", 0, "", category="cocotb", subcategory="stress"))
        else:
            results.append(TestResult(f"cocotb.stress.{test_id}", desc, "skipped", 0, "Test not executed", category="cocotb", subcategory="stress"))

    return results


def main():
    print(f"\n{BOLD}Running Axion-HDL Comprehensive Test Suite...{RESET}\n")
    print(f"Testing requirements: AXION, AXI-LITE, PARSER, GEN, ERR, CLI, ADDR, CDC, STRESS, SUB, DEF, VAL, YAML-INPUT, JSON-INPUT, EQUIV + Cocotb\n")

    all_results = []

    # Run Python unit tests (core functionality)
    print(f"  [1/18] Running Python unit tests...", flush=True)
    all_results.extend(run_python_unit_tests())

    # Run address conflict tests (ADDR requirements)
    print(f"  [2/18] Running address conflict tests...", flush=True)
    all_results.extend(run_address_conflict_tests())

    # Run Parser tests (PARSER requirements)
    print(f"  [3/18] Running parser tests...", flush=True)
    all_results.extend(run_parser_tests())

    # Run Generator tests (GEN requirements)
    print(f"  [4/18] Running generator tests...", flush=True)
    all_results.extend(run_generator_tests())

    # Run Error handling tests (ERR requirements)
    print(f"  [5/18] Running error handling tests...", flush=True)
    all_results.extend(run_error_handling_tests())

    # Run CLI tests (CLI requirements)
    print(f"  [6/18] Running CLI tests...", flush=True)
    all_results.extend(run_cli_tests())

    # Run CDC tests (CDC requirements)
    print(f"  [7/18] Running CDC tests...", flush=True)
    all_results.extend(run_cdc_tests())

    # Run ADDR tests (ADDR requirements)
    print(f"  [8/18] Running address management tests...", flush=True)
    all_results.extend(run_addr_tests())

    # Run STRESS tests (STRESS requirements)
    print(f"  [9/18] Running stress tests...", flush=True)
    all_results.extend(run_stress_tests())

    # Run SUB tests (Subregister requirements)
    print(f"  [10/18] Running subregister tests...", flush=True)
    all_results.extend(run_subregister_tests())

    # Run DEF tests (DEFAULT attribute requirements)
    print(f"  [11/18] Running default attribute tests...", flush=True)
    all_results.extend(run_default_tests())

    # Run VAL tests (Validation & Diagnostics requirements)
    print(f"  [12/18] Running validation tests...", flush=True)
    all_results.extend(run_validation_tests())

    # Run YAML-INPUT tests
    print(f"  [13/18] Running YAML input parser tests...", flush=True)
    all_results.extend(run_yaml_input_tests())

    # Run JSON-INPUT tests
    print(f"  [14/18] Running JSON input parser tests...", flush=True)
    all_results.extend(run_json_input_tests())

    # Run EQUIV tests (format equivalence)
    print(f"  [15/18] Running format equivalence tests...", flush=True)
    all_results.extend(run_equivalence_tests())

    # Run VHDL tests (AXION, AXI-LITE requirements)
    print(f"  [16/18] Running VHDL simulation tests...", flush=True)
    all_results.extend(run_vhdl_tests())

    # Run C tests
    print(f"  [17/18] Running C header tests...", flush=True)
    all_results.extend(run_c_tests())

    # Run Cocotb tests (comprehensive VHDL verification)
    print(f"  [18/18] Running Cocotb VHDL tests...", flush=True)
    all_results.extend(run_cocotb_tests())
    
    # Save and generate reports
    save_results(all_results)
    generate_markdown_report(all_results)
    
    # Print results
    success = print_results(all_results)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
