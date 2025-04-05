import pytest
from apps.maintenance.test_factories.maintenance_factories import MaintenanceRecordFactory

@pytest.mark.django_db
def test_create_maintenance_record():
    record = MaintenanceRecordFactory()
    assert record.id is not None
