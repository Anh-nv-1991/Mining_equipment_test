document.addEventListener("DOMContentLoaded", function () {
    const historyModal = document.getElementById("history-modal");
    const closeHistoryBtn = document.getElementById("close-history-modal");
    const historyRecordInfo = document.getElementById("history-record-info");
    const historyContent = document.getElementById("history-content");

    function openHistoryModal(recordId) {
        fetch(`/api/v1/maintenance/records/${recordId}/history/`)
            .then(res => {
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                return res.json();
            })
            .then(data => {
                console.log("🔥 History API payload:", data);
                renderHistoryModal(data);
                historyModal.style.display = "block";
            })
            .catch(err => alert("Could not fetch history data! " + err.message));
    }

    document.querySelectorAll(".open-history-modal").forEach(btn => {
        btn.addEventListener("click", e => {
            e.preventDefault();
            openHistoryModal(btn.dataset.recordId);
        });
    });

    closeHistoryBtn?.addEventListener("click", () => historyModal.style.display = "none");

    function renderHistoryModal(data) {
    const info = data.record_info || {};
    historyRecordInfo.innerHTML = `
      <p><strong>Created By:</strong> ${info.created_by}</p>
      <p><strong>Start Time:</strong> ${info.start_time}</p>
      <p><strong>End Time:</strong> ${info.end_time}</p>
      <p><strong>Maintenance Level:</strong> ${info.maintenance_level}</p>
    `;

    let html = `<table class="history-table"><thead>
      <tr><th>Updated By</th><th>Updated At</th><th>Change Details</th></tr>
    </thead><tbody>`;

    if (!Array.isArray(data.history) || !data.history.length) {
        html += `<tr><td colspan="3">No history found</td></tr>`;
    } else {
        data.history.forEach(h => {
            const details = h.changes.map(c => {
                return `<li><strong>Task ID ${c.task_id}</strong>: ${Object.entries(c.changed_fields)
                  .map(([f,d]) => `${f}: ${d.old} → ${d.new}`)
                  .join("; ")}</li>`;
            }).join("");
            html += `<tr><td>${h.updated_by}</td><td>${h.updated_at}</td><td><ul>${details}</ul></td></tr>`;
        });
    }
    html += `</tbody></table>`;
    historyContent.innerHTML = html;
}
});
