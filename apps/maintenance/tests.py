from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from apps.equipment_management.models import Equipment, EquipmentCategories, EquipmentManagementUnit
from apps.equipment_status.models import EquipmentStatus
from apps.maintenance.models import MaintenanceRecord


class MaintenanceModuleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.login(username="testuser", password="testpass")

        # Tạo danh mục thiết bị
        self.category = EquipmentCategories.objects.create(name="Excavator")

        # Tạo đơn vị quản lý
        self.management_unit = EquipmentManagementUnit.objects.create(name="Unit A")

        # Tạo thiết bị
        self.equipment = Equipment.objects.create(
            name="Test Excavator",
            category=self.category,
            management_unit=self.management_unit,
        )

        # Tạo trạng thái thiết bị
        self.status = EquipmentStatus.objects.create(
            equipment=self.equipment,
            operation_team="Team A",
        )

        # Tạo bản ghi bảo trì
        self.record = MaintenanceRecord.objects.create(
            equipment=self.equipment,
            category=self.category,
            maintenance_level=250,
            location="Site A",
            start_time=timezone.now(),
            responsible_units="Team A"
        )

    def test_create_maintenance_record(self):
        expected_str = "Test Excavator (Excavator) - 250h"
        self.assertEqual(str(self.record), expected_str)

    def test_get_equipment_by_category(self):
        url = reverse("maintenance:get_equipment_by_category")
        response = self.client.get(url, {"category_id": self.category.id})
        self.assertEqual(response.status_code, 200)
        self.assertIn("equipments", response.json())
