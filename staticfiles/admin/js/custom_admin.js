document.addEventListener("DOMContentLoaded", function() {
    let categoryField = document.querySelector("#id_category");
    let equipmentField = document.querySelector("#id_equipment");

    if (categoryField && equipmentField) {
        categoryField.addEventListener("change", function() {
            let categoryId = categoryField.value;
            console.log("🔹 DEBUG: Chọn loại máy - ID =", categoryId);

            if (categoryId) {
                fetch(`/maintenance/get_equipment_by_category/?category_id=${categoryId}`)
                    .then(response => response.json())
                    .then(data => {
                        console.log("🔹 DEBUG: Danh sách thiết bị nhận được:", data);
                        equipmentField.innerHTML = "";

                        let emptyOption = document.createElement("option");
                        emptyOption.value = "";
                        emptyOption.textContent = "---------";
                        equipmentField.appendChild(emptyOption);

                        data.equipments.forEach(function(equip) {
                            let option = document.createElement("option");
                            option.value = equip.id;
                            option.textContent = equip.name;
                            equipmentField.appendChild(option);
                        });
                    })
                    .catch(error => console.error("🔴 DEBUG: Lỗi khi tải danh sách thiết bị!", error));
            } else {
                equipmentField.innerHTML = "<option value=''>---------</option>";
            }
        });
    }

});
