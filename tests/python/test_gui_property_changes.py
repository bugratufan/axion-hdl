"""
GUI Property Change Tests

Tests that module properties (base_address, cdc_enable, cdc_stages) are correctly
saved and reflected in the diff view for all file formats (VHDL, JSON, XML, YAML).

These tests are STRICT - they require that:
1. Changes produce a diff (not "no-changes")
2. The diff contains the NEW value being added
3. The diff reflects the actual change made

Run with: pytest tests/python/test_gui_property_changes.py -v
"""
import pytest
import re
from pathlib import Path

# Skip all GUI tests if playwright is not installed
pytest.importorskip("playwright")


class TestVHDLPropertyChanges:
    """Tests for property changes on VHDL modules"""
    
    def _navigate_to_vhdl_module(self, gui_page, gui_server):
        """Navigate to a VHDL module (sensor_controller)"""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_load_state("networkidle")
        
        # Find and click the sensor_controller VHDL module card
        vhdl_card = gui_page.locator(".module-card", has_text=re.compile(r"sensor_controller.*\.vhd", re.IGNORECASE))
        if vhdl_card.count() > 0:
            vhdl_card.first.click()
            gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
            gui_page.wait_for_load_state("networkidle")
            gui_page.wait_for_function("() => window.initialState !== undefined")
            return True
        return False
    
    def test_vhdl_base_address_change_in_diff(self, gui_page, gui_server):
        """VHDL: Base address change MUST appear in diff with correct value"""
        if not self._navigate_to_vhdl_module(gui_page, gui_server):
            pytest.skip("VHDL module not found")
        
        # Get original value and change it
        base_input = gui_page.locator("input[name='base_address']")
        original_value = base_input.input_value()
        new_value = "A000"  # Different from default 0000
        
        # Ensure we're actually changing the value
        if original_value.upper() == new_value.upper():
            new_value = "B000"
        
        base_input.fill(new_value)
        gui_page.wait_for_timeout(500)
        
        # Click Review & Save
        gui_page.locator("button", has_text="Review").click()
        gui_page.wait_for_url(re.compile(r"/diff"), timeout=5000)
        gui_page.wait_for_load_state("networkidle")
        
        # STRICT: We must have a diff, not "no-changes"
        has_diff = gui_page.locator(".diff-line").count() > 0
        no_changes = gui_page.locator(".no-changes").is_visible() if gui_page.locator(".no-changes").count() > 0 else False
        
        assert has_diff, f"VHDL base_address change did NOT produce a diff! Original: {original_value}, New: {new_value}. no-changes visible: {no_changes}"
        
        # Get the full diff text
        diff_text = gui_page.locator("#diff-unified").text_content() or ""
        
        # Check that the NEW value appears in the diff (as an addition)
        assert new_value.upper() in diff_text.upper(), \
            f"Diff does NOT contain the new base address value '{new_value}'! Diff content:\n{diff_text[:1000]}"
    
    def test_vhdl_cdc_enable_change_in_diff(self, gui_page, gui_server):
        """VHDL: CDC enable toggle change MUST appear in diff"""
        if not self._navigate_to_vhdl_module(gui_page, gui_server):
            pytest.skip("VHDL module not found")
        
        # Toggle CDC enable
        cdc_checkbox = gui_page.locator("#cdcEnable")
        was_checked = cdc_checkbox.is_checked()
        
        if was_checked:
            cdc_checkbox.uncheck()
        else:
            cdc_checkbox.check()
        
        gui_page.wait_for_timeout(500)
        
        # Click Review & Save
        gui_page.locator("button", has_text="Review").click()
        gui_page.wait_for_url(re.compile(r"/diff"), timeout=5000)
        gui_page.wait_for_load_state("networkidle")
        
        # STRICT: We must have a diff
        has_diff = gui_page.locator(".diff-line").count() > 0
        no_changes = gui_page.locator(".no-changes").is_visible() if gui_page.locator(".no-changes").count() > 0 else False
        
        assert has_diff, f"VHDL CDC enable change did NOT produce a diff! Was checked: {was_checked}. no-changes visible: {no_changes}"
        
        # Verify diff content mentions CDC
        diff_text = gui_page.locator("#diff-unified").text_content() or ""
        assert "cdc" in diff_text.lower(), f"Diff doesn't contain CDC change. Diff:\n{diff_text[:1000]}"
    
    def test_vhdl_cdc_stages_change_in_diff(self, gui_page, gui_server):
        """VHDL: CDC stages change MUST appear in diff with correct value"""
        if not self._navigate_to_vhdl_module(gui_page, gui_server):
            pytest.skip("VHDL module not found")
        
        # Ensure CDC is enabled first
        cdc_checkbox = gui_page.locator("#cdcEnable")
        if not cdc_checkbox.is_checked():
            cdc_checkbox.check()
            gui_page.wait_for_timeout(300)
        
        # Change CDC stages
        cdc_stages = gui_page.locator("#cdcStages")
        original_stages = cdc_stages.input_value()
        new_stages = "4" if original_stages != "4" else "2"
        
        cdc_stages.fill(new_stages)
        gui_page.wait_for_timeout(500)
        
        # Click Review & Save
        gui_page.locator("button", has_text="Review").click()
        gui_page.wait_for_url(re.compile(r"/diff"), timeout=5000)
        gui_page.wait_for_load_state("networkidle")
        
        # STRICT: We must have a diff
        has_diff = gui_page.locator(".diff-line").count() > 0
        no_changes = gui_page.locator(".no-changes").is_visible() if gui_page.locator(".no-changes").count() > 0 else False
        
        assert has_diff, f"VHDL CDC stages change did NOT produce a diff! Original: {original_stages}, New: {new_stages}. no-changes visible: {no_changes}"
        
        # Verify diff content contains the new stage value
        diff_text = gui_page.locator("#diff-unified").text_content() or ""
        assert new_stages in diff_text, \
            f"Diff doesn't contain new CDC stages value '{new_stages}'. Diff:\n{diff_text[:1000]}"


