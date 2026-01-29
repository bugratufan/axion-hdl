/**
 * Axion-HDL GUI - Generate Module
 * Code generation page logic
 */

let lastTempDir = null;

/**
 * Initialize generate page
 */
function initGenerate() {
    // Load modules list
    loadModules('modulesList', 'module-checkbox');

    console.log('Generate module loaded');
}

/**
 * Log message to console output
 * @param {string} message - Message to log
 * @param {string} className - CSS class for styling
 */
function logAdd(message, className = '') {
    logAppend('consoleOutput', message, className);
}

/**
 * Run generation process
 */
async function runGenerate() {
    const log = document.getElementById('consoleOutput');
    const downloadSection = document.getElementById('downloadSection');

    // Reset state
    logClear('consoleOutput');
    downloadSection.style.display = 'none';
    lastTempDir = null;

    // Update status
    setBadgeStatus('statusBadge', 'running', 'Running...');
    logAdd('Initializing generation...', 'text-info');

    // Get selected modules
    const selectedModules = getSelectedModules();
    if (selectedModules.length === 0) {
        setBadgeStatus('statusBadge', 'warning', 'Warning');
        logAdd('No modules selected. Please select at least one module.', 'text-warning');
        return;
    }

    // Build payload
    const payload = {
        output_dir: document.getElementById('outputDir').value || null,
        modules: selectedModules,
        formats: {
            vhdl: document.getElementById('fmtVhdl').checked,
            xml: document.getElementById('fmtXml').checked,
            yaml: document.getElementById('fmtYaml').checked,
            json: document.getElementById('fmtJson').checked,
            header: document.getElementById('fmtHeader').checked,
            doc_md: document.getElementById('fmtDocMd').checked,
            doc_html: document.getElementById('fmtDocHtml').checked
        }
    };

    try {
        const data = await apiPost('/api/generate', payload);

        if (data.success) {
            setBadgeStatus('statusBadge', 'success', 'Success');
            logAdd('----------------------------------------', 'text-secondary');
            data.logs.forEach(line => logAdd(line));
            logAdd('Generation completed successfully.', 'text-success');

            if (data.temp_dir) {
                lastTempDir = data.temp_dir;
                downloadSection.style.display = 'block';
                logAdd('Click "Download ZIP" to save files.', 'text-info');
            } else {
                logAdd(`Files saved to: ${data.output_dir}`, 'text-info');
            }
        } else {
            setBadgeStatus('statusBadge', 'error', 'Failed');
            logAdd('Generation failed:', 'text-danger');
            data.logs.forEach(line => logAdd(line, 'text-danger'));
        }
    } catch (error) {
        setBadgeStatus('statusBadge', 'error', 'Error');
        logAdd('Network error: ' + error.message, 'text-danger');
    }
}

/**
 * Download generated files as ZIP
 */
function downloadZip() {
    if (!lastTempDir) {
        showToast('No files to download', 'warning');
        return;
    }

    const downloadUrl = '/api/download_generated_zip?source_dir=' + encodeURIComponent(lastTempDir);
    window.location.href = downloadUrl;

    showToast('Download started...', 'success');

    // Reset state after brief delay
    setTimeout(() => {
        document.getElementById('downloadSection').style.display = 'none';
        logAdd('Download started. Re-generate to download again.', 'text-warning');
        lastTempDir = null;
    }, 1500);
}

/**
 * Select output folder using native dialog
 */
async function browseOutputFolder() {
    const path = await selectFolder();
    if (path) {
        document.getElementById('outputDir').value = path;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initGenerate);
