import logging
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.utils.dateparse import parse_datetime

from apps.equipment_management.models import (
    Equipment,
    EquipmentCategories,
    EquipmentManagementUnit,
    Manufacturer
)
from apps.maintenance.models import MaintenanceRecord
from apps.maintenance.serializers import MaintenanceRecordSerializer

User = get_user_model()
logger = logging.getLogger(__name__)


class MaintenanceRecordAPITest(TestCase):
    def setUp(self):
        try:
            # Tạo tài khoản test
            self.user = User.objects.create_user(username="admin", password="4791")
            self.client = APIClient()
            self.client.login(username="admin", password="4791")

            # Tạo các đối tượng cần thiết
            self.category = EquipmentCategories.create_if_not_exists("Test Category")
            self.manufacturer = Manufacturer.objects.create(name="Test Manufacturer")
            self.management_unit = EquipmentManagementUnit.objects.create(name="Test Unit")

            self.equipment = Equipment.objects.create(
                name="Test Equipment",
                category=self.category,
                management_unit=self.management_unit,
                engine_hours=100,
                manufacturer=self.manufacturer,
            )

            # Sử dụng số cho maintenance_level vì model yêu cầu kiểu số
            self.record1 = MaintenanceRecord.objects.create(
                equipment=self.equipment,
                category=self.category,
                maintenance_level=1,
                start_time="2025-03-25T08:00:00Z"
            )
            self.record2 = MaintenanceRecord.objects.create(
                equipment=self.equipment,
                category=self.category,
                maintenance_level=2,
                start_time="2025-03-26T09:00:00Z"
            )
        except Exception as e:
            logger.error("Error in setUp: %s", e)
            raise

    def test_list_maintenance_records(self):
        try:
            url = reverse("maintenance:maintenance-record-list")
            response = self.client.get(url, {"limit": 1, "offset": 0})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("count", response.data)
            self.assertIn("results", response.data)
            self.assertEqual(len(response.data["results"]), 1)
        except Exception as e:
            logger.error("Error in test_list_maintenance_records: %s", e)
            raise

    def test_retrieve_maintenance_record(self):
        try:
            url = reverse("maintenance:maintenance-record-detail", args=[self.record1.id])
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            serializer = MaintenanceRecordSerializer(self.record1)

            # So sánh start_time bằng cách chuyển đổi về đối tượng datetime
            response_start = parse_datetime(response.data.get('start_time'))
            expected_start = parse_datetime(serializer.data.get('start_time'))
            self.assertEqual(response_start, expected_start, "Giá trị start_time không khớp sau chuyển đổi múi giờ")

            # So sánh các trường khác
            self.assertEqual(response.data.get('id'), serializer.data.get('id'))
            self.assertEqual(response.data.get('end_time'), serializer.data.get('end_time'))
        except Exception as e:
            logger.error("Error in test_retrieve_maintenance_record: %s", e)
            raise

        def test_for_error(self):
            raise Exception("Giả lập lỗi cho kiểm tra log")
