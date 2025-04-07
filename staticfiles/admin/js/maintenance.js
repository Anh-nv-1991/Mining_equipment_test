document.addEventListener("DOMContentLoaded", function () {
    console.log("maintenance.js loaded");

    // Xử lý thay đổi danh mục và thiết bị
    const categoryField = document.querySelector("#id_category");
    const equipmentField = document.querySelector("#id_equipment");

    if (categoryField && equipmentField) {
        categoryField.addEventListener("change", () => {
            const categoryId = categoryField.value;
            if (!categoryId) {
                equipmentField.innerHTML = "<option value=''>---------</option>";
                return;
            }
            fetch(`/maintenance/get_equipment_by_category/?category_id=${categoryId}`)
                .then(r => r.json())
                .then(data => {
                    equipmentField.innerHTML = "<option value=''>---------</option>";
                    data.equipments.forEach(e => {
                        const opt = document.createElement("option");
                        opt.value = e.id;
                        opt.textContent = e.name;
                        equipmentField.appendChild(opt);
                    });
                })
                .catch(err => console.error("Error loading equipments:", err));
        });
    }

    // Modal nhập liệu bảo dưỡng
    const modal = document.getElementById("maintenance-modal");
    const closeModalBtn = document.getElementById("close-modal");
    const saveBtn = document.getElementById("save-maintenance");
    const tasksContainer = document.getElementById("tasks-container");
    const recordInfoContainer = document.getElementById("record-info");
    let currentRecordId = null;

    function renderRecordInfo(record) {
        recordInfoContainer.innerHTML = `
            <p><strong>Equipment:</strong> ${record.equipment}</p>
            <p><strong>Category:</strong> ${record.category}</p>
            <p><strong>Maintenance Level:</strong> ${record.maintenance_level}</p>
            <p><strong>Start Time:</strong> ${record.start_time}</p>
            <p><strong>Created By:</strong> ${record.created_by}</p>
        `;
    }

    // Hàm dựng table cho mỗi nhóm task
    function renderTable(title, type, headers, tasks, rowBuilder) {
        if (!tasks?.length) return "";
        let html = `<h3>${title}</h3><table class="task-table"><thead><tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr></thead><tbody>`;
        tasks.forEach((task, i) => {
            html += rowBuilder(task, i, type);
        });
        html += `</tbody></table>`;
        return html;
    }

    // Hàm mở modal: fetch dữ liệu từ endpoint GET /maintenance-record/{id}/tasks
    function openModal(recordId) {
        currentRecordId = recordId;
        fetch(`/api/v1/maintenance/records/${recordId}/tasks/`)
            .then(res => res.ok ? res.json() : Promise.reject(res.status))
            .then(data => {
                // Hiển thị info chung
                renderRecordInfo(data.record);

                let html = "";

                // --- Replacement Maintenance ---
                // BỎ cột Completed checkbox, THÊM cột Actual Qty (số)
                html += renderTable(
                    "Replacement Maintenance", "replacement",
                    [
                        "#", "Task Name", "Replacement Type", "Manufacturer ID",
                        "Alternative ID", "Planned Qty", "Actual Qty",
                        "Check Inventory", "Notes"
                    ],
                    data.replacement_tasks,
                    (task, i, ttype) => `
                    <tr data-task-id="${task.id}" data-task-type="${ttype}">
                        <td>${i + 1}</td>
                        <td>${task.task_name}</td>
                        <td>${task.replacement_type}</td>
                        <td>${task.manufacturer_id}</td>
                        <td>${task.alternative_id}</td>
                        <td>${task.quantity}</td> <!-- Số lượng planned -->
                        <td>
                            <input
                                type="number"
                                class="actual-quantity-input"
                                value="${task.actual_quantity || ''}"
                                style="width:70px;"
                            >
                        </td>
                        <td>${task.check_inventory}</td>
                        <td><input class="notes-input" value="${task.notes || ''}"></td>
                    </tr>`
                );

                // --- Supplement Maintenance ---
                // Vẫn dùng checkbox Completed
                html += renderTable(
                    "Supplement Maintenance", "supplement",
                    ["#","Position","Change_type", "Quantity", "Completed", "Notes"],
                    data.supplement_tasks,
                    (task, i, ttype) => `
                    <tr data-task-id="${task.id}" data-task-type="${ttype}">
                        <td>${i + 1}</td>
                        <td>${task.position || ''}</td>
                        <td>${task.task_name}</td>
                        <td>${task.quantity}</td>
                        <td><input type="checkbox" class="completed-checkbox" ${task.completed ? 'checked' : ''}></td>
                        <td><input class="notes-input" value="${task.notes || ''}"></td>
                    </tr>`
                );

                // --- Inspection Maintenance ---
                html += renderTable(
                    "Inspection Maintenance", "inspection",
                    ["#", "Task Name", "Condition", "Notes"],
                    data.inspection_tasks,
                    (task, i, ttype) => `
                    <tr data-task-id="${task.id}" data-task-type="${ttype}">
                        <td>${i + 1}</td>
                        <td>${task.task_name}</td>
                        <td><input class="condition-input" value="${task.condition || ''}"></td>
                        <td><input class="notes-input" value="${task.notes || ''}"></td>
                    </tr>`
                );

                // --- Cleaning Maintenance ---
                html += renderTable(
                    "Cleaning Maintenance", "cleaning",
                    ["#", "Task Name", "Condition", "Notes"],
                    data.cleaning_tasks,
                    (task, i, ttype) => `
                    <tr data-task-id="${task.id}" data-task-type="${ttype}">
                        <td>${i + 1}</td>
                        <td>${task.task_name}</td>
                        <td><input class="condition-input" value="${task.condition || ''}"></td>
                        <td><input class="notes-input" value="${task.notes || ''}"></td>
                    </tr>`
                );

                tasksContainer.innerHTML = html;
                modal.style.display = "block";
            })
            .catch(err => alert(`Error fetching tasks: ${err}`));
    }

    // Gán event listener cho tất cả các phần tử có class "open-modal"
    document.querySelectorAll(".open-modal").forEach(btn => {
        btn.addEventListener("click", e => {
            e.preventDefault();
            const recordId = btn.dataset.recordId;
            openModal(recordId);
        });
    });
    // Để window.openModal nếu cần gọi inline
    window.openModal = openModal;

    // Khi nhấn Save, thu thập dữ liệu từ các input và gửi POST
    saveBtn?.addEventListener("click", () => {
        const rows = tasksContainer.querySelectorAll("tr[data-task-id]");
        const results = Array.from(rows).map(row => {
            const taskType = row.dataset.taskType;
            const notes = row.querySelector(".notes-input")?.value || "";

            // Chuẩn bị biến cục bộ
            let actual_quantity = 0;
            let completed = false;
            let condition = "";

            if (taskType === "replacement") {
                // Replacement: dùng actual_quantity (int)
                actual_quantity = parseInt(row.querySelector(".actual-quantity-input")?.value || "0", 10);
            }
            else if (taskType === "supplement") {
                // Supplement: dùng completed (checkbox)
                completed = !!row.querySelector(".completed-checkbox")?.checked;
            }
            else if (taskType === "inspection" || taskType === "cleaning") {
                // Inspection/Cleaning: dùng condition
                condition = row.querySelector(".condition-input")?.value || "";
            }

            return {
                id: row.dataset.taskId,
                task_type: taskType,
                actual_quantity,
                completed,
                condition,
                notes
            };
        });

        console.log("Payload to POST:", results);
        fetch(`/api/v1/maintenance/records/${currentRecordId}/tasks/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify({ results })
        })
        .then(res => res.json())
        .then(data => data.success ? alert("Saved!") : alert("Save failed"))
        .catch(err => alert(`Error saving: ${err}`));
    });

    closeModalBtn?.addEventListener("click", () => {
        modal.style.display = "none";
    });

    // Khi bấm Complete, gọi endpoint complete để ghi snapshot
    document.querySelectorAll(".complete-btn").forEach(btn => {
        btn.addEventListener("click", function (e) {
            e.preventDefault();
            const recordId = btn.dataset.recordId;
            fetch(`/api/v1/maintenance/records/${recordId}/complete/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie("csrftoken")
                }
            })
            .then(res => {
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                return res.json();
            })
            .then(data => {
                if (data.file) {
                    alert(`✅ Completed! File created at:\n${data.file}`);
                } else {
                    alert("✅ Completed successfully (no file returned).");
                }
            })
            .catch(err => alert(`❌ Complete failed: ${err.message}`));
        });
    });

    function getCookie(name) {
        return document.cookie.split(";").reduce((v, c) => {
            const [k, val] = c.trim().split("=");
            return k === name ? decodeURIComponent(val) : v;
        }, null);
    }
});

// Nếu cần định nghĩa getCookie ở ngoài:
function getCookie(name) {
    return document.cookie.split(";").reduce((value, cookie) => {
        const [key, val] = cookie.trim().split("=");
        return key === name ? decodeURIComponent(val) : value;
    }, null);
}
