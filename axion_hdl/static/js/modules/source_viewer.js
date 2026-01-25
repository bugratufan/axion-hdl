/**
 * Axion-HDL GUI - Source Viewer Module
 */


            if (result.success) {
                status.className = 'save-status success';
                status.innerHTML = '<i class="bi bi-check-circle"></i> Saved!';
                originalContent = editor.getValue();
                hasUnsavedChanges = false;
                updateUnsavedBadge();
                setTimeout(() => { status.className = 'save-status'; }, 2000);
            } else {
                throw new Error(result.error || 'Save failed');
            }
        } catch (error) {
            status.className = 'save-status error';
            status.innerHTML = '<i class="bi bi-exclamation-triangle"></i> ' + error.message;
            saveBtn.disabled = false;
            setTimeout(() => { status.className = 'save-status'; }, 4000);
        }
    }

    // Ctrl+S shortcut
    document.addEventListener('keydown', function (e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            if (isEditing && hasUnsavedChanges) saveFile();
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
    window.addEventListener('resize', () => editor.refresh());
