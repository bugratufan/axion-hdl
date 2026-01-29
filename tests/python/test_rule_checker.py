import pytest
from axion_hdl.rule_checker import RuleChecker

@pytest.fixture
def checker():
    return RuleChecker()

def test_overlap_detection(checker):
    """Verify detection of overlapping modules."""
    modules = [
        {'name': 'mod1', 'base_address': 0x00, 'registers': [{'address_int': 0x00, 'width': 32}]}, # 0x00-0x03
        {'name': 'mod2', 'base_address': 0x02, 'registers': [{'address_int': 0x02, 'width': 32}]}  # 0x02-0x05 (OVERLAP)
    ]
    checker.check_address_overlaps(modules)
    # 2 errors reported (one for each module involved in the overlap)
    assert len(checker.errors) == 2
    assert checker.errors[0]['type'] == "Address Overlap"
    assert "overlaps" in checker.errors[0]['msg']

def test_default_value_check(checker):
    """Verify that default values fit in register width."""
    modules = [{
        'name': 'mod_def',
        'registers': [
            {'reg_name': 'ok_reg', 'width': 8, 'default_value': 0xFF}, # OK
            {'reg_name': 'bad_reg', 'width': 4, 'default_value': 0x1F} # 5 bits needed -> Error
        ]
    }]
    checker.check_default_values(modules)
    assert len(checker.errors) == 1
    assert "exceeds 4-bit range" in checker.errors[0]['msg']

def test_naming_conventions(checker):
    """Verify identifier naming rules."""
    modules = [{
        'name': 'valid_mod',
        'registers': [
            {'reg_name': 'ValidReg', 'width': 32}, # OK
            {'reg_name': '1nvalid', 'width': 32},  # Error
            {'reg_name': 'signal', 'width': 32},   # Error: Reserved
            {'reg_name': 'bad__reg', 'width': 32}  # Warning: double underscore
        ]
    }]
    checker.check_naming_conventions(modules)
    
    errors = [e['msg'] for e in checker.errors]
    warnings = [w['msg'] for w in checker.warnings]
    
    assert any("invalid identifier" in e for e in errors)
    assert any("reserved keyword" in e for e in errors)
    assert any("double underscore" in w for w in warnings)

def test_address_alignment(checker):
    """Verify 4-byte alignment warning."""
    modules = [{
        'name': 'mod_align',
        'registers': [
            {'reg_name': 'aligned', 'address_int': 0x04, 'width': 32},
            {'reg_name': 'unaligned', 'address_int': 0x05, 'width': 32},
        ]
    }]
    checker.check_address_alignment(modules)
    assert len(checker.warnings) == 1
    assert "not 4-byte aligned" in checker.warnings[0]['msg']

def test_duplicate_names(checker):
    """Verify duplicate register name detection."""
    modules = [{
        'name': 'mod_dup',
        'registers': [
            {'reg_name': 'my_reg', 'width': 32},
            {'reg_name': 'my_reg', 'width': 32},
        ]
    }]
    checker.check_duplicate_names(modules)
    assert len(checker.errors) == 1
    assert "defined multiple times" in checker.errors[0]['msg']
