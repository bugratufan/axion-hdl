import pytest
from axion_hdl.rule_checker import RuleChecker

def test_val_005_duplicate_module_names():
    """VAL-005: Error if multiple modules share the same name."""
    checker = RuleChecker()
    
    modules = [
        {
            'name': 'spi_ctrl',
            'base_address': 0x1000,
            'registers': []
        },
        {
            'name': 'i2c_ctrl',
            'base_address': 0x2000,
            'registers': []
        },
        {
            'name': 'spi_ctrl',  # Duplicate name
            'base_address': 0x3000,
            'registers': []
        }
    ]
    
    report = checker.run_all_checks(modules)
    
    # Expect error about duplicate module
    errors = report['errors']
    dup_errors = [e for e in errors if e['type'] == 'Duplicate Module']
    
    assert len(dup_errors) > 0, "Should report duplicate module name error"
    assert dup_errors[0]['module'] == 'spi_ctrl'
    assert "multiple files/definitions" in dup_errors[0]['msg']

def test_val_005_unique_module_names():
    """Verify no error when names are unique."""
    checker = RuleChecker()
    
    modules = [
        {
            'name': 'spi_ctrl',
            'base_address': 0x1000,
            'registers': []
        },
        {
            'name': 'i2c_ctrl',
            'base_address': 0x2000,
            'registers': []
        }
    ]
    
    report = checker.run_all_checks(modules)
    
    errors = [e for e in report['errors'] if e['type'] == 'Duplicate Module']
    assert len(errors) == 0, "Should not report error for unique names"
