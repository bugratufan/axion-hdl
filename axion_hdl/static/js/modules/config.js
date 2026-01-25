/**
 * Axion-HDL GUI - Config Module
 * Configuration management page logic
 */

let currentConfig = null;

/**
 * Initialize config page
 */
function initConfig() {
    loadConfig();
    console.log('Config module loaded');
}

/**
 * Load current configuration from API
 */
async function loadConfig() {
    try {
        const config = await apiGet('/api/config');
        currentConfig = config;
        renderConfig(config);
        updateUnsavedBadge(config.unsaved_changes || false);
    } catch (error) {
        showToast('Failed to load configuration', 'error');
        console.error('Load config error:', error);
    }
}

/**
 * Render configuration to UI
 * @param {object} config - Configuration object
 */
function renderConfig(config) {
    // Render output directory
    const outputDirElem = document.getElementById('currentOutputDir');
    if (outputDirElem) {
        outputDirElem.textContent = config.output_dir || '(Not set - using temp dir)';
    }

    // Combine all sources
    const allDirs = [
        ...config.src_dirs.map(p => ({ path: p, type: 'dir', fileType: 'vhdl' })),
        ...config.xml_src_dirs.map(p => ({ path: p, type: 'dir', fileType: 'xml' })),
        ...config.yaml_src_dirs.map(p => ({ path: p, type: 'dir', fileType: 'yaml' })),
        ...config.json_src_dirs.map(p => ({ path: p, type: 'dir', fileType: 'json' })),
        ...config.src_files.map(p => ({ path: p, type: 'file', fileType: 'vhdl' })),
        ...config.xml_src_files.map(p => ({ path: p, type: 'file', fileType: 'xml' })),
        ...config.yaml_src_files.map(p => ({ path: p, type: 'file', fileType: 'yaml' })),
        ...config.json_src_files.map(p => ({ path: p, type: 'file', fileType: 'json' }))
    ];

    // Render directories and files
    const dirsList = document.getElementById('srcDirsList');
    const filesList = document.getElementById('srcFilesList');

    const dirs = allDirs.filter(item => item.type === 'dir');
    const files = allDirs.filter(item => item.type === 'file');

    if (dirs.length === 0) {
        dirsList.innerHTML = '<li class="empty-list">No source directories configured</li>';
    } else {
        dirsList.innerHTML = dirs.map(item => `
            <li class="path-item">
                <span class="badge type-badge ${item.fileType}">${item.fileType.toUpperCase()}</span>
                <code>${item.path}</code>
                <button class="remove-btn" onclick="removeSource('dir', '${item.path}', '${item.fileType}')">
                    <i class="bi bi-trash"></i>
                </button>
            </li>
        `).join('');
    }

    if (files.length === 0) {
        filesList.innerHTML = '<li class="empty-list">No source files configured</li>';
    } else {
        filesList.innerHTML = files.map(item => `
            <li class="path-item">
                <span class="badge type-badge ${item.fileType}">${item.fileType.toUpperCase()}</span>
                <code>${item.path}</code>
                <button class="remove-btn" onclick="removeSource('file', '${item.path}', '${item.fileType}')">
                    <i class="bi bi-trash"></i>
                </button>
            </li>
        `).join('');
    }

    // Render exclude patterns
    const excludeList = document.getElementById('excludeList');
    const patterns = config.exclude_patterns || [];

    if (patterns.length === 0) {
        excludeList.innerHTML = '<li class="empty-list">No exclude patterns</li>';
    } else {
        excludeList.innerHTML = patterns.map(p => `
            <li class="path-item">
                <code>${p}</code>
                <button class="remove-btn" onclick="removeExclude('${p}')">
                    <i class="bi bi-trash"></i>
                </button>
            </li>
        `).join('');
    }
}

/**
 * Add source directory or file
 * @param {string} type - 'dir' or 'file'
 */
async function addSource(type) {
    const input = type === 'dir'
        ? document.getElementById('newSrcDir')
        : document.getElementById('newSrcFile');

    const path = input.value.trim();
    if (!path) {
        showToast('Please enter a path', 'warning');
        return;
    }

    try {
        await apiPost('/api/config/add_source', { path, type });
        input.value = '';
        loadConfig();
        showToast('Source added successfully', 'success');
    } catch (error) {
        showToast(error.message || 'Failed to add source', 'error');
    }
}

