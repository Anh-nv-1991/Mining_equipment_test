import pytest
from django.utils import timezone

from ..test_factories.maintenance_factories import (
    EquipmentFactory,
    MaintenanceRecordFactory,
    MaintenanceTaskFactory,
    CompletedMaintenanceRecordFactory,
    EquipmentStatusFactory,
)


@pytest.mark.django_db
def test_equipment_factory():
    equipment = EquipmentFactory()
    assert equipment.name.startswith("Equipment")
    assert equipment.category is not None
    assert equipment.management_unit is not None
    # Kiểm tra giá trị mặc định của engine_hours
    assert equipment.engine_hours == 1000

@pytest.mark.django_db
def test_maintenance_record_factory():
    record = MaintenanceRecordFactory()
    # Kiểm tra rằng record có equipment và category được tạo từ factory
    assert record.equipment is not None
    assert record.category is not None
    # Kiểm tra start_time được set
    assert record.start_time <= timezone.now()

@pytest.mark.django_db
def test_maintenance_task_factory():
    task = MaintenanceTaskFactory()
    # Kiểm tra rằng task có maintenance_record và template (ReplacementTemplate)
    assert task.maintenance_record is not None
    assert hasattr(task.template, "replacement_type")
    # Kiểm tra số lượng
    assert task.quantity == 1

@pytest.mark.django_db
def test_completed_record_factory():
    comp_record = CompletedMaintenanceRecordFactory()
    # Kiểm tra rằng completed_record liên kết với MaintenanceRecord
    assert comp_record.maintenance_record is not None
    # Kiểm tra rằng trường notes có giá trị mặc định
    assert comp_record.notes == "Test Completed Record"

@pytest.mark.django_db
def test_equipment_status_factory():
    status = EquipmentStatusFactory()
    # Kiểm tra rằng equipment status liên kết với Equipment
    assert status.equipment is not None
    # Kiểm tra giá trị của operation_team
    assert status.operation_team == "Team A"
