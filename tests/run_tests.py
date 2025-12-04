#!/usr/bin/env python3
"""
Test runner with detailed results and markdown report generation for Axion-HDL

This runner executes all tests and generates a detailed TEST_RESULTS.md file
with individual test results for each sub-test.
"""

import subprocess
import sys
import os
import time
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple
from pathlib import Path

# ANSI colors
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
        axion = AxionHDL(output_dir=str(PROJECT_ROOT / "output"))
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
        axion = AxionHDL(output_dir=str(PROJECT_ROOT / "output"))
        axion.add_src(str(PROJECT_ROOT / "tests" / "vhdl"))
        axion.exclude("error_cases")
        axion.analyze()
        axion.generate_vhdl()
        # Check output files exist
        vhdl_files = list((PROJECT_ROOT / "output").glob("*_axion_reg.vhd"))
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
        axion = AxionHDL(output_dir=str(PROJECT_ROOT / "output"))
        axion.add_src(str(PROJECT_ROOT / "tests" / "vhdl"))
        axion.exclude("error_cases")
        axion.analyze()
        axion.generate_c_header()
        c_files = list((PROJECT_ROOT / "output").glob("*_regs.h"))
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
        axion = AxionHDL(output_dir=str(PROJECT_ROOT / "output"))
        axion.add_src(str(PROJECT_ROOT / "tests" / "vhdl"))
        axion.exclude("error_cases")
        axion.analyze()
        axion.generate_xml()
        xml_files = list((PROJECT_ROOT / "output").glob("*_regs.xml"))
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
        axion = AxionHDL(output_dir=str(PROJECT_ROOT / "output"))
        axion.add_src(str(PROJECT_ROOT / "tests" / "vhdl"))
        axion.exclude("error_cases")
        axion.analyze()
        axion.generate_documentation(format="md")
        doc_file = PROJECT_ROOT / "output" / "register_map.md"
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
            
            try:
                axion.analyze()
                results.append(TestResult(test_id, name, "failed", time.time() - start,
                                          "No AddressConflictError raised",
                                          category="python", subcategory="conflict"))
            except AddressConflictError as e:
                results.append(TestResult(test_id, name, "passed", time.time() - start,
                                          "AddressConflictError correctly raised",
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
            
            try:
                axion.analyze()
                results.append(TestResult(test_id, name, "failed", time.time() - start,
                                          "Wide signal overlap not detected",
                                          category="python", subcategory="conflict"))
            except AddressConflictError as e:
                results.append(TestResult(test_id, name, "passed", time.time() - start,
                                          "Wide signal overlap correctly detected",
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
    work_dir.mkdir(exist_ok=True)
    
    ghdl_opts = ["--std=08", f"--workdir={work_dir}"]
    
    # Test 2: Analyze sensor_controller.vhd
    test_id = "vhdl.analyze.sensor_controller"
    name = "Analyze sensor_controller.vhd"
    vhdl_file = PROJECT_ROOT / "tests" / "vhdl" / "sensor_controller.vhd"
    success, duration, output = run_command(["ghdl", "-a"] + ghdl_opts + [str(vhdl_file)])
    status = "passed" if success else "failed"
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
    
    # Test 4: Analyze mixed_width_controller.vhd
    test_id = "vhdl.analyze.mixed_width"
    name = "Analyze mixed_width_controller.vhd"
    vhdl_file = PROJECT_ROOT / "tests" / "vhdl" / "mixed_width_controller.vhd"
    success, duration, output = run_command(["ghdl", "-a"] + ghdl_opts + [str(vhdl_file)])
    status = "passed" if success else "failed"
    results.append(TestResult(test_id, name, status, duration, output,
                              category="vhdl", subcategory="analyze"))
    
    # Test 5: Analyze generated sensor_controller_axion_reg.vhd
    test_id = "vhdl.analyze.sensor_axion"
    name = "Analyze sensor_controller_axion_reg.vhd"
    vhdl_file = PROJECT_ROOT / "output" / "sensor_controller_axion_reg.vhd"
    if vhdl_file.exists():
        success, duration, output = run_command(["ghdl", "-a"] + ghdl_opts + [str(vhdl_file)])
        status = "passed" if success else "failed"
    else:
        success, duration, output = False, 0, "File not found"
        status = "failed"
    results.append(TestResult(test_id, name, status, duration, output,
                              category="vhdl", subcategory="analyze"))
    
    # Test 6: Analyze generated spi_controller_axion_reg.vhd
    test_id = "vhdl.analyze.spi_axion"
    name = "Analyze spi_controller_axion_reg.vhd"
    vhdl_file = PROJECT_ROOT / "output" / "spi_controller_axion_reg.vhd"
    if vhdl_file.exists():
        success, duration, output = run_command(["ghdl", "-a"] + ghdl_opts + [str(vhdl_file)])
        status = "passed" if success else "failed"
    else:
        success, duration, output = False, 0, "File not found"
        status = "failed"
    results.append(TestResult(test_id, name, status, duration, output,
                              category="vhdl", subcategory="analyze"))
    
    # Test 7: Analyze generated mixed_width_controller_axion_reg.vhd
    test_id = "vhdl.analyze.mixed_axion"
    name = "Analyze mixed_width_controller_axion_reg.vhd"
    vhdl_file = PROJECT_ROOT / "output" / "mixed_width_controller_axion_reg.vhd"
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
    success, duration, output = run_command(["ghdl", "-e"] + ghdl_opts + ["multi_module_tb"])
    status = "passed" if success else "failed"
    results.append(TestResult(test_id, name, status, duration, output,
                              category="vhdl", subcategory="elaborate"))
    
    # Test 10: Run simulation and parse individual test results
    test_id = "vhdl.simulate.testbench"
    name = "Run multi_module_tb Simulation"
    waveform_dir = PROJECT_ROOT / "waveforms"
    waveform_dir.mkdir(exist_ok=True)
    wave_file = waveform_dir / "multi_module_tb_wave.ghw"
    
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
        results.append(TestResult(test_id, name, status, duration, output,
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
            "requirements": "Requirements Verification (53 test cases)"
        })
    }
    
    for cat in ["python", "c", "vhdl"]:
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
        "vhdl": "🔧 VHDL"
    }
    
    total_passed = 0
    total_failed = 0
    total_skipped = 0
    total_time = 0.0
    
    print()
    print(f"{CYAN}{BOLD}{'═' * 80}{RESET}")
    print(f"{CYAN}{BOLD}  AXION-HDL TEST RESULTS{RESET}")
    print(f"{CYAN}{BOLD}{'═' * 80}{RESET}")
    
    for cat in ["python", "c", "vhdl"]:
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


def main():
    print(f"\n{BOLD}Running Axion-HDL Test Suite...{RESET}\n")
    
    all_results = []
    
    # Run Python unit tests
    print(f"  Running Python unit tests...", flush=True)
    all_results.extend(run_python_unit_tests())
    
    # Run address conflict tests
    print(f"  Running address conflict tests...", flush=True)
    all_results.extend(run_address_conflict_tests())
    
    # Run C tests
    print(f"  Running C header tests...", flush=True)
    all_results.extend(run_c_tests())
    
    # Run VHDL tests
    print(f"  Running VHDL simulation tests...", flush=True)
    all_results.extend(run_vhdl_tests())
    
    # Save and generate reports
    save_results(all_results)
    generate_markdown_report(all_results)
    
    # Print results
    success = print_results(all_results)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
