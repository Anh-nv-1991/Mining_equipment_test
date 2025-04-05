import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.utils import timezone
from django.contrib.auth.models import User

from apps.maintenance.models import MaintenanceRecord, CompletedMaintenanceRecord
from apps.maintenance.test_factories.maintenance_factories import MaintenanceRecordFactory, MaintenanceTaskFactory

@pytest.mark.django_db
def test_complete_record_integration():
    # Tạo user để xác thực
    user = User.objects.create_user(username="testuser", password="password")

    # Tạo một MaintenanceRecord mẫu
    record = MaintenanceRecordFactory(created_by=user)

    # Tạo một MaintenanceTask mẫu cho record (giả sử task thuộc kiểu replacement)
    task = MaintenanceTaskFactory(maintenance_record=record)

    # Khởi tạo APIClient và xác thực user
    client = APIClient()
    client.force_authenticate(user=user)

    # Gọi endpoint "complete" của MaintenanceRecordViewSet.
    url = reverse("maintenance:maintenance-record-complete", kwargs={"pk": record.id})
    response = client.post(url)

    # Kiểm tra response thành công
    assert response.status_code == 200, f"Response status code: {response.status_code}"
    data = response.json()
    assert data.get("success") is True, f"Response data: {data}"
    assert "file" in data, "File path should be returned in response"

    # Refresh record và kiểm tra rằng end_time đã được cập nhật
    record.refresh_from_db()
    assert record.end_time is not None, "MaintenanceRecord.end_time should be set upon completion"

    # Kiểm tra rằng CompletedMaintenanceRecord đã được tạo cho record
    comp_record = CompletedMaintenanceRecord.objects.filter(maintenance_record=record).first()
    assert comp_record is not None, "CompletedMaintenanceRecord should exist for the completed record"

    # Kiểm tra rằng completed_at của CompletedMaintenanceRecord trùng với record.end_time
    assert comp_record.completed_at == record.end_time, (
        "completed_at in CompletedMaintenanceRecord should match MaintenanceRecord.end_time"
    )

    # Kiểm tra snapshot tasks đã được lưu (dạng JSON snapshot)
    assert comp_record.tasks is not None, "Tasks snapshot should not be None"
