// Helper: get CSRF token dynamically
function getCSRFToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith('csrftoken=')) {
                cookieValue = decodeURIComponent(cookie.substring('csrftoken='.length));
                break;
            }
        }
    }
    return cookieValue;
}

// Initialize any table with checkboxes and action buttons
function initTableActions(options) {
    const tableSelector = options.tableSelector;
    const markAllSelector = options.markAllSelector || 'input.mark-all';
    const rowCheckboxSelector = options.rowCheckboxSelector || 'input.row-checkbox';
    const restoreBtnSelector = options.restoreBtnSelector; // optional
    const deleteBtnSelector = options.deleteBtnSelector; // optional

    const table = document.querySelector(tableSelector);
    if (!table) return;

    const markAll = table.querySelector(markAllSelector);
    const checkboxes = table.querySelectorAll(rowCheckboxSelector);
    const restoreBtn = restoreBtnSelector ? document.querySelector(restoreBtnSelector) : null;
    const deleteBtn = deleteBtnSelector ? document.querySelector(deleteBtnSelector) : null;

    if (!markAll || !checkboxes.length) return;

    function toggleButtons() {
        const anyChecked = Array.from(checkboxes).some(cb => cb.checked);
        if (restoreBtn) restoreBtn.style.display = anyChecked ? 'inline-block' : 'none';
        if (deleteBtn) deleteBtn.style.display = anyChecked ? 'inline-block' : 'none';
    }

    // Mark all checkbox
    markAll.addEventListener('change', () => {
        checkboxes.forEach(cb => cb.checked = markAll.checked);
        toggleButtons();
    });

    // Individual checkbox
    checkboxes.forEach(cb => cb.addEventListener('change', toggleButtons));

    // Restore button action
    if (restoreBtn) {
        restoreBtn.addEventListener('click', () => {
            const selectedIds = Array.from(checkboxes)
                .filter(cb => cb.checked)
                .map(cb => cb.value);
            if (!selectedIds.length) return;

            fetch(restoreBtn.dataset.restoreUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ids: selectedIds})
            })
            .then(res => res.json())
            .then(data => {
                alert(data.message);
                location.reload();
            })
            .catch(err => console.error(err));
        });
    }

    // Delete button action (soft/hard)
    if (deleteBtn) {
        deleteBtn.addEventListener('click', () => {
            const selectedIds = Array.from(checkboxes)
                .filter(cb => cb.checked)
                .map(cb => cb.value);
            if (!selectedIds.length) return;

            const deleteType = deleteBtn.dataset.type || 'hard'; // default to hard

            const sendDelete = () => {
                fetch(deleteBtn.dataset.deleteUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    },
                    body: JSON.stringify({ids: selectedIds, type: deleteType})
                })
                .then(res => res.json())
                .then(data => {
                    alert(data.message);
                    location.reload();
                })
                .catch(err => console.error(err));
            };

            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    title: deleteType === 'hard' ? "Delete Permanently?" : "Move to Trash?",
                    html: `You are about to ${deleteType === 'hard' ? 'permanently delete' : 'move to trash'} <b>${selectedIds.length}</b> record(s).`,
                    icon: "warning",
                    showCancelButton: true,
                    confirmButtonColor: "#d33",
                    cancelButtonColor: "#3085d6",
                    confirmButtonText: deleteType === 'hard' ? "Yes, Delete Permanently" : "Yes, Move to Trash"
                }).then(result => {
                    if (result.isConfirmed) sendDelete();
                });
            } else {
                if (confirm(`Are you sure you want to ${deleteType === 'hard' ? 'permanently delete' : 'move to trash'} selected items?`)) {
                    sendDelete();
                }
            }
        });
    }
}

// Auto-init tables on page load
document.addEventListener('DOMContentLoaded', () => {
    // Example initialization:
    // initTableActions({tableSelector: '#payslipTable', restoreBtnSelector: '#restoreSelectedBtn', deleteBtnSelector: '#deletePermanentlyBtn'});
});
