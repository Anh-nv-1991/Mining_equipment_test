import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from apps.maintenance.test_factories.maintenance_factories import MaintenanceRecordFactory

# ----- Test POST /records/<id>/complete/ edge cases -----
@pytest.mark.django_db
def test_post_complete_record_nonexistent():
    """
    Nếu record không tồn tại, POST /records/<id>/complete/ trả về 404.
    """
    user = User.objects.create_user(username="edgeuser", password="password")
    client = APIClient()
    client.force_authenticate(user=user)
    url = reverse("maintenance:maintenance-record-complete", kwargs={"pk": 999999})
    response = client.post(url)
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"

@pytest.mark.django_db
def test_post_complete_record_unauthenticated():
    """
    Nếu không xác thực, POST /records/<id>/complete/ trả về 401 hoặc 403.
    """
    record = MaintenanceRecordFactory()
    client = APIClient()
    url = reverse("maintenance:maintenance-record-complete", kwargs={"pk": record.id})
    response = client.post(url)
    assert response.status_code in (401, 403), f"Expected 401 or 403, got {response.status_code}"

# ----- Test GET /records/<id>/tasks/ edge cases -----
@pytest.mark.django_db
def test_get_record_tasks_no_tasks():
    """
    Nếu record không có task nào, GET /records/<id>/tasks/ trả về danh sách rỗng.
    """
    user = User.objects.create_user(username="edgeuser2", password="password")
    record = MaintenanceRecordFactory(created_by=user)
    client = APIClient()
    client.force_authenticate(user=user)
    url = reverse("maintenance:maintenance-record-tasks", kwargs={"pk": record.id})
    response = client.get(url)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "replacement_tasks" in data, "Response thiếu key 'replacement_tasks'"
    assert isinstance(data["replacement_tasks"], list), "'replacement_tasks' phải là list"
    assert len(data["replacement_tasks"]) == 0, "Expected no tasks for record without tasks"

@pytest.mark.django_db
def test_get_record_tasks_invalid_record():
    """
    Khi record không tồn tại, GET /records/<id>/tasks/ trả về 404.
    """
    user = User.objects.create_user(username="edgeuser3", password="password")
    client = APIClient()
    client.force_authenticate(user=user)
    url = reverse("maintenance:maintenance-record-tasks", kwargs={"pk": 999999})
    response = client.get(url)
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"

# ----- Test GET /status/<equipment_id>/ edge cases -----
@pytest.mark.django_db
def test_get_equipment_status_no_status():
    """
    Nếu không tìm thấy EquipmentStatus cho equipment, trả về 404 hoặc dữ liệu rỗng.
    """
    user = User.objects.create_user(username="edgeuser4", password="password")
    client = APIClient()
    client.force_authenticate(user=user)
    url = reverse("equipment_status:equipment-status-detail", kwargs={"equipment_id": 999999})
    response = client.get(url)
    assert response.status_code in (404, 200), f"Expected 404 or 200, got {response.status_code}"
    if response.status_code == 200:
        data = response.json()
        assert data == {}, "Expected empty response data when no EquipmentStatus found"

@pytest.mark.django_db
def test_get_equipment_status_unauthenticated():
    """
    Nếu không xác thực user, GET /status/<equipment_id>/ trả về 401 hoặc 403.
    """
    from apps.equipment_status.test_factories.factories import EquipmentStatusFactory
    equipment_status = EquipmentStatusFactory()
    client = APIClient()
    url = reverse("equipment_status:equipment-status-detail", kwargs={"equipment_id": equipment_status.equipment.id})
    response = client.get(url)
    assert response.status_code in (401, 403), f"Expected 401 or 403, got {response.status_code}"
