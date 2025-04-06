import pytest
from apps.equipment_status.serializers import EquipmentStatusSerializer
from apps.equipment_status.test_factories.factories import EquipmentStatusFactory

@pytest.mark.django_db
def test_equipment_status_serializer_fields():
    # Tạo một instance EquipmentStatus bằng factory
    status = EquipmentStatusFactory()
    serializer = EquipmentStatusSerializer(status)
    data = serializer.data

    # Các trường mong đợi (tùy vào cấu hình serializer của bạn)
    expected_fields = [
        "name",             # Tên thiết bị (được lấy từ equipment.name)
        "machine_type",     # Loại máy (từ equipment.category.name)
        "management_unit",  # Đơn vị quản lý (từ equipment.management_unit.name)
        "engine_hours",     # Giờ hoạt động (từ equipment.engine_hours)
        "maintenance_records",  # Danh sách id của maintenance_records liên quan
        "updated_at"        # Thời gian cập nhật trạng thái
    ]

    for field in expected_fields:
        assert field in data, f"Thiếu trường '{field}' trong dữ liệu serialized"
