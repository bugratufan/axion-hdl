/**
 * Axion-HDL GUI - Editor Module
 * Register map editor logic
 */

// ===== GLOBAL STATE =====
let nextAddr = 0;
let hasUnsavedChanges = false;
// Note: window.initialState is used globally for test synchronization

/**
 * Get current form state for comparison
 * @returns {string} JSON string of current state
 */
function getFormState() {
    try {
        const regs = [];
        document.querySelectorAll('.reg-row').forEach((row, index) => {
            const isPacked = row.querySelector('.toggle-subregs') !== null;
            const nameInput = row.querySelector('.reg-name-input');
            const name = nameInput?.value || '';
            const addr = row.querySelector('.reg-addr-input')?.value || '0x0';

            if (isPacked) {
                // Collect sub-fields instead of the container
                const subregRow = document.getElementById('subregs-' + row.getAttribute('data-index'));
                if (subregRow) {
                    subregRow.querySelectorAll('.subreg-field-row').forEach(fieldRow => {
                        regs.push({
                            name: fieldRow.querySelector('.subreg-name-input')?.value || '',
                            reg_name: name,
                            address: addr,
                            width: fieldRow.querySelector('.subreg-width-input')?.value || '',
                            access: fieldRow.querySelector('.subreg-access-input')?.value || '',
                            default_value: fieldRow.querySelector('.subreg-default-input')?.value || '',
                            description: fieldRow.querySelector('.subreg-desc-input')?.value || '',
                            bit_offset: fieldRow.querySelector('.subreg-offset-input')?.value || null,
                            is_packed_field: true
                        });
                    });
                }
            } else {
                // Standard register
                const strobes = row.querySelectorAll('.strobe-toggle');
                regs.push({
                    name: name,
                    width: row.querySelector('.reg-width-input')?.value || '',
                    access: row.querySelector('.reg-access-input')?.value || '',
                    default_value: row.querySelector('.reg-default-input')?.value || '',
                    description: row.querySelector('.reg-desc-input')?.value || '',
                    r_strobe: strobes[0]?.classList.contains('active') || false,
                    w_strobe: strobes[1]?.classList.contains('active') || false,
                    address: addr,
                    manual_address: row.querySelector('.reg-addr-input').getAttribute('data-locked') === 'true'
                });
            }
        });

        return JSON.stringify({
            base_address: document.querySelector('input[name="base_address"]')?.value || '',
            cdc_enabled: document.getElementById('cdcEnable')?.checked || false,
            cdc_stages: document.getElementById('cdcStages')?.value || '',
            registers: regs
        });
    } catch (e) {
        console.error("getFormState error:", e);
        return JSON.stringify({ registers: [] });
    }
}

/**
 * Get register address helper
 * @param {HTMLElement} row - Register row element
 * @returns {string} Address value
 */
function getRegAddress(row) {
    return row.querySelector('.reg-addr-input')?.value || '0x0';
}

/**
 * Mark form as changed
 */
function markAsChanged() {
    if (window.initialState && getFormState() !== window.initialState) {
        hasUnsavedChanges = true;
        document.getElementById('unsavedIndicator')?.classList.add('visible');
    } else {
        hasUnsavedChanges = false;
        document.getElementById('unsavedIndicator')?.classList.remove('visible');
    }
}

/**
 * Clear unsaved changes state
 */
function clearUnsavedChanges() {
    hasUnsavedChanges = false;
    document.getElementById('unsavedIndicator')?.classList.remove('visible');
}

/**
 * Handle address change
 * @param {HTMLInputElement} input - Address input element
 */
function onAddressChange(input) {
    input.setAttribute('data-locked', 'true');
    input.title = "Manual Address";
    validateHex(input);

    updateAddressVisualIndicator(input);
    recalculateAddresses();
    detectAddressConflicts();
    markAsChanged();
}

/**
 * Handle address blur
 * @param {HTMLInputElement} input - Address input element
 */
