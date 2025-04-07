document.addEventListener("DOMContentLoaded", function() {
    console.log(">>> equipment_status_modal_readonly.js: loaded!");

    const modal = document.getElementById("maintenanceReadonlyModal");
    const modalBody = document.getElementById("readonlyModalBody");
    const closeBtn = document.getElementById("closeReadonlyModal");

    // Debug: in ra xem modal, modalBody, closeBtn có tồn tại không
    console.log(">>> modal =", modal);
    console.log(">>> modalBody =", modalBody);
    console.log(">>> closeBtn =", closeBtn);

    // Đóng modal khi bấm nút X
    closeBtn?.addEventListener("click", () => {
        console.log(">>> closeBtn clicked => hide modal");
        if (modal) modal.style.display = "none";
    });

    // Đóng modal khi click ra ngoài modal content
    window.addEventListener("click", e => {
        if (e.target === modal) {
            console.log(">>> click outside modal => hide modal");
            modal.style.display = "none";
        }
    });

    // SỬ DỤNG EVENT DELEGATION: lắng nghe click trên document
    document.addEventListener("click", function(e) {
        console.log(">>> document clicked on:", e.target);

        // Tìm phần tử (hoặc cha) có class .open-readonly-modal
        const link = e.target.closest(".open-readonly-modal");
        console.log(">>> found link?", link);
        if (!link) return;  // nếu click không phải link => bỏ qua

        e.preventDefault();

        // Lấy data-modal-url
        const url = link.dataset.modalUrl;
        console.log(">>> open-readonly-modal clicked, url =", url);

        // Kiểm tra modal
        if (!modal) {
            console.error(">>> No modal element found in DOM");
            return;
        }
        // Hiển thị modal
        modal.style.display = "block";
        modalBody.innerHTML = "<p>Đang tải dữ liệu…</p>";

        // Fetch nội dung read-only
        fetch(url)
            .then(resp => {
                console.log(">>> fetch response status =", resp.status);
                if (!resp.ok) throw new Error(`HTTP error! status: ${resp.status}`);
                return resp.text();
            })
            .then(html => {
                console.log(">>> fetch success, length =", html.length);
                modalBody.innerHTML = html;
            })
            .catch(err => {
                console.error(">>> Error fetching read-only modal:", err);
                modalBody.innerHTML = "<p style='color:red;'>Không thể tải dữ liệu.</p>";
            });
    });
});
