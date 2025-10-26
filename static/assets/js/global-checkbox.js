document.addEventListener("DOMContentLoaded", function () {
    // Universal CSRF helper
    function getCSRFToken() {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.startsWith("csrftoken=")) {
                    cookieValue = decodeURIComponent(cookie.substring("csrftoken=".length));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Apply checkbox + delete logic to all tables that follow naming convention
    document.querySelectorAll("[id^='markAll']").forEach(function (markAll) {
        const table = markAll.closest("table") || document;
        const checkboxes = table.querySelectorAll(".row-checkbox");
        const deleteBtn = document.querySelector("#deleteSelectedBtn");

        if (!checkboxes.length) return;

        // Select / deselect all rows
        markAll.addEventListener("change", function () {
            checkboxes.forEach(cb => cb.checked = markAll.checked);
            toggleDeleteButton();
        });

        // Update master checkbox and button visibility
        checkboxes.forEach(cb => cb.addEventListener("change", toggleDeleteButton));

        function toggleDeleteButton() {
            const anyChecked = Array.from(checkboxes).some(cb => cb.checked);
            if (deleteBtn) deleteBtn.style.display = anyChecked ? "inline-block" : "none";
        }

        // ✅ Handle Global Delete
            deleteBtn.addEventListener("click", function () {
    const deleteUrl = deleteBtn.dataset.deleteUrl;
    const selectedIds = Array.from(checkboxes)
        .filter(cb => cb.checked)
        .map(cb => parseInt(cb.value));

    if (selectedIds.length === 0) return;

    if (typeof Swal !== "undefined") {
        Swal.fire({
            title: "Delete Payslips",
            html: `You are about to delete <b>${selectedIds.length}</b> record(s).`,
            icon: "warning",
            showCancelButton: true,
            showDenyButton: true,   // extra button
            confirmButtonText: "Move to Trash",
            denyButtonText: "Delete Permanently",
            cancelButtonText: "Cancel",
        }).then(result => {
            if (result.isConfirmed) {
                sendDeleteRequest(deleteUrl, selectedIds, 'soft');
            } else if (result.isDenied) {
                sendDeleteRequest(deleteUrl, selectedIds, 'hard');
            }
        });
    } else if (confirm("Are you sure you want to delete selected items?")) {
        sendDeleteRequest(deleteUrl, selectedIds, 'soft');
    }
});

function sendDeleteRequest(url, ids, type) {
    fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify({ ids: ids, type: type }),
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            if (typeof Swal !== "undefined") {
                Swal.fire({
                    title: "Deleted!",
                    text: data.message,
                    icon: "success",
                    confirmButtonText: "OK",
                }).then(() => location.reload());
            } else {
                alert(data.message);
                location.reload();
            }
        } else {
            if (typeof Swal !== "undefined") {
                Swal.fire("Error", data.message, "error");
            } else {
                alert("Delete failed: " + data.message);
            }
        }
    })
    .catch(err => console.error("Delete failed", err));
}


    });
});












const markAll = document.getElementById('markAllPayslips');
const checkboxes = document.querySelectorAll('.row-checkbox');
const restoreBtn = document.getElementById('restoreSelectedBtn');
const deleteBtn = document.getElementById('deletePermanentlyBtn');

// Show buttons if any checkbox is selected
function toggleButtons() {
    const anyChecked = Array.from(checkboxes).some(c => c.checked);
    restoreBtn.style.display = anyChecked ? 'inline-block' : 'none';
    deleteBtn.style.display = anyChecked ? 'inline-block' : 'none';
}

// Mark all checkbox
markAll.addEventListener('change', () => {
    checkboxes.forEach(cb => cb.checked = markAll.checked);
    toggleButtons();
});

// Individual checkbox change
checkboxes.forEach(cb => cb.addEventListener('change', toggleButtons));

// Restore action
restoreBtn.addEventListener('click', () => {
    const selectedIds = Array.from(checkboxes).filter(c => c.checked).map(c => c.value);
    if (!selectedIds.length) return;

    fetch(restoreBtn.dataset.restoreUrl, {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'X-CSRFToken': '{{ csrf_token }}'},
        body: JSON.stringify({ids: selectedIds})
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);
        location.reload();
    });
});

// Permanent delete action
deleteBtn.addEventListener('click', () => {
    const selectedIds = Array.from(checkboxes).filter(c => c.checked).map(c => c.value);
    if (!selectedIds.length) return;

    if (typeof Swal !== "undefined") {
        Swal.fire({
            title: "Delete Permanently?",
            html: `You are about to permanently delete <b>${selectedIds.length}</b> record(s).`,
            icon: "warning",
            showCancelButton: true,
            confirmButtonColor: "#d33",
            cancelButtonColor: "#3085d6",
            confirmButtonText: "Yes, Delete Permanently"
        }).then(result => {
            if (result.isConfirmed) sendDeleteRequest(deleteBtn.dataset.deleteUrl, selectedIds, 'hard');
        });
    } else if (confirm("Delete permanently?")) {
        sendDeleteRequest(deleteBtn.dataset.deleteUrl, selectedIds, 'hard');
    }
});

// Send delete request function
function sendDeleteRequest(url, ids, type) {
    fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'X-CSRFToken': '{{ csrf_token }}'},
        body: JSON.stringify({ids: ids, type: type})
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);
        location.reload();
    })
    .catch(err => console.error(err));
}