function onAddressBlur(input) {
    if (input.value.trim() === '') {
        revertAddress(input.closest('.addr-changed').querySelector('.addr-revert-btn'));
    }
}

/**
 * Normalize hex address for comparison
 * @param {string} addr - Address string
 * @returns {string} Normalized address
 */
function normalizeHexAddress(addr) {
    if (!addr) return '';
    const val = parseInt(addr, 16);
    if (isNaN(val)) return addr.toUpperCase();
    return '0x' + val.toString(16).toUpperCase();
}

/**
 * Update address visual indicator
 * @param {HTMLInputElement} input - Address input element
 */
function updateAddressVisualIndicator(input) {
    const container = input.closest('.addr-changed');
    if (!container) return;

    const originalSpan = container.querySelector('.addr-original');
    const revertBtn = container.querySelector('.addr-revert-btn');
    const originalValue = input.getAttribute('data-original');
    const currentValue = input.value;

    const normalizedOriginal = normalizeHexAddress(originalValue);
    const normalizedCurrent = normalizeHexAddress(currentValue);

    if (normalizedOriginal && normalizedCurrent !== normalizedOriginal) {
        originalSpan.textContent = originalValue;
        originalSpan.style.display = 'inline';
        if (revertBtn) revertBtn.style.display = 'inline-block';
    } else {
        originalSpan.style.display = 'none';
        if (revertBtn) revertBtn.style.display = 'none';
    }
}

/**
 * Revert address to original
 * @param {HTMLButtonElement} btn - Revert button
 */
function revertAddress(btn) {
    if (!btn) return;
    const container = btn.closest('.addr-changed');
    if (!container) return;

    const input = container.querySelector('.reg-addr-input');
    const originalValue = input.getAttribute('data-original');

    if (originalValue) {
        input.value = originalValue;
    }

    input.setAttribute('data-locked', 'false');
    input.title = "Auto-calculated";
    input.classList.remove('addr-conflict');

    const originalSpan = container.querySelector('.addr-original');
    const warningSpan = container.querySelector('.addr-conflict-warning');
    if (originalSpan) originalSpan.style.display = 'none';
    if (warningSpan) warningSpan.style.display = 'none';
    btn.style.display = 'none';

    recalculateAddresses();
    detectAddressConflicts();
    markAsChanged();
}

/**
 * Detect address conflicts
 * @returns {boolean} True if conflicts exist
 */
function detectAddressConflicts() {
    const addressMap = new Map();
    const inputs = document.querySelectorAll('.reg-addr-input');
    let hasConflicts = false;

    inputs.forEach((input, index) => {
        const addr = input.value.toUpperCase();
        if (!addressMap.has(addr)) {
            addressMap.set(addr, []);
        }
        addressMap.set(addr, [...addressMap.get(addr), { input, index }]);
    });

    inputs.forEach(input => {
        const container = input.closest('.addr-changed');
        const warningSpan = container?.querySelector('.addr-conflict-warning');
        const addr = input.value.toUpperCase();
        const conflicts = addressMap.get(addr);

        if (conflicts && conflicts.length > 1) {
            input.classList.add('addr-conflict');
            if (warningSpan) warningSpan.style.display = 'inline';
            hasConflicts = true;
        } else {
            input.classList.remove('addr-conflict');
            if (warningSpan) warningSpan.style.display = 'none';
        }
    });

    updateSaveButtonState(hasConflicts);
    return hasConflicts;
}

/**
 * Update save button state based on conflicts
 * @param {boolean} hasConflicts - Whether conflicts exist
 */
function updateSaveButtonState(hasConflicts) {
    const saveBtn = document.getElementById('saveBtn');
    const conflictWarning = document.getElementById('conflictWarning');

    if (hasConflicts) {
        saveBtn.disabled = true;
        saveBtn.classList.remove('btn-primary');
        saveBtn.classList.add('btn-secondary');
        saveBtn.title = 'Cannot save: Address conflicts must be resolved first';
        if (conflictWarning) conflictWarning.classList.remove('d-none');
    } else {
        saveBtn.disabled = false;
        saveBtn.classList.remove('btn-secondary');
        saveBtn.classList.add('btn-primary');
        saveBtn.title = 'Review and save changes';
        if (conflictWarning) conflictWarning.classList.add('d-none');
    }
}

