#!/usr/bin/env python3
"""
Append GUI test results to TEST_RESULTS.md
"""

import sys
import re
import os

def parse_gui_test_output(output_file):
    """Parse pytest output and extract test results."""
    results = []
    
    with open(output_file, 'r') as f:
        content = f.read()
    
    # Parse test results from pytest verbose output
    # Format: tests/python/test_gui.py::TestClass::test_name[chromium] PASSED/FAILED
    pattern = r'test_gui\.py::(\w+)::(\w+)\[chromium\]\s+(PASSED|FAILED)'
    matches = re.findall(pattern, content)
    
    for class_name, test_name, status in matches:
        # Extract requirement ID from test name (e.g., test_dash_001 -> GUI-DASH-001)
        match = re.search(r'test_(\w+)_(\d+)', test_name)
        if match:
            prefix = match.group(1).upper()
            num = match.group(2)
            req_id = f"GUI-{prefix}-{num}"
        else:
            req_id = test_name.upper()
        
        results.append({
            'class': class_name,
            'test': test_name,
            'req_id': req_id,
            'status': status
        })
    
    return results


def append_to_test_results(results):
    """Append GUI test results to TEST_RESULTS.md."""
    if not results:
        print("No GUI test results to append.")
        return
    
    test_results_file = 'TEST_RESULTS.md'
    
    # Group by category
    categories = {}
    for r in results:
        cat = r['class'].replace('TestGUI', '')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(r)
    
    # Build the GUI section
    gui_section = []
    gui_section.append("")
    gui_section.append("## GUI Test Results")
    gui_section.append("")
    
    total_passed = sum(1 for r in results if r['status'] == 'PASSED')
    total_failed = sum(1 for r in results if r['status'] == 'FAILED')
    total = len(results)
    
    gui_section.append(f"**Total: {total} tests ({total_passed} passed, {total_failed} failed)**")
    gui_section.append("")
    
    for cat, cat_results in sorted(categories.items()):
        passed = sum(1 for r in cat_results if r['status'] == 'PASSED')
        gui_section.append(f"### GUI-{cat.upper()} ({passed}/{len(cat_results)} passed)")
        gui_section.append("")
        gui_section.append("| Requirement | Test | Status |")
        gui_section.append("|-------------|------|--------|")
        
        for r in cat_results:
            status_icon = "✓" if r['status'] == 'PASSED' else "✗"
            gui_section.append(f"| {r['req_id']} | {r['test']} | {status_icon} {r['status']} |")
        
        gui_section.append("")
    
    # Read existing file and check if GUI section exists
    if os.path.exists(test_results_file):
        with open(test_results_file, 'r') as f:
            content = f.read()
        
        # Remove existing GUI section if present
        if '## GUI Test Results' in content:
            content = re.sub(r'\n## GUI Test Results.*', '', content, flags=re.DOTALL)
        
        # Append new GUI section
        with open(test_results_file, 'w') as f:
            f.write(content.rstrip() + '\n' + '\n'.join(gui_section))
    else:
        with open(test_results_file, 'w') as f:
            f.write('\n'.join(gui_section))
    
    print(f"GUI test results appended to {test_results_file}")
    print(f"  {total_passed}/{total} tests passed")


def update_coverage_summary(results):
    """Update the requirement coverage summary in TEST_RESULTS.md to include GUI requirements."""
    if not results:
        return
    
    test_results_file = 'TEST_RESULTS.md'
    
    if not os.path.exists(test_results_file):
        return
    
    with open(test_results_file, 'r') as f:
        content = f.read()
    
    # Count unique GUI requirements
    gui_reqs = set(r['req_id'] for r in results)
    gui_count = len(gui_reqs)
    
    # Update the coverage summary section
    # Find the "By Category:" section and add GUI
    if 'By Category:' in content:
        # Check if GUI already exists
        if 'GUI:' not in content:
            # Add GUI line after "By Category:"
            pattern = r'(By Category:\n)'
            replacement = f'\\1    GUI: {gui_count} requirements\n'
            content = re.sub(pattern, replacement, content)
            
            with open(test_results_file, 'w') as f:
                f.write(content)
            
            print(f"  Added GUI: {gui_count} requirements to coverage summary")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: append_gui_results.py <pytest_output_file>")
        sys.exit(1)
    
    output_file = sys.argv[1]
    
    if not os.path.exists(output_file):
        print(f"Error: {output_file} not found")
        sys.exit(1)
    
    results = parse_gui_test_output(output_file)
    append_to_test_results(results)
    update_coverage_summary(results)