class TestXMLPropertyChanges:
    """Tests for property changes on XML modules"""
    
    def _navigate_to_xml_module(self, gui_page, gui_server):
        """Navigate to an XML module (sensor_controller from xml dir)"""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_load_state("networkidle")
        
        # Find and click an XML module card
        xml_card = gui_page.locator(".module-card", has_text=re.compile(r"\.xml", re.IGNORECASE))
        if xml_card.count() > 0:
            xml_card.first.click()
            gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
            gui_page.wait_for_load_state("networkidle")
            gui_page.wait_for_function("() => window.initialState !== undefined")
            return True
        return False
    
    def test_xml_base_address_change_in_diff(self, gui_page, gui_server):
        """XML: Base address change MUST appear in diff with correct value"""
        if not self._navigate_to_xml_module(gui_page, gui_server):
            pytest.skip("XML module not found")
        
        # Change base address
        base_input = gui_page.locator("input[name='base_address']")
        original_value = base_input.input_value()
        new_value = "B000"
        
        if original_value.upper() == new_value.upper():
            new_value = "C000"
        
        base_input.fill(new_value)
        gui_page.wait_for_timeout(500)
        
        # Click Review & Save
        gui_page.locator("button", has_text="Review").click()
        gui_page.wait_for_url(re.compile(r"/diff"), timeout=5000)
        gui_page.wait_for_load_state("networkidle")
        
        # STRICT: Must have diff
        has_diff = gui_page.locator(".diff-line").count() > 0
        no_changes = gui_page.locator(".no-changes").is_visible() if gui_page.locator(".no-changes").count() > 0 else False
        
        assert has_diff, f"XML base_address change did NOT produce a diff! Original: {original_value}, New: {new_value}. no-changes visible: {no_changes}"
        
        # Check that the NEW value appears in the diff
        diff_text = gui_page.locator("#diff-unified").text_content() or ""
        assert new_value.upper() in diff_text.upper(), \
            f"Diff does NOT contain the new base address value '{new_value}'! Diff content:\n{diff_text[:1000]}"
    
    def test_xml_cdc_enable_change_in_diff(self, gui_page, gui_server):
        """XML: CDC enable toggle change MUST appear in diff with correct value"""
        if not self._navigate_to_xml_module(gui_page, gui_server):
            pytest.skip("XML module not found")
        
        # Toggle CDC enable
        cdc_checkbox = gui_page.locator("#cdcEnable")
        was_checked = cdc_checkbox.is_checked()
        expected_new_value = "false" if was_checked else "true"
        
        if was_checked:
            cdc_checkbox.uncheck()
        else:
            cdc_checkbox.check()
        
        gui_page.wait_for_timeout(500)
        
        # Click Review & Save
        gui_page.locator("button", has_text="Review").click()
        gui_page.wait_for_url(re.compile(r"/diff"), timeout=5000)
        gui_page.wait_for_load_state("networkidle")
        
        # STRICT: Must have diff
        has_diff = gui_page.locator(".diff-line").count() > 0
        no_changes = gui_page.locator(".no-changes").is_visible() if gui_page.locator(".no-changes").count() > 0 else False
        
        assert has_diff, f"XML CDC enable change did NOT produce a diff! Was checked: {was_checked}. no-changes visible: {no_changes}"
        
        # Check diff content contains cdc_en change
        diff_text = gui_page.locator("#diff-unified").text_content() or ""
        assert "cdc" in diff_text.lower(), \
            f"Diff doesn't contain CDC change. Diff:\n{diff_text[:1000]}"
    
    def test_xml_cdc_stages_change_in_diff(self, gui_page, gui_server):
        """XML: CDC stages change MUST appear in diff with correct value"""
        if not self._navigate_to_xml_module(gui_page, gui_server):
            pytest.skip("XML module not found")
        
        # Ensure CDC is enabled
        cdc_checkbox = gui_page.locator("#cdcEnable")
        if not cdc_checkbox.is_checked():
            cdc_checkbox.check()
            gui_page.wait_for_timeout(300)
        
        # Change CDC stages
        cdc_stages = gui_page.locator("#cdcStages")
        original_stages = cdc_stages.input_value()
        new_stages = "5" if original_stages != "5" else "2"
        
        cdc_stages.fill(new_stages)
        gui_page.wait_for_timeout(500)
        
        # Click Review & Save
        gui_page.locator("button", has_text="Review").click()
        gui_page.wait_for_url(re.compile(r"/diff"), timeout=5000)
        gui_page.wait_for_load_state("networkidle")
        
        # STRICT: Must have diff
        has_diff = gui_page.locator(".diff-line").count() > 0
        no_changes = gui_page.locator(".no-changes").is_visible() if gui_page.locator(".no-changes").count() > 0 else False
        
        assert has_diff, f"XML CDC stages change did NOT produce a diff! Original: {original_stages}, New: {new_stages}. no-changes visible: {no_changes}"
        
        # Check that the new stages value appears in diff
        diff_text = gui_page.locator("#diff-unified").text_content() or ""
        assert new_stages in diff_text, \
            f"Diff doesn't contain new CDC stages value '{new_stages}'. Diff:\n{diff_text[:1000]}"