/**
 * Toggle CDC enable
 */
function toggleCDC() {
    const enabled = document.getElementById('cdcEnable').checked;
    const settings = document.getElementById('cdcSettings');
    const label = document.querySelector('label[for="cdcEnable"]');

    settings.style.display = enabled ? 'block' : 'none';
    if (label) {
        label.textContent = enabled ? 'Enabled' : 'Disabled';
    }
    markAsChanged();
}

/**
 * Update access mode color
 * @param {HTMLSelectElement} select - Access select element
 */
function updateAccessColor(select) {
    const isSubreg = select.classList.contains('subreg-access-input');
    const baseClass = isSubreg ? 'subreg-access-input' : 'reg-access-input';

    select.className = `form-select form-select-sm ${baseClass} fw-bold border-0 bg-light-subtle`;
    if (select.value === 'RW') select.classList.add('text-primary');
    else if (select.value === 'RO') select.classList.add('text-success');
    else if (select.value === 'WO') select.classList.add('text-danger');
}

/**
 * Toggle subregisters visibility
 * @param {HTMLElement} btn - Toggle button
 * @param {string} index - Register index
 */
function toggleSubregisters(btn, index) {
    const row = document.getElementById('subregs-' + index);
    if (row) {
        if (row.style.display === 'none') {
            row.style.display = 'table-row';
            btn.classList.add('expanded');
        } else {
            row.style.display = 'none';
            btn.classList.remove('expanded');
        }
    }
}

/**
 * Update parent default value from subregisters
 * @param {HTMLInputElement} subInput - Subregister input
 */
function updateParentDefault(subInput) {
    const subregRow = subInput.closest('.subreg-details');
    if (!subregRow) return;

    const index = subregRow.id.replace('subregs-', '');
    const parentRow = document.querySelector(`.reg-row[data-index="${index}"]`);
    if (!parentRow) return;

    let totalValue = 0n;

    subregRow.querySelectorAll('.subreg-field-row').forEach(row => {
        const defaultInput = row.querySelector('.subreg-default-input');
        const offsetInput = row.querySelector('.subreg-offset-input');

        let valStr = defaultInput.value.trim();
        if (valStr.toLowerCase().startsWith('0x')) valStr = valStr.substring(2);
        let val = 0n;
        try {
            if (valStr) val = BigInt('0x' + valStr);
        } catch (e) { }

        const lowBit = parseInt(offsetInput?.value || '0');
        totalValue |= (val << BigInt(lowBit));
    });

    const parentInput = parentRow.querySelector('.reg-default-input');
    if (parentInput) {
        parentInput.value = '0x' + totalValue.toString(16).toUpperCase();
        markAsChanged();
    }
}

/**
 * Update subregisters from parent default value
 * @param {HTMLInputElement} input - Parent input
 * @param {string} index - Register index
 */
function updateSubregsFromParent(input, index) {
    const subregRow = document.getElementById('subregs-' + index);
    if (!subregRow) return;

    let valStr = input.value.trim();
    if (valStr.toLowerCase().startsWith('0x')) valStr = valStr.substring(2);
    let parentVal = 0n;
    try {
        if (valStr) parentVal = BigInt('0x' + valStr);
    } catch (e) { }

    subregRow.querySelectorAll('.subreg-field-row').forEach(row => {
        const defaultInput = row.querySelector('.subreg-default-input');
        const offsetInput = row.querySelector('.subreg-offset-input');
        const widthInput = row.querySelector('.subreg-width-input');

        const lowBit = parseInt(offsetInput?.value || '0');
        const width = parseInt(widthInput.value || '1');
        const mask = (1n << BigInt(width)) - 1n;
        const fieldVal = (parentVal >> BigInt(lowBit)) & mask;

        defaultInput.value = '0x' + fieldVal.toString(16).toUpperCase();
    });
    markAsChanged();
}

