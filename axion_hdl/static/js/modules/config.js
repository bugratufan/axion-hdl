/**
 * Axion-HDL GUI - Config Module
 * Configuration management page logic
 */

let currentConfig = null;
let detectedFilesCache = []; // Store for filtering

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

    // Combine sources for "Detected Files" list
    // Note: The API returns discrete lists, we combine them for "Detected" view
    // The "Source Directories" and "Source Files" lists in UI should only show user-configured items
    // But the API response mixes them slightly depending on implementation.
    // Assuming config.src_dirs etc are the user configured ones.

    // 1. Render User Configured Source Directories
    renderList('srcDirsList', [
        ...config.src_dirs.map(p => ({ path: p, type: 'dir', fileType: 'vhdl' })),
        ...config.xml_src_dirs.map(p => ({ path: p, type: 'dir', fileType: 'xml' })),
        ...config.yaml_src_dirs.map(p => ({ path: p, type: 'dir', fileType: 'yaml' })),
        ...config.json_src_dirs.map(p => ({ path: p, type: 'dir', fileType: 'json' }))
    ], 'dir');

    // 2. Render User Configured Source Files
    renderList('srcFilesList', [
        ...config.src_files.map(p => ({ path: p, type: 'file', fileType: 'vhdl' })),
        ...config.xml_src_files.map(p => ({ path: p, type: 'file', fileType: 'xml' })),
        ...config.yaml_src_files.map(p => ({ path: p, type: 'file', fileType: 'yaml' })),
        ...config.json_src_files.map(p => ({ path: p, type: 'file', fileType: 'json' }))
    ], 'file');

    // 3. Render Exclude Patterns
    const excludeList = document.getElementById('excludeList');
    const patterns = config.exclude_patterns || [];
    if (patterns.length === 0) {
        excludeList.innerHTML = '<li class="empty-list">No exclude patterns</li>';
    } else {
        excludeList.innerHTML = patterns.map(p => `
            <li class="path-item">
                <code class="text-danger">${p}</code>
                <button class="remove-btn" onclick="removeExclude('${p}')" title="Remove Pattern">
                    <i class="bi bi-x-lg"></i>
                </button>
            </li>
        `).join('');
    }

    // 4. Update Detected Files Cache (This would ideally come from a separate API or analysis result)
    // For now we simulate it with what we have + potentially analyzed files if available in config object
    // If the API doesn't return *all* detected files, we might only see configured ones.
    // Let's check what we have.
    // In many implementations, 'src_files' in config might just be explicitly added files.
    // To get ALL detected files (including those inside dirs), we might need the 'modules' API or similar.
    // But for this view, let's show the configured sources as a baseline, or if the API provided a 'detected_files' field (it doesnt seemingly).
    // Let's aggregate all configured items for now as "Tracked Paths". 

    // BETTER APPROACH: Fetch modules to see what files were actually found/analyzed
    fetchDetectedFiles();
}

async function fetchDetectedFiles() {
    try {
        // Fetch modules to get actual file paths that were analyzed
        const modules = await apiGet('/api/modules');
        // Note: /api/modules returns names only. We need details.
        // Let's trust the loadConfig's lists for now, but formatted nicely.
        // Or if we want real "Detected Files" (recursive scan results), we need an endpoint for it.
        // Assuming we just list the *configured* inputs for now in the right panel to show what the tool is looking at.

        // Actually, let's mix the configured items.

        detectedFilesCache = [
            ...currentConfig.src_dirs.map(p => ({ path: p, type: 'USER DIRECTORY', fileType: 'dir' })),
            ...currentConfig.src_files.map(p => ({ path: p, type: 'USER FILE', fileType: 'vhdl' })),
            // Add check for other types...
            ...currentConfig.xml_src_files.map(p => ({ path: p, type: 'USER FILE', fileType: 'xml' })),
            // etc
        ];

        // Update count
        document.getElementById('detectedCount').textContent = detectedFilesCache.length;
        renderDetectedFiles(detectedFilesCache);

    } catch (e) {
        console.error("Error fetching detected details", e);
    }
}


function renderList(elementId, items, sourceType) {
    const list = document.getElementById(elementId);
    if (!list) return;

    if (items.length === 0) {
        list.innerHTML = `<li class="empty-list">No ${sourceType === 'dir' ? 'directories' : 'files'} added</li>`;
        return;
    }

    list.innerHTML = items.map(item => `
        <li class="path-item">
            <span class="type-badge ${item.fileType}">${item.fileType}</span>
            <code title="${item.path}">${truncatePath(item.path)}</code>
            <button class="remove-btn" onclick="removeSource('${sourceType}', '${item.path}', '${item.fileType}')" title="Remove">
                <i class="bi bi-trash"></i>
            </button>
        </li>
    `).join('');
}