class TestYAMLPropertyChanges:
    """Tests for property changes on YAML modules"""
    
    def _navigate_to_yaml_module(self, gui_page, gui_server):
        """Navigate to a YAML module"""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_load_state("networkidle")
        
        # Find and click a YAML module card
        yaml_card = gui_page.locator(".module-card", has_text=re.compile(r"\.yaml|\.yml", re.IGNORECASE))
        if yaml_card.count() > 0:
            yaml_card.first.click()
            gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
            gui_page.wait_for_load_state("networkidle")
            gui_page.wait_for_function("() => window.initialState !== undefined")
            return True
        return False
    
    def test_yaml_base_address_change_in_diff(self, gui_page, gui_server):
        """YAML: Base address change MUST appear in diff with correct value"""
        if not self._navigate_to_yaml_module(gui_page, gui_server):
            pytest.skip("YAML module not found")
        
        # Change base address
        base_input = gui_page.locator("input[name='base_address']")
        original_value = base_input.input_value()
        new_value = "C000"
        
        if original_value.upper() == new_value.upper():
            new_value = "D000"
        
        base_input.fill(new_value)
        gui_page.wait_for_timeout(500)
        
        # Click Review & Save
        gui_page.locator("button", has_text="Review").click()
        gui_page.wait_for_url(re.compile(r"/diff"), timeout=5000)
        gui_page.wait_for_load_state("networkidle")
        
        # STRICT: Must have diff
        has_diff = gui_page.locator(".diff-line").count() > 0
        no_changes = gui_page.locator(".no-changes").is_visible() if gui_page.locator(".no-changes").count() > 0 else False
        
        assert has_diff, f"YAML base_address change did NOT produce a diff! Original: {original_value}, New: {new_value}. no-changes visible: {no_changes}"
        
        # Check that the NEW value appears in the diff
        diff_text = gui_page.locator("#diff-unified").text_content() or ""
        assert new_value.upper() in diff_text.upper(), \
            f"Diff does NOT contain the new base address value '{new_value}'! Diff content:\n{diff_text[:1000]}"
    
    def test_yaml_cdc_enable_change_in_diff(self, gui_page, gui_server):
        """YAML: CDC enable toggle change MUST appear in diff"""
        if not self._navigate_to_yaml_module(gui_page, gui_server):
            pytest.skip("YAML module not found")
        
        # Toggle CDC enable
        cdc_checkbox = gui_page.locator("#cdcEnable")
        was_checked = cdc_checkbox.is_checked()
        expected_new_value = "false" if was_checked else "true"
        
        if was_checked:
            cdc_checkbox.uncheck()
        else:
            cdc_checkbox.check()
        
        gui_page.wait_for_timeout(500)
        
        # Click Review & Save
        gui_page.locator("button", has_text="Review").click()
        gui_page.wait_for_url(re.compile(r"/diff"), timeout=5000)
        gui_page.wait_for_load_state("networkidle")
        
        # STRICT: Must have diff
        has_diff = gui_page.locator(".diff-line").count() > 0
        no_changes = gui_page.locator(".no-changes").is_visible() if gui_page.locator(".no-changes").count() > 0 else False
        
        assert has_diff, f"YAML CDC enable change did NOT produce a diff! Was checked: {was_checked}. no-changes visible: {no_changes}"
        
        # Check diff content contains cdc change
        diff_text = gui_page.locator("#diff-unified").text_content() or ""
        assert "cdc" in diff_text.lower(), \
            f"Diff doesn't contain CDC change. Diff:\n{diff_text[:1000]}"
    
    def test_yaml_cdc_stages_change_in_diff(self, gui_page, gui_server):
        """YAML: CDC stages change MUST appear in diff with correct value"""
        if not self._navigate_to_yaml_module(gui_page, gui_server):
            pytest.skip("YAML module not found")
        
        # Ensure CDC is enabled
        cdc_checkbox = gui_page.locator("#cdcEnable")
        if not cdc_checkbox.is_checked():
            cdc_checkbox.check()
            gui_page.wait_for_timeout(300)
        
        # Change CDC stages
        cdc_stages = gui_page.locator("#cdcStages")
        original_stages = cdc_stages.input_value()
        new_stages = "4" if original_stages != "4" else "3"
        
        cdc_stages.fill(new_stages)
        gui_page.wait_for_timeout(500)
        
        # Click Review & Save
        gui_page.locator("button", has_text="Review").click()
        gui_page.wait_for_url(re.compile(r"/diff"), timeout=5000)
        gui_page.wait_for_load_state("networkidle")
        
        # STRICT: Must have diff
        has_diff = gui_page.locator(".diff-line").count() > 0
        no_changes = gui_page.locator(".no-changes").is_visible() if gui_page.locator(".no-changes").count() > 0 else False
        
        assert has_diff, f"YAML CDC stages change did NOT produce a diff! Original: {original_stages}, New: {new_stages}. no-changes visible: {no_changes}"
        
        # Check that the new stages value appears in diff
        diff_text = gui_page.locator("#diff-unified").text_content() or ""
        assert new_stages in diff_text, \
            f"Diff doesn't contain new CDC stages value '{new_stages}'. Diff:\n{diff_text[:1000]}"