/**
 * Toggle strobe
 * @param {HTMLElement} elem - Strobe element
 * @param {string} type - Strobe type (r/w)
 */
function toggleStrobe(elem, type) {
    const isActive = elem.classList.contains('active');
    elem.classList.remove('active', 'inactive');
    elem.classList.add(isActive ? 'inactive' : 'active');
    markAsChanged();
}

/**
 * Recalculate addresses
 */
function recalculateAddresses() {
    const rows = [...document.querySelectorAll('.reg-row')];
    if (rows.length === 0) return;

    rows.forEach((row, idx) => {
        const input = row.querySelector('.reg-addr-input');
        if (input) {
            updateAddressVisualIndicator(input);
        }
    });

    detectAddressConflicts();
}

/**
 * Add new register
 */
function addRegister() {
    try {
        const emptyState = document.getElementById('emptyState');
        if (emptyState) emptyState.remove();

        const tbody = document.getElementById('regsBody');
        const row = document.createElement('tr');
        // SMART ADDRESS CALCULATION
        let newAddrInt = 0;
        const rows = document.querySelectorAll('.reg-row');
        if (rows.length > 0) {
            const lastRow = rows[rows.length - 1];

            // Get last address
            const lastAddrInput = lastRow.querySelector('.reg-addr-input');
            let lastAddr = 0;
            if (lastAddrInput) {
                lastAddr = parseHex(lastAddrInput.value);
            }

            // Get last width
            let lastWidth = 32; // Default to 32 if can't determine

            // Check if packed
            const isPacked = lastRow.querySelector('.toggle-subregs') !== null;
            if (isPacked) {
                // For packed, we assume 32-bit aligned chunks. 
                // To be safe and simple, we assume specific width if we can calculate it, 
                // but usually packed registers are 32-bit.
                // However, let's try to sum up fields or check valid width?
                // Actually, packed registers in this GUI don't have a main width input visible usually,
                // but one might exist on the object model. 
                // The DOM for packed row:
                // <input type="number" ... class="reg-width-input" ...> might be hidden or not present?
                // Looking at template: {% if not reg.is_packed %}... reg-width-input ... {% endif %}
                // So packed registers don't have a width input in the row immediately.
                // We'll assume 32 bit for packed registers for now as they are typically 32-bit CSRs.
                // If the user wants 64-bit packed, they usually add two 32-bit regs? 
                // Or maybe we should check if there are fields going beyond 32?
                // Let's stick effectively to 32 for packed for now, or just look at the last address 
                // and add 4.
                lastWidth = 32;
            } else {
                const widthInput = lastRow.querySelector('.reg-width-input');
                if (widthInput) {
                    lastWidth = parseInt(widthInput.value) || 32;
                }
            }

            // Calculate offset: Round up to nearest 32-bit word, then multiply by 4 bytes
            // e.g. 1-32 bits -> 1 word -> 4 bytes
            //      33-64 bits -> 2 words -> 8 bytes
            const bytesStrided = Math.ceil(lastWidth / 32) * 4;

            newAddrInt = lastAddr + bytesStrided;
        }

        const newAddr = '0x' + newAddrInt.toString(16).toUpperCase().padStart(4, '0');
        row.className = 'reg-row border-bottom-0 animate__animated animate__fadeIn';
        row.innerHTML = `
            <td class="ps-4 addr-cell">
                <div class="addr-changed">
                    <span class="addr-original" style="display: none;"></span>
                    <input type="text"
                        class="form-control form-control-sm font-monospace reg-addr-input border-0 bg-transparent p-0"
                        value="${newAddr}"
                        style="width: 70px;"
                        data-locked="false"
                        data-original="${newAddr}"
                        title="Auto-calculated"
                        onchange="onAddressChange(this)"
                        onblur="onAddressBlur(this)">
                    <button class="addr-revert-btn" style="display: none;" onclick="revertAddress(this)" data-action="revert-address" title="Revert to original">
                        <i class="bi bi-arrow-counterclockwise"></i>
                    </button>
                    <span class="addr-conflict-warning" style="display: none;"><i class="bi bi-exclamation-triangle"></i></span>
                </div>
            </td>
        <td>
            <input type="text" placeholder="new_reg" class="form-control font-monospace reg-name-input fw-bold bg-light-subtle border-0" oninput="validateName(this)">
        </td>
        <td>
            <div class="input-group input-group-sm">
                <input type="number" value="32" class="form-control reg-width-input border-0 bg-light-subtle" min="1" max="1024" style="width: 50px;" onchange="recalculateAddresses()">
            </div>
        </td>
        <td>
            <select class="form-select form-select-sm reg-access-input fw-bold border-0 bg-light-subtle text-primary" onchange="updateAccessColor(this)">
                <option value="RW" class="text-primary">RW</option>
                <option value="RO" class="text-success">RO</option>
                <option value="WO" class="text-danger">WO</option>
            </select>
        </td>
        <td>
            <input type="text" value="0x0" class="form-control form-control-sm font-monospace reg-default-input border-0 bg-light-subtle text-secondary" style="width: 70px;" oninput="validateHex(this)">
        </td>
        <td>
            <div class="strobe-group">
                <span class="strobe-toggle inactive" onclick="toggleStrobe(this, 'r')" data-tooltip="Read Strobe">R</span>
                <span class="strobe-toggle inactive" onclick="toggleStrobe(this, 'w')" data-tooltip="Write Strobe">W</span>
            </div>
        </td>
        <td>
            <input type="text" placeholder="Description" class="form-control form-control-sm reg-desc-input border-0 bg-transparent">
        </td>
        <td class="pe-4 text-end">
            <button onclick="duplicateRow(this)" class="action-btn btn btn-outline-primary btn-sm border-0 bg-primary-subtle text-primary me-1" title="Duplicate" data-tooltip="Duplicate">
                <i class="bi bi-copy"></i>
            </button>
            <button onclick="deleteRow(this)" class="action-btn btn btn-outline-danger btn-sm border-0 bg-danger-subtle text-danger" title="Delete" data-tooltip="Delete">
                <i class="bi bi-trash-fill"></i>
            </button>
        </td>
    `;
        tbody.appendChild(row);
        recalculateAddresses();

        const nameInput = row.querySelector('.reg-name-input');
        if (nameInput) {
            nameInput.focus();
            setTimeout(() => nameInput.removeAttribute('readonly'), 0);
        }

        markAsChanged();
    } catch (e) {
        console.error("addRegister error:", e);
    }
}

