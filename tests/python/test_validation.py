import pytest
import os
from axion_hdl.json_input_parser import JSONInputParser
from axion_hdl.yaml_input_parser import YAMLInputParser
from axion_hdl.xml_input_parser import XMLInputParser
from axion_hdl.rule_checker import RuleChecker

def test_json_missing_module_field(tmp_path):
    """VAL-001: Missing 'module' field in JSON must be reported as Error."""
    p = tmp_path / "bad.json"
    p.write_text('{"registers": []}') # No module field
    
    parser = JSONInputParser()
    module = parser.parse_file(str(p))
    
    assert module is None
    assert len(parser.errors) >= 1
    assert "Missing 'module' field" in parser.errors[0]['msg']

def test_yaml_missing_module_field(tmp_path):
    """VAL-001: Missing 'module' field in YAML must be reported as Error."""
    p = tmp_path / "bad.yaml"
    p.write_text('registers: []') # No module field
    
    parser = YAMLInputParser()
    module = parser.parse_file(str(p))
    
    assert module is None
    assert len(parser.errors) >= 1
    assert "Missing 'module' field" in parser.errors[0]['msg']

def test_xml_missing_module_attr(tmp_path):
    """VAL-001: Missing 'module' attribute in XML must be reported as Error."""
    p = tmp_path / "bad.xml"
    p.write_text('<register_map registers="[]"></register_map>') # No module attribute
    
    parser = XMLInputParser()
    module = parser.parse_file(str(p))
    
    assert module is None
    assert len(parser.errors) >= 1
    assert "Missing 'module' attribute" in parser.errors[0]['msg']

def test_syntax_error(tmp_path):
    """VAL-002: Syntax error must be reported."""
    p = tmp_path / "broken.json"
    p.write_text('{ broken }')
    
    parser = JSONInputParser()
    module = parser.parse_file(str(p))
    
    assert module is None
    assert len(parser.errors) >= 1
    # Error message format depends on Python version/json lib, but definitely an error

def test_check_documentation_warning():
    """VAL-004: Missing descriptions must raise warning."""
    checker = RuleChecker()
    modules = [{
        'name': 'undoc_mod',
        'registers': [
            {'name': 'r1', 'description': ''}, # Empty
            {'name': 'r2', 'description': 'Good desc'},
            {'name': 'r3'} # Missing key
        ]
    }]
    
    checker.run_all_checks(modules)
    
    warnings = [w for w in checker.warnings if w['type'] == 'Missing Documentation']
    assert len(warnings) == 1
    assert "2 registers are missing descriptions" in warnings[0]['msg']


def test_val_003_logical_integrity_check():
    """VAL-003: Validates integrity of loaded modules (non-empty register lists)."""
    checker = RuleChecker()
    modules = [
        {'name': 'empty_mod', 'registers': []},  # Invalid - empty registers
        {'name': 'valid_mod', 'registers': [{'name': 'r1'}]}  # Valid
    ]
    
    checker.run_all_checks(modules)
    
    # Check for integrity warnings about empty register list
    integrity_issues = [w for w in checker.warnings if 'empty_mod' in w.get('module', '')]
    assert len(integrity_issues) >= 1, "Should warn about module with empty register list"

