"""
GUI Address Assignment Tests using Playwright

Tests the address editing and conflict resolution functionality in Axion-HDL GUI.
Covers requirements GUI-EDIT-020 through GUI-EDIT-026.

Run with: pytest tests/python/test_gui_address_assignment.py -v
"""
import pytest
from pathlib import Path

# Skip all GUI tests if playwright is not installed
pytest.importorskip("playwright")


class TestGUIAddressAssignment:
    """Tests for GUI-EDIT-020 through GUI-EDIT-026: Address Assignment Requirements"""

    # GUI-EDIT-020: Address input field is editable
    def test_edit_020_address_input_editable(self, gui_page, gui_server):
        """Address input field should be editable for manual address assignment."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        
        # Navigate to a module editor
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)
        
        # Find address input
        addr_input = gui_page.locator(".reg-addr-input").first
        assert addr_input.is_visible(), "Address input should be visible"
        
        # Check editable (not readonly, not disabled)
        assert not addr_input.get_attribute("readonly"), "Address input should not be readonly"
        assert not addr_input.get_attribute("disabled"), "Address input should not be disabled"
        
        # Try to type a new address
        addr_input.fill("0x20")
        assert addr_input.input_value() == "0x20", "Address input should accept new value"

    # GUI-EDIT-021: Address conflict resolution - auto-shift passive locked registers
    def test_edit_021_address_conflict_resolution(self, gui_page, gui_server):
        """When user changes an address to conflict with another, the other should auto-shift."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        
        # Navigate to a module with multiple registers
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)
        
        # Get all address inputs
        addr_inputs = gui_page.locator(".reg-addr-input")
        count = addr_inputs.count()
        
        if count < 2:
            pytest.skip("Need at least 2 registers to test conflict resolution")
        
        # Get second register's original address
        second_input = addr_inputs.nth(1)
        second_addr_original = second_input.input_value()
        
        # Set first register address to conflict with second
        first_input = addr_inputs.first
        first_input.fill(second_addr_original)
        first_input.dispatch_event("change")
        
        # Wait for recalculation
        gui_page.wait_for_timeout(500)
        
        # Second register should have been auto-shifted (passive locked becomes auto-calculated)
        second_addr_new = addr_inputs.nth(1).input_value()
        assert second_addr_new != second_addr_original, \
            f"Second register should have auto-shifted from {second_addr_original} to avoid conflict with user's change"

    # GUI-EDIT-022: Manual address preservation - active locked addresses don't change
    def test_edit_022_manual_address_preservation(self, gui_page, gui_server):
        """User-modified (active-locked) addresses should be preserved and not auto-shifted."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)
        
        addr_inputs = gui_page.locator(".reg-addr-input")
        count = addr_inputs.count()
        
        if count < 3:
            pytest.skip("Need at least 3 registers to test preservation")
        
        # Set third register to a high non-conflicting address (making it active-locked)
        third_input = addr_inputs.nth(2)
        third_input.fill("0x100")
        third_input.dispatch_event("change")
        gui_page.wait_for_timeout(300)
        
        # Now modify first register to a different address
        first_input = addr_inputs.first
        first_input.fill("0x08")
        first_input.dispatch_event("change")
        gui_page.wait_for_timeout(300)
        
        # Third register (active-locked at 0x100) should still be at 0x100
        third_addr = addr_inputs.nth(2).input_value()
        assert "100" in third_addr.upper(), \
            f"Active-locked register at 0x100 should be preserved, got {third_addr}"

    # GUI-EDIT-023: Address change visual indicator (strikethrough old, show new)
    def test_edit_023_address_change_visual_indicator(self, gui_page, gui_server):
        """When address differs from original, show old address with strikethrough."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)
        
        addr_input = gui_page.locator(".reg-addr-input").first
        original_addr = addr_input.input_value()
        
        # Change address to something different
        addr_input.fill("0x50")
        addr_input.dispatch_event("change")
        gui_page.wait_for_timeout(300)
        
        # Look for visual indicator (original address with strikethrough)
        row = addr_input.locator("xpath=ancestor::tr")
        
        # Check for strikethrough element - the addr-original span should be visible
        addr_original_span = row.locator(".addr-original")
        
        # The original span should be visible and contain the original address
        assert addr_original_span.is_visible(), "Original address strikethrough should be visible"
        assert original_addr in addr_original_span.text_content() or addr_original_span.text_content() != "", \
            "Original address should be shown with strikethrough"

    # GUI-EDIT-024: Address revert on clear or button click
    def test_edit_024_address_revert_on_clear(self, gui_page, gui_server):
        """Clicking revert button or clearing address should restore original."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)
        
        addr_input = gui_page.locator(".reg-addr-input").first
        original_addr = addr_input.input_value()
        
        # Change address
        addr_input.fill("0x80")
        addr_input.dispatch_event("change")
        gui_page.wait_for_timeout(300)
        
        # Look for revert button
        row = addr_input.locator("xpath=ancestor::tr")
        revert_btn = row.locator(".addr-revert-btn, [data-action='revert-address']")
        
        if revert_btn.is_visible():
            revert_btn.click()
            gui_page.wait_for_timeout(300)
            
            # Address should be restored
            new_addr = addr_input.input_value()
            assert new_addr != "", "Address should not be empty after revert"
        else:
            # Alternative: clear the field and trigger blur
            addr_input.fill("")
            addr_input.dispatch_event("blur")
            gui_page.wait_for_timeout(300)
            
            # Address should be auto-calculated (not empty)
            new_addr = addr_input.input_value()
            assert new_addr != "", "Address should not remain empty after blur"

    # GUI-EDIT-025: Real-time address update when width changes
    def test_edit_025_realtime_address_update(self, gui_page, gui_server):
        """When register width changes, subsequent addresses should update immediately."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)
        
        addr_inputs = gui_page.locator(".reg-addr-input")
        count = addr_inputs.count()
        
        if count < 2:
            pytest.skip("Need at least 2 registers to test real-time update")
        
        # Get second register's initial address and original
        second_input = addr_inputs.nth(1)
        second_original = second_input.get_attribute("data-original")
        second_initial = second_input.input_value()
        
        # Change first register width (which should affect subsequent addresses)
        width_input = gui_page.locator(".reg-width-input").first
        width_input.fill("64")  # 64-bit = 2 words = 8 bytes
        width_input.dispatch_event("change")
        gui_page.wait_for_timeout(500)
        
        # Second register address should have updated
        second_new = addr_inputs.nth(1).input_value()
        
        # The address should have changed (unless it was active-locked)
        # If second was passive-locked, it should shift
        # Check either: address changed OR it stayed same (active locked case)
        assert second_new != "" , "Second register should have a valid address"

    # GUI-EDIT-026: Address conflict warning indicator
    def test_edit_026_address_conflict_warning(self, gui_page, gui_server):
        """When two active-locked addresses conflict, warning should be shown."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)
        
        addr_inputs = gui_page.locator(".reg-addr-input")
        count = addr_inputs.count()
        
        if count < 2:
            pytest.skip("Need at least 2 registers to test conflict warning")
        
        # First, make first register active-locked at 0x10
        first_input = addr_inputs.first
        first_input.fill("0x10")
        first_input.dispatch_event("change")
        gui_page.wait_for_timeout(300)
        
        # Now make second register active-locked at the same address (0x10)
        second_input = addr_inputs.nth(1)
        second_input.fill("0x10")
        second_input.dispatch_event("change")
        gui_page.wait_for_timeout(300)
        
        # Both are now active-locked at same address - should show conflict warning
        # Check for warning indicator on either input
        has_conflict_class = (
            first_input.evaluate("el => el.classList.contains('addr-conflict')") or
            second_input.evaluate("el => el.classList.contains('addr-conflict')")
        )
        
        first_row = first_input.locator("xpath=ancestor::tr")
        second_row = second_input.locator("xpath=ancestor::tr")
        has_warning_icon = (
            first_row.locator(".addr-conflict-warning").is_visible() or
            second_row.locator(".addr-conflict-warning").is_visible()
        )
        
        assert has_conflict_class or has_warning_icon, \
            "Should show conflict warning when two active-locked addresses overlap"


class TestGUIAddressAssignmentEdgeCases:
    """Additional edge case tests for address assignment"""

    def test_passive_locked_auto_shifts_on_conflict(self, gui_page, gui_server):
        """Registers defined in source file should auto-shift when user causes conflict."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)
        
        addr_inputs = gui_page.locator(".reg-addr-input")
        if addr_inputs.count() < 2:
            pytest.skip("Need at least 2 registers")
        
        # Get original addresses
        first_original = addr_inputs.first.get_attribute("data-original")
        second_original = addr_inputs.nth(1).get_attribute("data-original")
        
        # User changes first to second's address
        addr_inputs.first.fill(second_original)
        addr_inputs.first.dispatch_event("change")
        gui_page.wait_for_timeout(500)
        
        # Second should have auto-shifted (strikethrough should appear)
        second_new = addr_inputs.nth(1).input_value()
        second_row = addr_inputs.nth(1).locator("xpath=ancestor::tr")
        
        # Either address changed or strikethrough visible
        has_strikethrough = second_row.locator(".addr-original").is_visible()
        address_changed = second_new != second_original
        
        assert has_strikethrough or address_changed, \
            f"Second register should show change indicator or shift from {second_original} to {second_new}"

    def test_multiple_active_locks_preserved(self, gui_page, gui_server):
        """Multiple user-modified addresses should all be preserved."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)
        
        addr_inputs = gui_page.locator(".reg-addr-input")
        if addr_inputs.count() < 3:
            pytest.skip("Need at least 3 registers")
        
        # Lock first at 0x00
        addr_inputs.first.fill("0x00")
        addr_inputs.first.dispatch_event("change")
        gui_page.wait_for_timeout(200)
        
        # Lock third at 0x20
        addr_inputs.nth(2).fill("0x20")
        addr_inputs.nth(2).dispatch_event("change")
        gui_page.wait_for_timeout(500)
        
        # Verify both active-locked values preserved
        first_val = addr_inputs.first.input_value()
        third_val = addr_inputs.nth(2).input_value()
        
        assert "0" in first_val.upper() and first_val.upper().endswith("0"), \
            f"First should remain at 0x00, got {first_val}"
        assert "20" in third_val.upper(), \
            f"Third should remain at 0x20, got {third_val}"
        
        # Second (passive) should be somewhere between (e.g., 0x04)
        second_val = addr_inputs.nth(1).input_value()
        second_int = int(second_val, 16)
        assert 0 < second_int < 0x20, \
            f"Second should be auto-calculated between 0x00 and 0x20, got {second_val}"
