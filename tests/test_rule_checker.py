import unittest
from axion_hdl.rule_checker import RuleChecker

class TestRuleChecker(unittest.TestCase):
    def setUp(self):
        self.checker = RuleChecker()

    def test_overlap_detection(self):
        modules = [
            {'name': 'mod1', 'base_address': 0x00, 'registers': [{'address_int': 0x00, 'width': 32}]}, # 0x00-0x03
            {'name': 'mod2', 'base_address': 0x02, 'registers': [{'address_int': 0x02, 'width': 32}]}  # 0x02-0x05 (OVERLAP)
        ]
        self.checker.check_address_overlaps(modules)
        self.assertEqual(len(self.checker.errors), 1)
        self.assertEqual(self.checker.errors[0]['type'], "Address Overlap")
        self.assertIn("overlaps", self.checker.errors[0]['msg'])

    def test_default_value_check(self):
        modules = [{
            'name': 'mod_def',
            'registers': [
                {'reg_name': 'ok_reg', 'width': 8, 'default_value': 0xFF}, # OK
                {'reg_name': 'bad_reg', 'width': 4, 'default_value': 0x1F} # 5 bits needed -> Error
            ]
        }]
        self.checker.check_default_values(modules)
        self.assertEqual(len(self.checker.errors), 1)
        self.assertIn("exceeds 4-bit range", self.checker.errors[0]['msg'])

    def test_naming_conventions(self):
        modules = [{
            'name': 'valid_mod',
            'registers': [
                {'reg_name': 'ValidReg', 'width': 32}, # OK
                {'reg_name': '1nvalid', 'width': 32},  # Error: starts with number
                {'reg_name': 'signal', 'width': 32},   # Error: Reserved keyword
                {'reg_name': 'bad__reg', 'width': 32}  # Warning: double underscore
            ]
        }]
        self.checker.check_naming_conventions(modules)
        
        errors = [e['msg'] for e in self.checker.errors]
        warnings = [w['msg'] for w in self.checker.warnings]
        
        self.assertTrue(any("invalid identifier" in e for e in errors))
        self.assertTrue(any("reserved keyword" in e for e in errors))
        self.assertTrue(any("double underscore" in w for w in warnings))

    def test_address_alignment(self):
        modules = [{
            'name': 'mod_align',
            'registers': [
                {'reg_name': 'aligned', 'address_int': 0x04, 'width': 32},
                {'reg_name': 'unaligned', 'address_int': 0x05, 'width': 32},
            ]
        }]
        self.checker.check_address_alignment(modules)
        self.assertEqual(len(self.checker.warnings), 1)
        self.assertIn("not 4-byte aligned", self.checker.warnings[0]['msg'])

    def test_duplicate_names(self):
        modules = [{
            'name': 'mod_dup',
            'registers': [
                {'reg_name': 'my_reg', 'width': 32},
                {'reg_name': 'my_reg', 'width': 32},
            ]
        }]
        self.checker.check_duplicate_names(modules)
        self.assertEqual(len(self.checker.errors), 1)
        self.assertIn("defined multiple times", self.checker.errors[0]['msg'])

if __name__ == '__main__':
    unittest.main()
