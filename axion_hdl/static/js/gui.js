/**
 * Axion-HDL GUI - Common JavaScript
 * Shared utilities and functions across all GUI pages
 */

// ===== UTILITY FUNCTIONS =====

/**
 * Validate hexadecimal input
 * @param {HTMLInputElement} input - The input element to validate
 */
function validateHex(input) {
    const val = input.value;
    const valid = /^(0x)?[0-9A-Fa-f]+$/.test(val) || val === '';
    input.classList.toggle('input-invalid', !valid && val !== '');
}

/**
 * Validate name input (identifier)
 * @param {HTMLInputElement} input - The input element to validate
 */
function validateName(input) {
    const val = input.value;
    const valid = /^[a-zA-Z_][a-zA-Z0-9_]*$/.test(val) || val === '';
    input.classList.toggle('input-invalid', !valid && val !== '');
}

/**
 * Show toast notification
 * @param {string} message - Message to display
 * @param {string} type - Type of notification (success, error, warning, info)
 * @param {number} duration - Duration in ms (default 3000)
 */
function showToast(message, type = 'info', duration = 3000) {
    return; // Disabled per user request
    // Create toast container if it doesn't exist
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        `;
        document.body.appendChild(container);
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `alert alert-${type}`;
    toast.style.cssText = `
        min-width: 300px;
        animation: slideIn 0.3s ease;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    `;
    toast.innerHTML = `
        <div class="d-flex align-items-center gap-2">
            <i class="bi bi-${getToastIcon(type)}"></i>
            <span>${message}</span>
        </div>
    `;

    container.appendChild(toast);

    // Auto remove after duration
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * Get icon for toast type
 * @param {string} type - Toast type
 * @returns {string} Bootstrap icon class
 */
function getToastIcon(type) {
    const icons = {
        success: 'check-circle-fill',
        error: 'x-circle-fill',
        warning: 'exclamation-triangle-fill',
        info: 'info-circle-fill'
    };
    return icons[type] || 'info-circle-fill';
}

/**
 * Debounce function to limit rate of function calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in ms
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Copy text to clipboard with visual feedback
 * @param {string} text - Text to copy
 * @param {HTMLElement} button - Button element for feedback (optional)
 */
async function copyToClipboard(text, button = null) {
    try {
        await navigator.clipboard.writeText(text);

        if (button) {
            const originalHTML = button.innerHTML;
            button.innerHTML = '<i class="bi bi-check"></i>';
            button.classList.add('btn-success');

            setTimeout(() => {
                button.innerHTML = originalHTML;
                button.classList.remove('btn-success');
            }, 2000);
        } else {
            showToast('Copied to clipboard!', 'success', 2000);
        }
    } catch (err) {
        console.error('Failed to copy:', err);
        showToast('Failed to copy to clipboard', 'error');
    }
}

/**
 * Format hex value with proper padding
 * @param {number|string} value - Value to format
 * @param {number} width - Bit width for padding
 * @returns {string} Formatted hex string
 */
function formatHex(value, width = 32) {
    let val = typeof value === 'string' ? parseInt(value.replace(/0x/i, ''), 16) : value;
    if (isNaN(val)) val = 0;

    const hexDigits = Math.ceil(width / 4);
    return '0x' + val.toString(16).toUpperCase().padStart(hexDigits, '0');
}

/**
 * Parse hex string to integer
 * @param {string} hexStr - Hex string to parse
 * @returns {number} Parsed integer
 */
function parseHex(hexStr) {
    if (!hexStr) return 0;
    const cleaned = hexStr.toString().replace(/0x/i, '');
    const val = parseInt(cleaned, 16);
    return isNaN(val) ? 0 : val;
}

/**
 * Show loading spinner on button
 * @param {HTMLElement} button - Button element
 * @param {string} text - Loading text
 */
function showButtonLoading(button, text = 'Loading...') {
    button.dataset.originalHTML = button.innerHTML;
    button.disabled = true;
    button.innerHTML = `
        <span class="spinner-border spinner-border-sm me-2"></span>
        ${text}
    `;
}

/**
 * Hide loading spinner on button
 * @param {HTMLElement} button - Button element
 */
function hideButtonLoading(button) {
    button.disabled = false;
    button.innerHTML = button.dataset.originalHTML || button.innerHTML;
    delete button.dataset.originalHTML;
}

/**
 * Confirm dialog with custom message
 * @param {string} message - Confirmation message
 * @param {string} confirmText - Confirm button text
 * @returns {boolean} User confirmation
 */
function confirmAction(message, confirmText = 'Confirm') {
    // Simple confirm for now, can be enhanced with custom modal
    return confirm(message);
}

/**
 * Initialize tooltips (if using Bootstrap tooltips)
 */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Safe JSON parse with fallback
 * @param {string} jsonStr - JSON string to parse
 * @param {*} fallback - Fallback value if parse fails
 * @returns {*} Parsed object or fallback
 */
function safeJSONParse(jsonStr, fallback = null) {
    try {
        return JSON.parse(jsonStr);
    } catch (e) {
        console.error('JSON parse error:', e);
        return fallback;
    }
}

/**
 * Download file to user's computer
 * @param {string} filename - Name of file
 * @param {string} content - File content
 * @param {string} mimeType - MIME type (default: text/plain)
 */
function downloadFile(filename, content, mimeType = 'text/plain') {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// ===== API HELPERS =====

/**
 * Fetch JSON from API endpoint
 * @param {string} url - API endpoint
 * @param {object} options - Fetch options
 * @returns {Promise} Response data
 */
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || `Request failed with status ${response.status}`);
        }

        return data;
    } catch (error) {
        console.error('API request error:', error);
        throw error;
    }
}

/**
 * POST request helper
 * @param {string} url - API endpoint
 * @param {object} body - Request body
 * @returns {Promise} Response data
 */
async function apiPost(url, body) {
    return apiRequest(url, {
        method: 'POST',
        body: JSON.stringify(body)
    });
}

/**
 * GET request helper
 * @param {string} url - API endpoint
 * @returns {Promise} Response data
 */
async function apiGet(url) {
    return apiRequest(url, { method: 'GET' });
}

// ===== FILE/FOLDER SELECTION =====

/**
 * Open native folder selection dialog (macOS)
 * @returns {Promise<string>} Selected folder path
 */
async function selectFolder() {
    try {
        const data = await apiGet('/api/select_folder');
        if (data.path) {
            return data.path;
        } else if (data.error && data.error !== 'User cancelled') {
            showToast(data.error, 'error');
        }
        return null;
    } catch (error) {
        console.error('Folder selection error:', error);
        showToast('Failed to select folder', 'error');
        return null;
    }
}

/**
 * Open native file selection dialog (macOS)
 * @returns {Promise<string>} Selected file path
 */
async function selectFile() {
    try {
        const data = await apiGet('/api/select_file');
        if (data.path) {
            return data.path;
        } else if (data.error && data.error !== 'User cancelled') {
            showToast(data.error, 'error');
        }
        return null;
    } catch (error) {
        console.error('File selection error:', error);
        showToast('Failed to select file', 'error');
        return null;
    }
}

// ===== LOGGING HELPERS =====

/**
 * Append log entry to a log container
 * @param {string} containerId - ID of log container element
 * @param {string} message - Log message
 * @param {string} className - CSS class for styling (optional)
 */
function logAppend(containerId, message, className = '') {
    const container = document.getElementById(containerId);
    if (!container) {
        console.warn(`Log container '${containerId}' not found`);
        return;
    }

    const line = document.createElement('div');
    if (className) line.className = className;
    line.textContent = message;
    container.appendChild(line);

    // Auto-scroll to bottom
    container.scrollTop = container.scrollHeight;
}

/**
 * Clear log container
 * @param {string} containerId - ID of log container element
 */
function logClear(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = '';
    }
}

/**
 * Set badge status
 * @param {string} badgeId - Badge element ID
 * @param {string} status - Status type (success, error, warning, info, running)
 * @param {string} text - Badge text
 */
function setBadgeStatus(badgeId, status, text) {
    const badge = document.getElementById(badgeId);
    if (!badge) return;

    // Remove all status classes
    badge.className = 'badge';

    // Add new status class
    const statusMap = {
        success: 'bg-success',
        error: 'bg-danger',
        warning: 'bg-warning',
        info: 'bg-info',
        running: 'bg-primary'
    };

    badge.classList.add(statusMap[status] || 'bg-secondary');
    badge.textContent = text;
}

// ===== MODULE SELECTION HELPERS =====

/**
 * Load modules list from API
 * @param {string} containerId - Container element ID
 * @param {string} checkboxClass - Checkbox class name
 * @returns {Promise<Array>} List of modules
 */
async function loadModules(containerId, checkboxClass = 'module-checkbox') {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container '${containerId}' not found`);
        return [];
    }

    try {
        const modules = await apiGet('/api/modules');

        if (modules.length === 0) {
            container.innerHTML = '<div class="text-muted small">No modules found.</div>';
            return [];
        }

        container.innerHTML = modules.map(name => `
            <div class="form-check">
                <input class="form-check-input ${checkboxClass}" type="checkbox"
                       value="${name}" id="mod_${name}" checked>
                <label class="form-check-label font-monospace small" for="mod_${name}">
                    ${name}
                </label>
            </div>
        `).join('');

        return modules;
    } catch (error) {
        container.innerHTML = '<div class="text-danger small">Failed to load modules.</div>';
        return [];
    }
}

/**
 * Get selected module names
 * @param {string} checkboxClass - Checkbox class selector
 * @returns {Array<string>} Selected module names
 */
function getSelectedModules(checkboxClass = 'module-checkbox') {
    return Array.from(document.querySelectorAll(`.${checkboxClass}:checked`))
        .map(cb => cb.value);
}

/**
 * Select/deselect all modules
 * @param {boolean} select - True to select all, false to deselect all
 * @param {string} checkboxClass - Checkbox class selector
 */
function selectAllModules(select, checkboxClass = 'module-checkbox') {
    document.querySelectorAll(`.${checkboxClass}`).forEach(cb => {
        cb.checked = select;
    });
}

// ===== ANIMATIONS =====

// Add CSS for toast animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(100%);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes slideOut {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }

    .input-invalid {
        border-color: var(--error-color) !important;
        background-color: rgba(239, 68, 68, 0.1) !important;
    }
`;
document.head.appendChild(style);

// ===== INITIALIZATION =====

document.addEventListener('DOMContentLoaded', function () {
    // Initialize tooltips if Bootstrap is loaded
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        initTooltips();
    }

    // Log GUI JS loaded
    console.log('Axion GUI utilities loaded');
});
