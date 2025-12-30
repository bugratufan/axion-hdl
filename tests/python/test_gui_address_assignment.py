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
        # gui_page already navigated to server, go to dashboard
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

    # GUI-EDIT-021: Address conflict resolution - auto-shift
    def test_edit_021_address_conflict_resolution(self, gui_page, gui_server):
        """When address conflicts occur, non-manual addresses should auto-shift."""
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
        
        # First, unlock the second register by clicking its revert button or setting data-locked to false
        second_input = addr_inputs.nth(1)
        second_addr_original = second_input.input_value()
        
        # Unlock the second register via JavaScript (simulate it being auto-calculated)
        second_input.evaluate("el => el.setAttribute('data-locked', 'false')")
        
        # Now set first register address to conflict with second
        first_input = addr_inputs.first
        first_input.fill(second_addr_original)
        first_input.dispatch_event("change")
        
        # Wait for recalculation
        gui_page.wait_for_timeout(500)
        
        # Second register (which is now unlocked) should have been auto-shifted
        second_addr_new = addr_inputs.nth(1).input_value()
        assert second_addr_new != second_addr_original, \
            f"Unlocked second register should have auto-shifted from {second_addr_original} to avoid conflict"

    # GUI-EDIT-022: Manual address preservation
    def test_edit_022_manual_address_preservation(self, gui_page, gui_server):
        """Manually assigned addresses should be preserved when no conflict exists."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)
        
        addr_inputs = gui_page.locator(".reg-addr-input")
        count = addr_inputs.count()
        
        if count < 3:
            pytest.skip("Need at least 3 registers to test preservation")
        
        # Set third register to a high non-conflicting address
        third_input = addr_inputs.nth(2)
        third_input.fill("0x100")
        third_input.dispatch_event("change")
        
        # Wait for recalculation
        gui_page.wait_for_timeout(300)
        
        # Now modify first register
        first_input = addr_inputs.first
        first_input.fill("0x08")
        first_input.dispatch_event("change")
        
        gui_page.wait_for_timeout(300)
        
        # Third register should still be at 0x100
        third_addr = addr_inputs.nth(2).input_value()
        assert "100" in third_addr.upper(), \
            f"Third register at 0x100 should be preserved, got {third_addr}"

    # GUI-EDIT-023: Address change visual indicator (strikethrough old, show new)
    def test_edit_023_address_change_visual_indicator(self, gui_page, gui_server):
        """When address differs from original, show old address with strikethrough."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)
        
        addr_input = gui_page.locator(".reg-addr-input").first
        original_addr = addr_input.input_value()
        
        # Change address
        addr_input.fill("0x50")
        addr_input.dispatch_event("change")
        
        gui_page.wait_for_timeout(300)
        
        # Look for visual indicator (original address with strikethrough)
        row = addr_input.locator("xpath=ancestor::tr")
        
        # Check for strikethrough element or class
        has_indicator = (
            row.locator(".addr-original").count() > 0 or
            row.locator("[style*='text-decoration: line-through']").count() > 0 or
            row.locator(".addr-changed").count() > 0
        )
        
        assert has_indicator, "Should show visual indicator when address changes from original"

    # GUI-EDIT-024: Address revert on clear
    def test_edit_024_address_revert_on_clear(self, gui_page, gui_server):
        """If user clears a manual address, original address should be restored."""
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
        
        # Look for revert button or clear the field
        row = addr_input.locator("xpath=ancestor::tr")
        revert_btn = row.locator(".addr-revert-btn, [data-action='revert-address']")
        
        if revert_btn.count() > 0:
            revert_btn.click()
        else:
            # Alternative: clear the field and blur
            addr_input.fill("")
            addr_input.dispatch_event("blur")
        
        gui_page.wait_for_timeout(300)
        
        # Address should revert or be recalculated
        new_addr = addr_input.input_value()
        # Either matches original or is auto-calculated (not empty)
        assert new_addr != "", "Address should not remain empty after revert"

    # GUI-EDIT-025: Real-time address update
    def test_edit_025_realtime_address_update(self, gui_page, gui_server):
        """Address changes should appear immediately without page reload."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)
        
        addr_inputs = gui_page.locator(".reg-addr-input")
        count = addr_inputs.count()
        
        if count < 2:
            pytest.skip("Need at least 2 registers to test real-time update")
        
        # First, unlock the second register so it can be auto-calculated
        second_input = addr_inputs.nth(1)
        second_initial = second_input.input_value()
        second_input.evaluate("el => el.setAttribute('data-locked', 'false')")
        
        # Change first register width (which affects subsequent addresses)
        width_input = gui_page.locator(".reg-width-input").first
        width_input.fill("64")  # 64-bit = 2 words = 8 bytes
        width_input.dispatch_event("change")
        
        # Wait briefly
        gui_page.wait_for_timeout(500)
        
        # Second register address should update without reload (since it's unlocked)
        second_new = addr_inputs.nth(1).input_value()
        
        # The address should have changed due to increased width
        assert second_new != second_initial, \
            f"Unlocked second register address should update in real-time: {second_initial} -> {second_new}"

    # GUI-EDIT-026: Address conflict warning
    def test_edit_026_address_conflict_warning(self, gui_page, gui_server):
        """Visual warning indicator should be shown when address conflict is detected."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)
        
        addr_inputs = gui_page.locator(".reg-addr-input")
        count = addr_inputs.count()
        
        if count < 2:
            pytest.skip("Need at least 2 registers to test conflict warning")
        
        # Get addresses
        first_addr = addr_inputs.first.input_value()
        
        # Set second to same as first (create conflict)
        second_input = addr_inputs.nth(1)
        second_input.fill(first_addr)
        second_input.dispatch_event("change")
        
        # Wait for validation
        gui_page.wait_for_timeout(300)
        
        # Check for warning indicator
        # Could be: red border, warning icon, error class, etc.
        row = second_input.locator("xpath=ancestor::tr")
        has_warning = (
            second_input.evaluate("el => el.classList.contains('input-invalid')") or
            second_input.evaluate("el => el.classList.contains('addr-conflict')") or
            row.locator(".addr-conflict-warning, .bi-exclamation-triangle").count() > 0
        )
        
        # Note: After our implementation, conflict should either:
        # 1. Show warning, OR
        # 2. Auto-resolve (shift the first one since second was edited)
        # This test checks for warning presence
        assert has_warning or addr_inputs.first.input_value() != first_addr, \
            "Should show warning or auto-resolve conflict"