class TestJSONPropertyChanges:
    """Tests for property changes on JSON modules"""
    
    def _navigate_to_json_module(self, gui_page, gui_server):
        """Navigate to a JSON module"""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_load_state("networkidle")
        
        # Find and click a JSON module card
        json_card = gui_page.locator(".module-card", has_text=re.compile(r"\.json", re.IGNORECASE))
        if json_card.count() > 0:
            json_card.first.click()
            gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
            gui_page.wait_for_load_state("networkidle")
            gui_page.wait_for_function("() => window.initialState !== undefined")
            return True
        return False
    
    def test_json_base_address_change_in_diff(self, gui_page, gui_server):
        """JSON: Base address change MUST appear in diff with correct value"""
        if not self._navigate_to_json_module(gui_page, gui_server):
            pytest.skip("JSON module not found")
        
        # Change base address
        base_input = gui_page.locator("input[name='base_address']")
        original_value = base_input.input_value()
        new_value = "D000"
        
        if original_value.upper() == new_value.upper():
            new_value = "E000"
        
        base_input.fill(new_value)
        gui_page.wait_for_timeout(500)
        
        # Click Review & Save
        gui_page.locator("button", has_text="Review").click()
        gui_page.wait_for_url(re.compile(r"/diff"), timeout=5000)
        gui_page.wait_for_load_state("networkidle")
        
        # STRICT: Must have diff
        has_diff = gui_page.locator(".diff-line").count() > 0
        no_changes = gui_page.locator(".no-changes").is_visible() if gui_page.locator(".no-changes").count() > 0 else False
        
        assert has_diff, f"JSON base_address change did NOT produce a diff! Original: {original_value}, New: {new_value}. no-changes visible: {no_changes}"
        
        # Check that the NEW value appears in the diff
        diff_text = gui_page.locator("#diff-unified").text_content() or ""
        assert new_value.upper() in diff_text.upper(), \
            f"Diff does NOT contain the new base address value '{new_value}'! Diff content:\n{diff_text[:1000]}"
    
    def test_json_cdc_enable_change_in_diff(self, gui_page, gui_server):
        """JSON: CDC enable toggle change MUST appear in diff"""
        if not self._navigate_to_json_module(gui_page, gui_server):
            pytest.skip("JSON module not found")
        
        # Toggle CDC enable
        cdc_checkbox = gui_page.locator("#cdcEnable")
        was_checked = cdc_checkbox.is_checked()
        expected_new_value = "false" if was_checked else "true"
        
        if was_checked:
            cdc_checkbox.uncheck()
        else:
            cdc_checkbox.check()
        
        gui_page.wait_for_timeout(500)
        
        # Click Review & Save
        gui_page.locator("button", has_text="Review").click()
        gui_page.wait_for_url(re.compile(r"/diff"), timeout=5000)
        gui_page.wait_for_load_state("networkidle")
        
        # STRICT: Must have diff
        has_diff = gui_page.locator(".diff-line").count() > 0
        no_changes = gui_page.locator(".no-changes").is_visible() if gui_page.locator(".no-changes").count() > 0 else False
        
        assert has_diff, f"JSON CDC enable change did NOT produce a diff! Was checked: {was_checked}. no-changes visible: {no_changes}"
        
        # Check diff content
        diff_text = gui_page.locator("#diff-unified").text_content() or ""
        assert "cdc" in diff_text.lower(), \
            f"Diff doesn't contain CDC change. Diff:\n{diff_text[:1000]}"
    
    def test_json_cdc_stages_change_in_diff(self, gui_page, gui_server):
        """JSON: CDC stages change MUST appear in diff with correct value"""
        if not self._navigate_to_json_module(gui_page, gui_server):
            pytest.skip("JSON module not found")
        
        # Ensure CDC is enabled
        cdc_checkbox = gui_page.locator("#cdcEnable")
        if not cdc_checkbox.is_checked():
            cdc_checkbox.check()
            gui_page.wait_for_timeout(300)
        
        # Change CDC stages
        cdc_stages = gui_page.locator("#cdcStages")
        original_stages = cdc_stages.input_value()
        new_stages = "5" if original_stages != "5" else "2"
        
        cdc_stages.fill(new_stages)
        gui_page.wait_for_timeout(500)
        
        # Click Review & Save
        gui_page.locator("button", has_text="Review").click()
        gui_page.wait_for_url(re.compile(r"/diff"), timeout=5000)
        gui_page.wait_for_load_state("networkidle")
        
        # STRICT: Must have diff
        has_diff = gui_page.locator(".diff-line").count() > 0
        no_changes = gui_page.locator(".no-changes").is_visible() if gui_page.locator(".no-changes").count() > 0 else False
        
        assert has_diff, f"JSON CDC stages change did NOT produce a diff! Original: {original_stages}, New: {new_stages}. no-changes visible: {no_changes}"
        
        # Check that the new stages value appears in diff
        diff_text = gui_page.locator("#diff-unified").text_content() or ""
        assert new_stages in diff_text, \
            f"Diff doesn't contain new CDC stages value '{new_stages}'. Diff:\n{diff_text[:1000]}"


