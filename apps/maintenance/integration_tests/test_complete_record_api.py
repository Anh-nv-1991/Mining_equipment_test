import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from django.utils import timezone
from apps.maintenance.test_factories.maintenance_factories import MaintenanceRecordFactory, \
    CompletedMaintenanceRecordFactory
from apps.maintenance.models import CompletedMaintenanceRecord


@pytest.mark.django_db
def test_post_complete_record_api():
    """
    Test POST /records/<id>/complete/ endpoint.
    Khi gọi endpoint này:
      - Record.end_time được cập nhật.
      - Một CompletedMaintenanceRecord được tạo với completed_at khớp với record.end_time.
      - Response trả về chứa thông tin file (nếu có).
    """
    # Tạo user mẫu
    user = User.objects.create_user(username="testuser", password="password")

    # Tạo một MaintenanceRecord mẫu (end_time ban đầu là None)
    record = MaintenanceRecordFactory(created_by=user, end_time=None)

    client = APIClient()
    client.force_authenticate(user=user)

    # Reverse URL: theo cấu hình router và namespace của app maintenance, ví dụ: "maintenance-record-complete"
    url = reverse("maintenance:maintenance-record-complete", kwargs={"pk": record.id})

    response = client.post(url)

    assert response.status_code in (200, 201), f"Unexpected status code: {response.status_code}"

    data = response.json()
    # Kiểm tra key 'file' có trong response, nếu thiết kế trả về file path
    assert "file" in data, "Response không chứa key 'file'"

    # Reload record từ DB để xác nhận rằng end_time đã được cập nhật
    record.refresh_from_db()
    assert record.end_time is not None, "Record.end_time chưa được cập nhật sau khi complete"

    # Kiểm tra CompletedMaintenanceRecord được tạo và trường completed_at khớp với record.end_time
    comp_record = CompletedMaintenanceRecord.objects.filter(maintenance_record=record).first()
    assert comp_record is not None, "Không tạo ra CompletedMaintenanceRecord cho record"
    assert comp_record.completed_at == record.end_time, (
        f"Expected comp_record.completed_at ({comp_record.completed_at}) to equal record.end_time ({record.end_time})"
    )
