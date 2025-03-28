console.log("✅ DEBUG: adjust_fields.js đang chạy!");

document.addEventListener("DOMContentLoaded", function () {
    function adjustFieldSizes() {
        let locationField = document.querySelector("#id_location");
        let responsibleUnitsField = document.querySelector("#id_responsible_units");

        if (locationField) {
            locationField.style.width = "300px";  // 🔹 Giới hạn chiều rộng
        }
        if (responsibleUnitsField) {
            responsibleUnitsField.style.width = "300px";  // 🔹 Giới hạn chiều rộng
            responsibleUnitsField.style.height = "30px";  // 🔹 Giới hạn chiều cao
        }
        console.log("✅ DEBUG: Đã điều chỉnh kích thước input và textarea!");
    }

    adjustFieldSizes(); // Gọi ngay khi DOM đã sẵn sàng
});
