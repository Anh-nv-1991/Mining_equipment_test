import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from apps.maintenance.test_factories.maintenance_factories import (
    MaintenanceRecordFactory,
    MaintenanceTaskFactory,
    ReplacementResultFactory
)


@pytest.mark.django_db
def test_get_record_tasks_api():
    """
    Test endpoint GET /records/<id>/tasks/:
    Kiểm tra response trả về danh sách tasks cho một record bảo dưỡng.
    """
    user = User.objects.create_user(username="testuser", password="password")
    record = MaintenanceRecordFactory(created_by=user)

    task = MaintenanceTaskFactory(maintenance_record=record)
    # Không truyền tham số 'completed' nữa vì model không có trường đó
    ReplacementResultFactory(task=task, actual_quantity=task.quantity, notes="Task completed")

    client = APIClient()
    client.force_authenticate(user=user)

    # Giả sử endpoint GET /records/<id>/tasks/ được định danh là "maintenance-record-tasks"
    url = reverse("maintenance:maintenance-record-tasks", kwargs={"pk": record.id})
    response = client.get(url)
    data = response.json()

    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    assert "replacement_tasks" in data, "Response thiếu trường 'replacement_tasks'"
    assert isinstance(data["replacement_tasks"], list), "replacement_tasks phải là danh sách"
    assert len(data["replacement_tasks"]) > 0, "Không có task nào được trả về"
    task_data = data["replacement_tasks"][0]
    assert "task_name" in task_data, "Task không chứa trường 'task_name'"
    assert "notes" in task_data, "Task không chứa trường 'notes'"
