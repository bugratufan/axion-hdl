/**
 * Axion-HDL GUI - Source Viewer Module
 */

let editor;
let isEditing = false;
let hasUnsavedChanges = false;
let originalContent = '';

document.addEventListener('DOMContentLoaded', function () {
    initializeEditor();
});

function initializeEditor() {
    const textArea = document.getElementById('sourceCode');
    if (!textArea) return;

    // Determine mode based on file extension
    const filePath = document.querySelector('.file-path').innerText;
    let mode = 'text/plain';

    if (filePath.endsWith('.vhd') || filePath.endsWith('.vhdl')) {
        mode = 'vhdl';
    } else if (filePath.endsWith('.json')) {
        mode = 'application/json';
    } else if (filePath.endsWith('.yaml') || filePath.endsWith('.yml')) {
        mode = 'yaml';
    } else if (filePath.endsWith('.xml')) {
        mode = 'xml';
    } else if (filePath.endsWith('.js')) {
        mode = 'javascript';
    } else if (filePath.endsWith('.py')) {
        mode = 'python';
    }

    // Initialize CodeMirror
    editor = CodeMirror.fromTextArea(textArea, {
        lineNumbers: true,
        theme: 'monokai',
        mode: mode,
        readOnly: 'nocursor', // Start in read-only mode
        viewportMargin: Infinity,
        lineWrapping: true,
        styleActiveLine: true,
        matchBrackets: true
    });

    originalContent = editor.getValue();

    // Change listener
    editor.on('change', function () {
        if (!isEditing) return;

        if (editor.getValue() !== originalContent) {
            hasUnsavedChanges = true;
            document.getElementById('saveBtn').disabled = false;
            updateUnsavedBadge();
        } else {
            hasUnsavedChanges = false;
            document.getElementById('saveBtn').disabled = true;
            updateUnsavedBadge();
        }
    });
}

function toggleEdit() {
    isEditing = !isEditing;
    const btn = document.getElementById('editBtn');

    if (isEditing) {
        editor.setOption('readOnly', false);
        btn.classList.add('active');
        btn.innerHTML = '<i class="bi bi-x-lg me-1"></i>Cancel';
        document.getElementById('saveBtn').disabled = !hasUnsavedChanges;
    } else {
        if (hasUnsavedChanges) {
            if (!confirm('Discard unsaved changes?')) {
                isEditing = true;
                return;
            }
        }
        // Revert content
        editor.setValue(originalContent);
        editor.setOption('readOnly', 'nocursor');
        btn.classList.remove('active');
        btn.innerHTML = '<i class="bi bi-pencil me-1"></i>Edit';
        hasUnsavedChanges = false;
        document.getElementById('saveBtn').disabled = true;
        updateUnsavedBadge();
    }
}

function updateUnsavedBadge() {
    const badge = document.getElementById('unsavedBadge');
    if (hasUnsavedChanges) {
        badge.classList.add('visible');
    } else {
        badge.classList.remove('visible');
    }
}

async function saveFile() {
    const saveBtn = document.getElementById('saveBtn');
    const status = document.getElementById('saveStatus');
    const filePath = document.querySelector('.file-path').getAttribute('title'); // Use title for full path in case text is truncated

    try {
        status.style.display = 'flex';
        status.className = 'save-status saving';
        status.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving...';
        saveBtn.disabled = true;

        const response = await fetch('/api/source/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                filepath: filePath,
                content: editor.getValue()
            })
        });

        const result = await response.json();

        if (result.success) {
            status.className = 'save-status success';
            status.innerHTML = '<i class="bi bi-check-circle-fill"></i> Saved!';
            originalContent = editor.getValue();
            hasUnsavedChanges = false;
            updateUnsavedBadge();

            // Exit edit mode on save? No, let user continue editing if they want.
            // But we should re-enable save button only if changes happen again.

            setTimeout(() => {
                status.style.display = 'none';
            }, 2000);
        } else {
            throw new Error(result.error || 'Save failed');
        }
    } catch (error) {
        status.className = 'save-status error';
        status.innerHTML = '<i class="bi bi-exclamation-triangle-fill"></i> ' + error.message;
        saveBtn.disabled = false;
        setTimeout(() => {
            status.style.display = 'none';
        }, 4000);
    }
}

// Ctrl+S shortcut
document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        if (isEditing) saveFile();
    }
});

// Warn before leaving
window.addEventListener('beforeunload', function (e) {
    if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = 'Unsaved changes will be lost.';
        return e.returnValue;
    }
});

// Handle window resize
window.addEventListener('resize', () => {
    if (editor) editor.refresh();
});
