/**
 * Axion-HDL GUI - Diff Module
 * Diff view logic
 */

    function showUnified() {
        document.getElementById('diff-unified').style.display = 'block';
        document.getElementById('diff-split').classList.remove('active');
        document.getElementById('btn-unified').classList.add('active');
        document.getElementById('btn-split').classList.remove('active');
    }

    function showSplit() {
        document.getElementById('diff-unified').style.display = 'none';
        document.getElementById('diff-split').classList.add('active');
        document.getElementById('btn-unified').classList.remove('active');
        document.getElementById('btn-split').classList.add('active');
    }