/**
 * Browse for folder using native dialog
 */
async function browseFolder() {
    const path = await selectFolder();
    if (path) {
        document.getElementById('newSrcDir').value = path;
    }
}

/**
 * Browse for file using native dialog
 */
async function browseFile() {
    const path = await selectFile();
    if (path) {
        document.getElementById('newSrcFile').value = path;
    }
}

/**
 * Remove source directory or file
 * @param {string} type - 'dir' or 'file'
 * @param {string} path - Path to remove
 * @param {string} fileType - File type (vhdl, xml, yaml, json)
 */
async function removeSource(type, path, fileType) {
    if (!confirm(`Remove this ${type}?\n${path}`)) {
        return;
    }

    try {
        await apiPost('/api/config/remove_source', { path, type, file_type: fileType });
        loadConfig();
        showToast('Source removed', 'success');
    } catch (error) {
        showToast(error.message || 'Failed to remove source', 'error');
    }
}

/**
 * Add exclude pattern
 */
async function addExclude() {
    const input = document.getElementById('newExclude');
    const pattern = input.value.trim();

    if (!pattern) {
        showToast('Please enter a pattern', 'warning');
        return;
    }

    try {
        await apiPost('/api/config/add_exclude', { pattern });
        input.value = '';
        loadConfig();
        showToast('Exclude pattern added', 'success');
    } catch (error) {
        showToast(error.message || 'Failed to add exclude pattern', 'error');
    }
}

/**
 * Remove exclude pattern
 * @param {string} pattern - Pattern to remove
 */
async function removeExclude(pattern) {
    if (!confirm(`Remove exclude pattern?\n${pattern}`)) {
        return;
    }

    try {
        await apiPost('/api/config/remove_exclude', { pattern });
        loadConfig();
        showToast('Exclude pattern removed', 'success');
    } catch (error) {
        showToast(error.message || 'Failed to remove exclude pattern', 'error');
    }
}

/**
 * Refresh configuration (re-analyze sources)
 */
async function refreshConfig() {
    const btn = document.getElementById('refreshBtn');
    const log = document.getElementById('refreshLog');

    showButtonLoading(btn, 'Refreshing...');
    logClear('refreshLog');
    logAppend('refreshLog', 'Refreshing configuration...', 'text-info');

    try {
        const data = await apiPost('/api/config/refresh', {});

        if (data.success) {
            data.logs.forEach(line => logAppend('refreshLog', line));
            logAppend('refreshLog', 'Refresh completed successfully.', 'text-success');
            loadConfig();
            showToast('Configuration refreshed', 'success');
        } else {
            data.logs.forEach(line => logAppend('refreshLog', line, 'text-danger'));
            showToast('Refresh failed', 'error');
        }
    } catch (error) {
        logAppend('refreshLog', 'Error: ' + error.message, 'text-danger');
        showToast('Refresh failed', 'error');
    } finally {
        hideButtonLoading(btn);
    }
}

/**
 * Save configuration to .axion_conf
 */
async function saveConfig() {
    const btn = document.getElementById('saveBtn');
    showButtonLoading(btn, 'Saving...');

    try {
        const data = await apiPost('/api/config/save', {});

        if (data.success) {
            showToast('Configuration saved to .axion_conf', 'success');
            updateUnsavedBadge(false);
        } else {
            showToast(data.error || 'Failed to save configuration', 'error');
        }
    } catch (error) {
        showToast(error.message || 'Failed to save configuration', 'error');
    } finally {
        hideButtonLoading(btn);
    }
}

/**
 * Export configuration as JSON file
 */
async function exportConfig() {
    try {
        const response = await fetch('/api/config/export');
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'axion_config.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        showToast('Configuration exported', 'success');
    } catch (error) {
        showToast('Export failed', 'error');
    }
}

/**
 * Update unsaved changes badge
 * @param {boolean} hasUnsaved - Whether there are unsaved changes
 */
function updateUnsavedBadge(hasUnsaved) {
    const badge = document.getElementById('unsavedBadge');
    if (badge) {
        badge.style.display = hasUnsaved ? 'inline-block' : 'none';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initConfig);
