/**
 * Axion-HDL GUI - Rule Check Module
 */

let lastAnalysisTime = 0;
let analysisPollingInterval = null;

/**
 * Initialize rule check page
 */
function initRuleCheck() {
    // Run check automatically on page load
    runCheck();
    console.log('Rule Check module loaded');

    // Start polling for analysis updates
    startAnalysisPolling();
}

/**
 * Start polling for analysis status updates
 */
function startAnalysisPolling() {
    // Initial status check
    checkAnalysisStatus();

    // Poll every 5 seconds
    analysisPollingInterval = setInterval(checkAnalysisStatus, 5000);
}

/**
 * Check analysis status
 */
async function checkAnalysisStatus() {
    try {
        const status = await apiGet('/api/analysis_status');

        // Initialize lastAnalysisTime on first check
        if (lastAnalysisTime === 0) {
            lastAnalysisTime = status.last_analysis_time;
            return;
        }

        // If analysis completed since last check, re-run checks
        if (status.last_analysis_time > lastAnalysisTime) {
            console.log('[Axion] Analysis updated, re-running checks...');
            runCheck();
            lastAnalysisTime = status.last_analysis_time;
        }

        // Show analyzing indicator if analyzing
        if (status.is_analyzing) {
            showAnalyzingIndicator();
        } else {
            hideAnalyzingIndicator();
        }
    } catch (error) {
        // Silent error - don't spam console
    }
}

/**
 * Show analyzing indicator
 */
