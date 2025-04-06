import pytest
from apps.maintenance.serializers import MaintenanceRecordSerializer, ModalMaintenanceTaskSerializer
from apps.maintenance.test_factories.maintenance_factories import (
    MaintenanceRecordFactory,
    MaintenanceTaskFactory,
    ReplacementResultFactory
)


@pytest.mark.django_db
def test_maintenance_record_serializer():
    """
    Test MaintenanceRecordSerializer:
      - Tạo một bản ghi bảo dưỡng mẫu bằng factory.
      - Kiểm tra rằng dữ liệu serialize chứa các trường cần thiết.
    """
    record = MaintenanceRecordFactory()
    serializer = MaintenanceRecordSerializer(record)
    data = serializer.data

    # Các trường mong đợi (theo cấu trúc của serializer)
    expected_fields = [
        "id",
        "equipment",  # Thông tin thiết bị (theo cách serialize, đây có thể là tên thiết bị)
        "category",  # Tên category
        "maintenance_level",
        "start_time",
        "end_time",
    ]

    for field in expected_fields:
        assert field in data, f"Thiếu trường '{field}' trong output của MaintenanceRecordSerializer"


@pytest.mark.django_db
def test_modal_maintenance_task_serializer():
    """
    Test ModalMaintenanceTaskSerializer:
      - Tạo một task bảo dưỡng mẫu và gắn kết một ReplacementResult.
      - Kiểm tra rằng dữ liệu serialize trả về đầy đủ các trường, bao gồm nested data như notes.
    """
    task = MaintenanceTaskFactory()
    # Tạo kết quả cho task; không truyền 'completed' vì model không có trường đó
    ReplacementResultFactory(task=task, actual_quantity=task.quantity, notes="Task completed")

    serializer = ModalMaintenanceTaskSerializer(task)
    data = serializer.data

    expected_fields = [
        "id",
        "task_type",
        "task_name",
        "position",
        "quantity",
        "replacement_type",
        "manufacturer_id",
        "alternative_id",
        "actual_quantity",
        "completed",  # Serializer sẽ trả về giá trị từ supplement_result nếu có, hoặc False
        "condition",
        "check_inventory",
        "notes",
    ]
    for field in expected_fields:
        assert field in data, f"Thiếu trường '{field}' trong output của ModalMaintenanceTaskSerializer"
