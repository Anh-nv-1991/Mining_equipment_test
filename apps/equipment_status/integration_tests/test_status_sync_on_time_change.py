import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth.models import User

# Giả sử bạn có factory cho EquipmentStatus và Equipment
from apps.maintenance.test_factories.maintenance_factories import EquipmentStatusFactory


@pytest.mark.django_db
def test_get_equipment_status():
    """
    Test endpoint GET /status/<equipment_id>/ của EquipmentStatusViewSet.
    Endpoint này trả về thông tin EquipmentStatus, bao gồm:
      - name (từ equipment.name)
      - machine_type (từ equipment.category.name)
      - management_unit (từ equipment.management_unit.name)
      - engine_hours (từ equipment.engine_hours)
      - maintenance_records (danh sách id của maintenance_records)
      - updated_at (timestamp cập nhật)
    """
    # Tạo user để xác thực
    user = User.objects.create_user(username="testuser", password="password")
    # Tạo EquipmentStatus mẫu bằng factory (factory này cũng tự tạo Equipment bên trong)
    equipment_status = EquipmentStatusFactory()

    client = APIClient()
    client.force_authenticate(user=user)

    # Reverse tên URL: theo cấu hình router trong apps/equipment_status/urls.py, basename là "equipment-status"
    # lookup_field được đặt là 'equipment_id'
    url = reverse("equipment_status:equipment-status-detail", kwargs={"equipment_id": equipment_status.equipment.id})
    response = client.get(url)
    data = response.json()

    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
    # Kiểm tra một số trường cần thiết có trong response
    assert "name" in data, "Response thiếu trường 'name'"
    assert "machine_type" in data, "Response thiếu trường 'machine_type'"
    assert "management_unit" in data, "Response thiếu trường 'management_unit'"
    assert "engine_hours" in data, "Response thiếu trường 'engine_hours'"
    assert "maintenance_records" in data, "Response thiếu trường 'maintenance_records'"
    assert "updated_at" in data, "Response thiếu trường 'updated_at'"