/**
 * Duplicate register row
 * @param {HTMLButtonElement} btn - Duplicate button
 */
function duplicateRow(btn) {
    const row = btn.closest('tr');
    const newRow = row.cloneNode(true);
    newRow.classList.add('animate__animated', 'animate__fadeIn');

    const nameInput = newRow.querySelector('.reg-name-input');
    nameInput.value = nameInput.value + '_copy';

    row.parentNode.insertBefore(newRow, row.nextSibling);
    recalculateAddresses();
    markAsChanged();
}

/**
 * Delete register row
 * @param {HTMLButtonElement} btn - Delete button
 */
function deleteRow(btn) {
    if (confirm('Are you sure you want to delete this register?')) {
        const row = btn.closest('tr');
        row.classList.add('animate__animated', 'animate__fadeOutRight');
        setTimeout(() => {
            row.remove();
            recalculateAddresses();
            markAsChanged();
        }, 300);
    }
}

/**
 * Save changes
 */
function saveChanges() {
    clearUnsavedChanges();

    const isNew = typeof moduleIsNew !== 'undefined' ? moduleIsNew : false;
    const cdcEnabled = document.getElementById('cdcEnable').checked;
    const cdcStages = document.getElementById('cdcStages').value;
    const baseAddress = document.querySelector('input[name="base_address"]').value;
    const moduleName = isNew ? document.getElementById('moduleName').value : moduleNameGlobal;

    const regs = [];
    document.querySelectorAll('.reg-row').forEach(row => {
        const isPacked = row.querySelector('.toggle-subregs') !== null;
        const name = row.querySelector('.reg-name-input')?.value || '';
        const addr = row.querySelector('.reg-addr-input')?.value || '0x0';
        const manualAddr = row.querySelector('.reg-addr-input')?.getAttribute('data-locked') === 'true';

        if (isPacked) {
            const subregRow = document.getElementById('subregs-' + row.getAttribute('data-index'));
            if (subregRow) {
                subregRow.querySelectorAll('.subreg-field-row').forEach(fieldRow => {
                    regs.push({
                        name: fieldRow.querySelector('.subreg-name-input')?.value || '',
                        reg_name: name,
                        address: addr,
                        width: fieldRow.querySelector('.subreg-width-input')?.value || '',
                        access: fieldRow.querySelector('.subreg-access-input')?.value || '',
                        default_value: fieldRow.querySelector('.subreg-default-input')?.value || '',
                        description: fieldRow.querySelector('.subreg-desc-input')?.value || '',
                        bit_offset: fieldRow.querySelector('.subreg-offset-input')?.value || null,
                        is_packed_field: true,
                        manual_address: manualAddr
                    });
                });
            }
        } else {
            const strobes = row.querySelectorAll('.strobe-toggle');
            regs.push({
                name: name,
                width: row.querySelector('.reg-width-input')?.value || '',
                access: row.querySelector('.reg-access-input')?.value || '',
                default_value: row.querySelector('.reg-default-input')?.value || '',
                description: row.querySelector('.reg-desc-input')?.value || '',
                r_strobe: strobes[0]?.classList.contains('active') || false,
                w_strobe: strobes[1]?.classList.contains('active') || false,
                address: addr,
                manual_address: manualAddr
            });
        }
    });

    if (isNew) {
        const modal = new bootstrap.Modal(document.getElementById('saveFileModal'));
        document.getElementById('saveFilePath').value = moduleName + '.yaml';
        document.getElementById('saveFormat').value = 'yaml';
        modal.show();

        window._pendingSave = {
            moduleName: moduleName,
            regs: regs,
            properties: {
                cdc_enabled: cdcEnabled,
                cdc_stages: parseInt(cdcStages),
                base_address: baseAddress
            }
        };
    } else {
        const filePath = moduleFileGlobal;
        fetch('/api/save_diff', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                module_name: moduleName,
                file_path: filePath,
                properties: {
                    cdc_enabled: cdcEnabled,
                    cdc_stages: parseInt(cdcStages),
                    base_address: baseAddress
                },
                registers: regs
            })
        }).then(res => res.json()).then(data => {
            if (data.redirect) window.location.href = data.redirect;
        }).catch(err => alert('Error saving changes: ' + err));
    }
}

