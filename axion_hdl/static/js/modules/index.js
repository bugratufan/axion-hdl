/**
 * Axion-HDL GUI - Index/Dashboard Module
 * Module list filtering and search
 */

let lastAnalysisTime = 0;
let analysisPollingInterval = null;

/**
 * Filter modules based on search input
 */
// Initialize on page load
// Initialize on page load
function initIndexModule() {
    console.log('[Axion] Index module init started');

    // Attach search listener
    const searchInput = document.getElementById('moduleSearch');
    if (searchInput) {
        console.log('[Axion] Search input found');
        // Remove the inline onkeyup if it exists (allows for cleaner HTML later)
        if (searchInput.hasAttribute('onkeyup')) {
            searchInput.removeAttribute('onkeyup');
        }

        // Remove existing listeners if any (not easily possible with anonymous functions but we are replacing the logic)
        // Just add new ones
        searchInput.addEventListener('keyup', filterModules);
        searchInput.addEventListener('search', filterModules); // Handles built-in clear buttons
        searchInput.addEventListener('input', filterModules); // Handles paste and other inputs

        console.log('[Axion] Search listeners attached');
    } else {
        console.error('[Axion] Search input NOT found');
    }

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

        // If analysis completed since last check, refresh page
        if (status.last_analysis_time > lastAnalysisTime) {
            console.log('[Axion] Analysis updated, refreshing page...');
            location.reload();
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

// Run immediately if DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initIndexModule);
} else {
    initIndexModule();
}

/**
 * Calculate Levenshtein distance between two strings
 */
function levenshtein(a, b) {
    if (a.length === 0) return b.length;
    if (b.length === 0) return a.length;

    const matrix = [];

    for (let i = 0; i <= b.length; i++) {
        matrix[i] = [i];
    }

    for (let j = 0; j <= a.length; j++) {
        matrix[0][j] = j;
    }

    for (let i = 1; i <= b.length; i++) {
        for (let j = 1; j <= a.length; j++) {
            if (b.charAt(i - 1) === a.charAt(j - 1)) {
                matrix[i][j] = matrix[i - 1][j - 1];
            } else {
                matrix[i][j] = Math.min(
                    matrix[i - 1][j - 1] + 1, // substitution
                    Math.min(
                        matrix[i][j - 1] + 1, // insertion
                        matrix[i - 1][j] + 1  // deletion
                    )
                );
            }
        }
    }

    return matrix[b.length][a.length];
}

/**
 * Fuzzy check if pattern is in text (with typo tolerance)
 * Uses sliding window Levenshtein
 */
function isFuzzyMatch(text, pattern) {
    // 1. Exact substring match (fast path)
    if (text.indexOf(pattern) > -1) return true;

    // 2. If pattern is very short, insist on exact match (too much noise otherwise)
    if (pattern.length < 3) return false;

    // 3. Sliding window Levenshtein
    // We scan substrings of 'text' that are roughly the same length as 'pattern'
    // and check their edit distance.

    // Allow 1 error for length 3-5, 2 errors for 6+, etc.
    const maxErrors = pattern.length > 5 ? 2 : 1;

    // We only need to check substrings of length pattern.length +/- 1
    // because larger/smaller differences would exceed error limits mostly.
    const pLen = pattern.length;
    const tLen = text.length;

    // Optimization: if text is shorter than pattern - maxErrors, it can't match
    if (tLen < pLen - maxErrors) return false;

    // Scan windows
    for (let i = 0; i <= tLen - pLen + maxErrors; i++) {
        // Define window bounds
        // We act conservative: take a slice of similar length
        // But we need to handle "insertion" and "deletion" which change length.
        // Let's try slices of length pLen, pLen-1, pLen+1

        for (let lenOffset = -1; lenOffset <= 1; lenOffset++) {
            const wLen = pLen + lenOffset;
            if (i + wLen > tLen) continue;
            if (wLen <= 0) continue;

            const substr = text.substr(i, wLen);
            const dist = levenshtein(pattern, substr);

            if (dist <= maxErrors) {
                return true;
            }
        }
    }

    return false;
}

/**
 * Filter modules based on search input
 */
function filterModules() {
    const input = document.getElementById('moduleSearch');
    if (!input) return;

    const filter = input.value.toLowerCase().trim();
    console.log('[Axion] Filtering modules with:', filter);

    const list = document.querySelector('.module-list');
    if (!list) return;

    const cards = list.getElementsByClassName('module-card');

    let visibleCount = 0;

    for (let i = 0; i < cards.length; i++) {
        const nameSpan = cards[i].querySelector('.module-name-text');
        if (nameSpan) {
            const txtValue = (nameSpan.textContent || nameSpan.innerText).trim();
            const lowerTxt = txtValue.toLowerCase();

            let isMatch = false;
            if (filter === '') {
                isMatch = true;
            } else {
                isMatch = isFuzzyMatch(lowerTxt, filter);
            }

            if (isMatch) {
                // Show - remove forced display:none if set
                if (cards[i].style.getPropertyValue('display') === 'none') {
                    cards[i].style.removeProperty('display');
                }
                visibleCount++;
            } else {
                // Hide - MUST use !important to override bootstrap d-block !important
                cards[i].style.setProperty('display', 'none', 'important');
            }
        }
    }
    console.log('[Axion] Filter complete. Visible:', visibleCount);
}