class TestSVPropertyChanges:
    """Tests for property changes on SystemVerilog modules"""

    def _navigate_to_sv_module(self, gui_page, gui_server):
        """Navigate to a SystemVerilog module card"""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_load_state("networkidle")

        sv_card = gui_page.locator(".module-card", has_text=re.compile(r"\.sv", re.IGNORECASE))
        if sv_card.count() > 0:
            sv_card.first.click()
            gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
            gui_page.wait_for_load_state("networkidle")
            gui_page.wait_for_function("() => window.initialState !== undefined")
            return True
        return False

    def test_sv_base_address_change_in_diff(self, gui_page, gui_server):
        """SV: Base address change MUST appear in diff with correct value"""
        if not self._navigate_to_sv_module(gui_page, gui_server):
            pytest.skip("SV module not found")

        base_input = gui_page.locator("input[name='base_address']")
        original_value = base_input.input_value()
        new_value = "C000" if original_value.upper() != "C000" else "D000"

        base_input.fill(new_value)
        gui_page.wait_for_timeout(500)

        gui_page.locator("button", has_text="Review").click()
        gui_page.wait_for_url(re.compile(r"/diff"), timeout=5000)
        gui_page.wait_for_load_state("networkidle")

        has_diff = gui_page.locator(".diff-line").count() > 0
        no_changes = gui_page.locator(".no-changes").is_visible() if gui_page.locator(".no-changes").count() > 0 else False

        assert has_diff, f"SV base_address change did NOT produce a diff! Original: {original_value}, New: {new_value}. no-changes visible: {no_changes}"

        diff_text = gui_page.locator("#diff-unified").text_content() or ""
        assert new_value.upper() in diff_text.upper(), \
            f"Diff does NOT contain new base address '{new_value}':\n{diff_text[:1000]}"

        # SV files must NOT use -- style comments in diff
        assert "-- @axion_def" not in diff_text, \
            f"Diff contains VHDL-style '-- @axion_def' in an SV file:\n{diff_text[:1000]}"

    def test_sv_cdc_enable_change_in_diff(self, gui_page, gui_server):
        """SV: CDC enable toggle change MUST appear in diff using // comment style"""
        if not self._navigate_to_sv_module(gui_page, gui_server):
            pytest.skip("SV module not found")

        cdc_checkbox = gui_page.locator("#cdcEnable")
        was_checked = cdc_checkbox.is_checked()

        if was_checked:
            cdc_checkbox.uncheck()
        else:
            cdc_checkbox.check()

        gui_page.wait_for_timeout(500)

        gui_page.locator("button", has_text="Review").click()
        gui_page.wait_for_url(re.compile(r"/diff"), timeout=5000)
        gui_page.wait_for_load_state("networkidle")

        has_diff = gui_page.locator(".diff-line").count() > 0
        no_changes = gui_page.locator(".no-changes").is_visible() if gui_page.locator(".no-changes").count() > 0 else False

        assert has_diff, f"SV CDC enable change did NOT produce a diff! Was checked: {was_checked}. no-changes visible: {no_changes}"

        diff_text = gui_page.locator("#diff-unified").text_content() or ""
        assert "cdc" in diff_text.lower(), f"Diff doesn't mention CDC:\n{diff_text[:1000]}"
        assert "-- @axion_def" not in diff_text, \
            "Diff uses VHDL '-- @axion_def' style in SV file"

    def test_sv_cdc_stages_change_in_diff(self, gui_page, gui_server):
        """SV: CDC stages change MUST appear in diff with correct value"""
        if not self._navigate_to_sv_module(gui_page, gui_server):
            pytest.skip("SV module not found")

        cdc_checkbox = gui_page.locator("#cdcEnable")
        if not cdc_checkbox.is_checked():
            cdc_checkbox.check()
            gui_page.wait_for_timeout(300)

        cdc_stages = gui_page.locator("#cdcStages")
        original_stages = cdc_stages.input_value()
        new_stages = "4" if original_stages != "4" else "3"

        cdc_stages.fill(new_stages)
        gui_page.wait_for_timeout(500)

        gui_page.locator("button", has_text="Review").click()
        gui_page.wait_for_url(re.compile(r"/diff"), timeout=5000)
        gui_page.wait_for_load_state("networkidle")

        has_diff = gui_page.locator(".diff-line").count() > 0
        assert has_diff, f"SV CDC stages change did NOT produce a diff! Original: {original_stages}, New: {new_stages}"

        diff_text = gui_page.locator("#diff-unified").text_content() or ""
        assert new_stages in diff_text, \
            f"Diff doesn't contain new CDC stages value '{new_stages}':\n{diff_text[:1000]}"

    def test_sv_dashboard_shows_sv_module(self, gui_page, gui_server):
        """Dashboard must show at least one SV module card"""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_load_state("networkidle")

        sv_card = gui_page.locator(".module-card", has_text=re.compile(r"\.sv", re.IGNORECASE))
        assert sv_card.count() > 0, \
            "No SV module card found on dashboard — SV sources may not be loaded in test server"

    def test_sv_generate_toggle_exists(self, gui_page, gui_server):
        """Generate page must have a SystemVerilog output toggle"""
        gui_page.goto(gui_server.url + "/generate")
        gui_page.wait_for_load_state("networkidle")

        sv_checkbox = gui_page.locator("#fmtSystemVerilog")
        assert sv_checkbox.count() > 0, "No #fmtSystemVerilog checkbox found on generate page"
        assert sv_checkbox.is_visible(), "SystemVerilog checkbox not visible on generate page"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