/**
 * Confirm save file
 */
function confirmSaveFile() {
    const filePath = document.getElementById('saveFilePath').value;
    const format = document.getElementById('saveFormat').value;
    if (!filePath) {
        alert('Please enter a file path');
        return;
    }
    const data = window._pendingSave;
    if (data) {
        saveToFile(filePath, data.moduleName, data.regs, data.properties, format);
        bootstrap.Modal.getInstance(document.getElementById('saveFileModal')).hide();
    }
}

/**
 * Update file extension based on format
 */
function updateFileExtension() {
    const format = document.getElementById('saveFormat').value;
    const pathInput = document.getElementById('saveFilePath');
    let path = pathInput.value;
    path = path.replace(/\.(json|yaml|yml|xml)$/i, '.' + (format === 'yaml' ? 'yaml' : format));
    pathInput.value = path;
}

/**
 * Save to file
 */
function saveToFile(filePath, moduleName, registers, properties, format) {
    fetch('/api/save_new_module', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            file_path: filePath,
            module_name: moduleName,
            registers: registers,
            properties: properties,
            format: format
        })
    }).then(res => res.json()).then(data => {
        if (data.success) {
            alert('Module saved successfully to: ' + filePath);
            window.location.href = '/';
        } else {
            alert('Error saving module: ' + (data.error || 'Unknown error'));
        }
    }).catch(err => alert('Error saving: ' + err));
}