function showAnalyzingIndicator() {
    let indicator = document.getElementById('analyzing-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'analyzing-indicator';
        indicator.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #161b22;
            border: 1px solid rgba(0, 217, 255, 0.5);
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            display: flex;
            align-items: center;
            gap: 10px;
            z-index: 1000;
        `;
        indicator.innerHTML = `
            <div class="spinner-border spinner-border-sm" style="color: #00d9ff; width: 16px; height: 16px;"></div>
            <span style="color: #e6edf3; font-size: 0.9rem;">Analyzing files...</span>
        `;
        document.body.appendChild(indicator);
    }
}

/**
 * Hide analyzing indicator
 */
function hideAnalyzingIndicator() {
    const indicator = document.getElementById('analyzing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (analysisPollingInterval) {
        clearInterval(analysisPollingInterval);
    }
});

/**
 * Run design rule check
 */
async function runCheck() {
    const loadingDiv = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');
    const activityLog = document.getElementById('activity-log');

    // Show loading, hide results
    loadingDiv.style.display = 'block';
    resultsDiv.style.display = 'none';

    // Clear activity log
    if (activityLog) {
        logClear('activity-log');
        logAppend('activity-log', 'Starting Design Rule Check...', 'text-info');
    }

    try {
        // Call API to run rule check
        const data = await apiGet('/api/run_check');

        // Update activity log
        if (activityLog && data.logs) {
            data.logs.forEach(line => logAppend('activity-log', line));
        }

        // Update checked modules count
        document.getElementById('checkedModules').textContent = data.checked_modules || 0;

        // Render results
        renderResults(data);

        // Hide loading, show results
        loadingDiv.style.display = 'none';
        resultsDiv.style.display = 'block';

        // Show summary toast
        if (data.summary.passed) {
            showToast('All checks passed!', 'success');
        } else {
            showToast(`Found ${data.summary.total_errors} error(s) and ${data.summary.total_warnings} warning(s)`, 'warning');
        }

    } catch (error) {
        loadingDiv.style.display = 'none';

        if (activityLog) {
            logAppend('activity-log', 'Error: ' + error.message, 'text-danger');
        }

        showToast('Rule check failed: ' + error.message, 'error');
        console.error('Rule check error:', error);
    }
}

/**
 * Render rule check results
 * @param {object} data - Rule check data from API
 */
function renderResults(data) {
    const { errors, warnings, summary } = data;

    // Update badge counts
    document.getElementById('badge-errors').textContent = summary.total_errors;
    document.getElementById('badge-warnings').textContent = summary.total_warnings;

    // Render status card
    renderStatusCard(summary);

    // Combine all issues for "All" tab
    const allIssues = [
        ...errors.map(e => ({ ...e, severity: 'error' })),
        ...warnings.map(w => ({ ...w, severity: 'warning' }))
    ];

    // Render tabs
    renderIssueList('pills-all', allIssues);
    renderIssueList('pills-errors', errors.map(e => ({ ...e, severity: 'error' })));
    renderIssueList('pills-warnings', warnings.map(w => ({ ...w, severity: 'warning' })));
}

/**
 * Render status card
 * @param {object} summary - Summary object
 */
function renderStatusCard(summary) {
    const statusCard = document.getElementById('status-card');

    if (summary.passed) {
        statusCard.innerHTML = `
            <div class="d-flex align-items-center gap-3">
                <i class="bi bi-check-circle-fill text-success" style="font-size: 2rem;"></i>
                <div>
                    <h5 class="mb-0">All Checks Passed</h5>
                    <p class="mb-0 text-secondary">No design rule violations found.</p>
                </div>
            </div>
        `;
        statusCard.style.background = 'rgba(34, 197, 94, 0.1)';
        statusCard.style.border = '1px solid rgba(34, 197, 94, 0.3)';
    } else {
        statusCard.innerHTML = `
            <div class="d-flex align-items-center gap-3">
                <i class="bi bi-exclamation-triangle-fill text-warning" style="font-size: 2rem;"></i>
                <div>
                    <h5 class="mb-0">Issues Found</h5>
                    <p class="mb-0 text-secondary">
                        <span class="badge bg-danger me-2">${summary.total_errors} Error(s)</span>
                        <span class="badge bg-warning text-dark">${summary.total_warnings} Warning(s)</span>
                    </p>
                </div>
            </div>
        `;
        statusCard.style.background = 'rgba(251, 191, 36, 0.1)';
        statusCard.style.border = '1px solid rgba(251, 191, 36, 0.3)';
    }
}

/**
 * Render issue list in a tab
 * @param {string} tabId - Tab container ID
 * @param {Array} issues - List of issues
 */
function renderIssueList(tabId, issues) {
    const container = document.getElementById(tabId);

    if (issues.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5 text-secondary">
                <i class="bi bi-check-circle" style="font-size: 3rem; opacity: 0.5;"></i>
                <p class="mt-3">No issues to display</p>
            </div>
        `;
        return;
    }

    // Group issues by module
    const grouped = {};
    issues.forEach(issue => {
        const module = issue.module || 'Unknown';
        if (!grouped[module]) {
            grouped[module] = [];
        }
        grouped[module].push(issue);
    });

    // Render grouped issues
    container.innerHTML = '';
    Object.keys(grouped).sort().forEach(name => {
        const moduleIssues = grouped[name];

        // Count errors vs warnings for module badge color
        const errorCount = moduleIssues.filter(i => i.severity === 'error').length;
        const hasErrors = errorCount > 0;

        const rows = moduleIssues.map(i => {
            const msg = i.msg.replace(/(0x[0-9A-Fa-f]+)/g, '<code>$1</code>');

            // Each issue gets its own badge color based on severity
            const badgeClass = i.severity === 'error' ? 'bg-danger text-white' : 'bg-warning text-dark';

            return `<tr>
                <td class="issue-type-cell">
                    <span class="badge ${badgeClass}">${i.type}</span>
                </td>
                <td class="issue-msg">${msg}</td>
            </tr>`;
        }).join('');

        container.innerHTML += `
            <div class="module-section">
                <div class="module-header">
                    <h5><i class="bi bi-box-seam me-2"></i>${name}</h5>
                    <span class="module-count"
                          style="background:${hasErrors ? '#fee2e2; color:#dc2626' : '#fef3c7; color:#d97706'}">
                        ${moduleIssues.length}
                    </span>
                </div>
                <table class="issues-table">
                    <thead><tr><th>Type</th><th>Message</th></tr></thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>`;
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initRuleCheck);