function renderDetectedFiles(files) {
    const list = document.getElementById('detectedFilesList');
    if (!list) return;

    if (files.length === 0) {
        list.innerHTML = '<li class="list-group-item bg-transparent text-center text-muted p-4">No sources configured.</li>';
        return;
    }

    list.innerHTML = files.map(item => `
        <li class="path-item list-group-item d-flex justify-content-between align-items-center">
            <div class="d-flex align-items-center gap-2 overflow-hidden">
                <i class="bi ${item.fileType === 'dir' ? 'bi-folder-fill text-primary' : 'bi-file-earmark-code text-secondary'}"></i>
                <code class="text-truncate" title="${item.path}">${item.path}</code>
            </div>
            <span class="badge bg-dark border border-secondary text-secondary" style="font-size: 0.6rem;">${item.type}</span>
        </li>
    `).join('');
}

function filterDetectedFiles() {
    const query = document.getElementById('filterFiles').value.toLowerCase();
    const filtered = detectedFilesCache.filter(item => item.path.toLowerCase().includes(query));
    renderDetectedFiles(filtered);
}

function truncatePath(path) {
    // helper to shorten long paths if needed for UI, though CSS text-overflow is better
    return path;
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
        await loadConfig(); // Reload to update UI
        showToast('Source added successfully', 'success');
    } catch (error) {
        showToast(error.message || 'Failed to add source', 'error');
    }
}

/**
 * Remove source directory or file
 */
async function removeSource(type, path, fileType) {
    if (!confirm(`Remove this ${type}?\n${path}`)) {
        return;
    }

    try {
        await apiPost('/api/config/remove_source', { path, type, file_type: fileType });
        await loadConfig();
        showToast('Source removed', 'success');
    } catch (error) {
        showToast(error.message || 'Failed to remove source', 'error');
    }
}

/**
 * Add/Remove Exclude Patterns
 */
async function addExclude() {
    const input = document.getElementById('newExclude');
    const pattern = input.value.trim();

    if (!pattern) return;

    try {
        await apiPost('/api/config/add_exclude', { pattern });
        input.value = '';
        await loadConfig();
        showToast('Exclude pattern added', 'success');
    } catch (error) {
        showToast(error.message || 'Failed to add pattern', 'error');
    }
}

async function removeExclude(pattern) {
    if (!confirm(`Remove pattern: ${pattern}?`)) return;
    try {
        await apiPost('/api/config/remove_exclude', { pattern });
        await loadConfig();
        showToast('Pattern removed', 'success');
    } catch (error) {
        showToast('Failed to remove pattern', 'error');
    }
}

/**
 * Browse Handlers
 */
async function browseFolder() {
    const path = await selectFolder();
    if (path) document.getElementById('newSrcDir').value = path;
}

async function browseFile() {
    const path = await selectFile();
    if (path) document.getElementById('newSrcFile').value = path;
}

/**
 * Toolbar Actions
 */
async function refreshConfig() {
    const btn = document.getElementById('refreshBtn');
    const log = document.getElementById('refreshLog');

    // Auto-show logs
    const collapseElement = document.getElementById('logsCollapse');
    if (collapseElement && !collapseElement.classList.contains('show')) {
        new bootstrap.Collapse(collapseElement, { toggle: true });
    }

    // Reset Log
    log.innerHTML = '';
    const addLog = (msg, color = 'text-light') => {
        const div = document.createElement('div');
        div.className = color;
        div.innerText = `> ${msg}`;
        log.appendChild(div);
    };

    showButtonLoading(btn, 'Refreshing...');
    addLog('Starting refresh...', 'text-info');

    try {
        const data = await apiPost('/api/config/refresh', {});
        if (data.success) {
            (data.logs || []).forEach(l => addLog(l));
            addLog('Refresh successful!', 'text-success');
            loadConfig();
            fetchDetectedFiles(); // Also refresh the detected files list
            showToast('Configuration refreshed', 'success');
        } else {
            (data.logs || []).forEach(l => addLog(l, 'text-danger'));
            addLog('Refresh failed.', 'text-danger');
            showToast('Refresh failed', 'error');
        }
    } catch (e) {
        addLog(e.message, 'text-danger');
    } finally {
        hideButtonLoading(btn);
    }
}

async function saveConfig() {
    const btn = document.getElementById('saveBtn');
    showButtonLoading(btn, 'Saving...');
    try {
        const data = await apiPost('/api/config/save', {});
        if (data.success) {
            showToast('Configuration saved to disk', 'success');
            updateUnsavedBadge(false);
        } else {
            showToast(data.error || 'Save failed', 'error');
        }
    } catch (e) {
        showToast(e.message, 'error');
    } finally {
        hideButtonLoading(btn);
    }
}

async function exportConfig() {
    try {
        const response = await fetch('/api/config/export');
        if (!response.ok) throw new Error("Network response was not ok");
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'axion_config.json';
        document.body.appendChild(a);
        a.click();
        a.remove();
        showToast('Configuration exported', 'success');
    } catch (e) {
        showToast('Export failed', 'error');
    }
}

function updateUnsavedBadge(hasUnsaved) {
    const badge = document.getElementById('unsavedBadge');
    if (badge) badge.style.display = hasUnsaved ? 'block' : 'none';
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initConfig);