/**
 * Update bit range display
 * @param {HTMLInputElement} input - Input element
 */
function updateBitRange(input) {
    const row = input.closest('.subreg-field-row');
    const offsetInput = row.querySelector('.subreg-offset-input');
    const widthInput = row.querySelector('.subreg-width-input');
    const display = row.querySelector('.bit-range-display');

    const offset = parseInt(offsetInput.value || 0);
    const width = parseInt(widthInput.value || 1);
    const high = offset + width - 1;

    display.textContent = `[${high}:${offset}]`;
    updateParentDefault(input);

    const table = row.closest('.subreg-table');
    validateSubregisterOverlaps(table);
    markAsChanged();
}

/**
 * Validate subregister overlaps
 * @param {HTMLElement} tableOrElement - Table or element
 */
function validateSubregisterOverlaps(tableOrElement) {
    if (!tableOrElement) return;

    const table = tableOrElement.tagName === 'TABLE' ? tableOrElement : tableOrElement.closest('.subreg-table');
    if (!table) return;

    const rows = table.querySelectorAll('.subreg-field-row');
    const ranges = [];

    rows.forEach(row => {
        row.querySelector('.subreg-offset-input').classList.remove('input-invalid');
        row.querySelector('.subreg-width-input').classList.remove('input-invalid');
        row.title = "";
    });

    rows.forEach((row, index) => {
        const offset = parseInt(row.querySelector('.subreg-offset-input').value || 0);
        const width = parseInt(row.querySelector('.subreg-width-input').value || 1);
        ranges.push({ index, start: offset, end: offset + width - 1, row });
    });

    for (let i = 0; i < ranges.length; i++) {
        for (let j = i + 1; j < ranges.length; j++) {
            const r1 = ranges[i];
            const r2 = ranges[j];

            if (Math.max(r1.start, r2.start) <= Math.min(r1.end, r2.end)) {
                r1.row.querySelector('.subreg-offset-input').classList.add('input-invalid');
                r1.row.querySelector('.subreg-width-input').classList.add('input-invalid');
                r2.row.querySelector('.subreg-offset-input').classList.add('input-invalid');
                r2.row.querySelector('.subreg-width-input').classList.add('input-invalid');

                r1.row.title = `Overlaps with field at index ${j}`;
                r2.row.title = `Overlaps with field at index ${i}`;
            }
        }
    }
}

// ===== GENERATE MODAL LOGIC =====

let genTempDir = null;
const currentModuleName = typeof moduleNameGlobal !== 'undefined' ? moduleNameGlobal : '';

/**
 * Open generate modal
 */
function openGenerateModal() {
    genTempDir = null;
    document.getElementById('genDownloadSection').classList.add('d-none');
    document.getElementById('genLog').innerHTML = 'Ready to generate...';
    const modal = new bootstrap.Modal(document.getElementById('generateModal'));
    modal.show();
}

/**
 * Add log to generate modal
 * @param {string} text - Log text
 * @param {string} className - CSS class
 */
function genLogAdd(text, className = '') {
    const log = document.getElementById('genLog');
    const div = document.createElement('div');
    if (className) div.className = className;
    div.innerText = text;
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
}

/**
 * Run direct generate
 */
