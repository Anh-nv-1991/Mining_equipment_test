from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.maintenance.models import (
    MaintenanceRecord, MaintenanceRecordHistory, CompletedMaintenanceRecord,
    generate_record_id,
)
from apps.equipment_management.models import Equipment, EquipmentCategories
from unittest.mock import patch, MagicMock
from datetime import datetime
from django.utils.timezone import now


class MaintenanceViewsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        User = get_user_model()
        self.user = User.objects.create_user(username="tester", password="test123")
        self.client.force_login(self.user)

        self.category = EquipmentCategories.objects.create(name="Excavator")
        self.equipment = Equipment.objects.create(name="Hitachi ZX", category=self.category)

        self.record = MaintenanceRecord.objects.create(
            equipment=self.equipment,
            category=self.category,
            start_time=datetime(2025, 4, 1, 8, 0),
            end_time="2025-04-01T10:00:00Z",
            maintenance_level=250,
            created_by=self.user
        )

        base = f"/api/v1/maintenance/records/{self.record.pk}"
        self.url_tasks = f"{base}/tasks/"
        self.url_readonly = f"{base}/readonly/"
        self.url_complete = f"{base}/complete/"
        self.url_history = f"{base}/history/"

    @patch("apps.maintenance.maintenance_helpers.get_grouped_data")
    def test_get_tasks(self, mock_grouped_data):
        mock_grouped_data.return_value = {
            "replacement_tasks": [],
            "supplement_tasks": [],
            "inspection_tasks": [],
            "cleaning_tasks": [],
        }
        response = self.client.get(self.url_tasks)
        self.assertEqual(response.status_code, 200)
        self.assertIn("replacement_tasks", response.data)

    @patch("apps.maintenance.models.MaintenanceRecordHistory.objects.get_or_create", return_value=(MagicMock(), True))
    @patch("apps.maintenance.models.ReplacementResult.objects.get_or_create", return_value=(MagicMock(), True))
    @patch("apps.maintenance.models.SupplementResult.objects.get_or_create", return_value=(MagicMock(), True))
    @patch("apps.maintenance.models.InspectionResult.objects.get_or_create", return_value=(MagicMock(), True))
    @patch("apps.maintenance.models.CleaningResult.objects.get_or_create", return_value=(MagicMock(), True))
    def test_post_results(self, mock_cleaning, mock_inspect, mock_supp, mock_repl, mock_hist):
        payload = {
            "results": [
                {"id": 1, "task_type": "replacement", "actual_quantity": 1},
                {"id": 2, "task_type": "supplement", "completed": True},
                {"id": 3, "task_type": "inspection", "condition": "Tốt"},
                {"id": 4, "task_type": "cleaning", "condition": "Sạch"}
            ]
        }
        response = self.client.post(self.url_tasks, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])

    @patch("apps.maintenance.maintenance_helpers.render_grouped_table", return_value="<html>OK</html>")
    def test_readonly_view(self, mock_render):
        CompletedMaintenanceRecord.objects.create(
            maintenance_record=self.record,
            notes="Đã xong",
            tasks={},
            completed_at=now()
        )
        response = self.client.get(self.url_readonly)
        self.assertEqual(response.status_code, 200)

        expected_id = generate_record_id(self.record)
        self.assertEqual(response.data["record_id"], expected_id)

    def test_history_view(self):
        MaintenanceRecordHistory.objects.create(
            record=self.record,
            updated_by=self.user,
            changes={"field": "value"},
        )
        response = self.client.get(self.url_history)
        self.assertEqual(response.status_code, 200)
        self.assertIn("history", response.data)
        self.assertIsInstance(response.data["history"], list)
        self.assertEqual(response.data["history"][0]["updated_by"], "tester")

    @patch("apps.maintenance.views.export_record_to_excel")
    @patch("apps.maintenance.models.CompletedMaintenanceRecord.objects.get_or_create")
    @patch("apps.wear_part_stock.services.sync_inventory_with_record")
    def test_complete_success(self, mock_sync, mock_completed, mock_export):
        mock_completed.return_value = (MagicMock(tasks={}), True)
        mock_export.return_value = "path/to/file.xlsx"
        response = self.client.post(self.url_complete)
        self.assertEqual(response.status_code, 200)
        self.assertIn("file", response.data)

    @patch("apps.maintenance.views.export_record_to_excel", side_effect=PermissionError("File đang mở"))
    @patch("apps.maintenance.models.CompletedMaintenanceRecord.objects.get_or_create")
    @patch("apps.wear_part_stock.services.sync_inventory_with_record")
    def test_complete_permission_error(self, mock_sync, mock_completed, mock_export):
        mock_completed.return_value = (MagicMock(tasks={}), True)
        response = self.client.post(self.url_complete)
        self.assertEqual(response.status_code, 409)
        self.assertIn("error", response.data)
