import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from apps.equipment_status.test_factories.factories import EquipmentStatusFactory


@pytest.mark.django_db
def test_get_equipment_status_api():
    """
    Test endpoint GET /status/<equipment_id>/:
      - Kiểm tra response trả về thông tin EquipmentStatus
      - Các trường: name, machine_type, management_unit, engine_hours, maintenance_records, updated_at
    """
    # Tạo user mẫu để xác thực
    user = User.objects.create_user(username="testuser", password="password")
    # Tạo EquipmentStatus mẫu thông qua factory (factory này tạo luôn equipment liên quan)
    equipment_status = EquipmentStatusFactory()

    client = APIClient()
    client.force_authenticate(user=user)

    # Giả sử viewset của EquipmentStatus đăng ký với router và lookup_field là 'equipment_id'
    # Và tên route là "equipment-status-detail" trong namespace "equipment_status"
    url = reverse("equipment_status:equipment-status-detail", kwargs={"equipment_id": equipment_status.equipment.id})
    response = client.get(url)
    data = response.json()

    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"

    # Kiểm tra một số trường chính có trong response
    assert "name" in data, "Response thiếu trường 'name'"
    assert "machine_type" in data, "Response thiếu trường 'machine_type'"
    assert "management_unit" in data, "Response thiếu trường 'management_unit'"
    assert "engine_hours" in data, "Response thiếu trường 'engine_hours'"
    assert "maintenance_records" in data, "Response thiếu trường 'maintenance_records'"
    assert "updated_at" in data, "Response thiếu trường 'updated_at'"