function runDirectGenerate() {
    const log = document.getElementById('genLog');
    const downloadSection = document.getElementById('genDownloadSection');
    const runBtn = document.getElementById('genRunBtn');

    log.innerHTML = '';
    downloadSection.classList.add('d-none');
    genTempDir = null;
    runBtn.disabled = true;
    runBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Generating...';

    genLogAdd('Starting generation for ' + currentModuleName + '...', 'text-info');

    const payload = {
        modules: [currentModuleName],
        formats: {
            vhdl: document.getElementById('genVhdl').checked,
            xml: document.getElementById('genXml').checked,
            yaml: document.getElementById('genYaml').checked,
            json: document.getElementById('genJson').checked,
            header: document.getElementById('genHeader').checked,
            doc_md: document.getElementById('genDocMd').checked,
            doc_html: false
        }
    };

    fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
        .then(res => res.json())
        .then(data => {
            runBtn.disabled = false;
            runBtn.innerHTML = '<i class="bi bi-play-fill me-2"></i>Generate';

            if (data.success) {
                data.logs.forEach(line => genLogAdd(line));
                genLogAdd('Generation completed successfully!', 'text-success fw-bold');

                if (data.temp_dir) {
                    genTempDir = data.temp_dir;
                    downloadSection.classList.remove('d-none');
                    genLogAdd('Click "Download ZIP" to save files.', 'text-info');
                } else {
                    genLogAdd('Files saved to: ' + data.output_dir, 'text-info');
                }
            } else {
                genLogAdd('Generation failed:', 'text-danger fw-bold');
                genLogAdd(data.error, 'text-danger');
            }
        })
        .catch(err => {
            runBtn.disabled = false;
            runBtn.innerHTML = '<i class="bi bi-play-fill me-2"></i>Generate';
            genLogAdd('Network error: ' + err, 'text-danger');
        });
}

/**
 * Download generated ZIP
 */
function downloadGeneratedZip() {
    if (!genTempDir) {
        alert('No files to download.');
        return;
    }
    window.location.href = '/api/download_generated_zip?source_dir=' + encodeURIComponent(genTempDir);

    const btn = document.getElementById('genDownloadBtn');
    btn.disabled = true;
    btn.innerHTML = '<i class="bi bi-check2-circle me-2"></i>Downloading...';

    setTimeout(() => {
        document.getElementById('genDownloadSection').classList.add('d-none');
        genLogAdd('Download started. Re-generate to download again.', 'text-warning');
        genTempDir = null;
    }, 1500);
}

// ===== INITIALIZATION =====

document.addEventListener('DOMContentLoaded', function () {
    // Store initial state
    window.initialState = getFormState();

    // Event delegation for inputs
    document.addEventListener('input', (e) => {
        if (e.target.matches('input, textarea')) markAsChanged();
    });
    document.addEventListener('change', (e) => {
        if (e.target.matches('input, select, textarea')) markAsChanged();
    });

    // Ctrl+Enter to add register
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && e.ctrlKey) {
            addRegister();
        }
    });

    // Re-capture initial state after delay
    setTimeout(() => {
        document.querySelectorAll('.reg-addr-input').forEach(input => {
            if (input.getAttribute('data-locked') === 'true') {
                // Style standardized
            }
        });
        window.initialState = getFormState();
    }, 200);

    // Detect conflicts on load
    detectAddressConflicts();

    // Validate subregisters
    document.querySelectorAll('.subreg-table').forEach(table => {
        validateSubregisterOverlaps(table);
    });

    // Warn before leaving with unsaved changes
    window.addEventListener('beforeunload', function (e) {
        if (hasUnsavedChanges) {
            e.preventDefault();
            e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
            return e.returnValue;
        }
    });

    // Intercept navigation links
    document.addEventListener('click', function (e) {
        const link = e.target.closest('a[href]');
        if (link && hasUnsavedChanges && !link.href.includes('/diff')) {
            if (!confirm('You have unsaved changes. Are you sure you want to leave?')) {
                e.preventDefault();
            }
        }
    });

    console.log('Editor module loaded');
});
