from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from apps.equipment_management.models import Equipment, EquipmentCategories, EquipmentManagementUnit
from apps.maintenance.models import MaintenanceRecord
from apps.equipment_status.models import EquipmentStatus

class MaintenanceModuleTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Tạo user kiểm thử
        self.user = User.objects.create_user(username="testuser", password="testpass")
        # Tạo danh mục thiết bị
        self.category = EquipmentCategories.objects.create(name="Excavator")
        # Tạo đối tượng quản lý thiết bị
        self.management_unit = EquipmentManagementUnit.objects.create(name="Test Management Unit")
        # Tạo Equipment với đầy đủ thông tin theo model:
        self.equipment = Equipment.objects.create(
            name="Test Excavator",
            category=self.category,
            management_unit=self.management_unit,
            engine_hours=100,
        )
        self.status = EquipmentStatus.objects.create(
            equipment=self.equipment,
            operator_team="Team A",
        )
        self.client.login(username="testuser", password="testpass")

    def test_create_maintenance_record(self):
        # Tạo bản ghi bảo dưỡng cho Equipment vừa tạo
        record = MaintenanceRecord.objects.create(
            category=self.category,
            equipment=self.equipment,
            maintenance_level=250,
            location="Site A",
            start_time=timezone.now(),
            responsible_units="Maintenance Team",
            created_by=self.user,
            updated_by=self.user
        )
        # Giả sử __str__ của MaintenanceRecord trả về "Test Excavator (Excavator) - 250h"
        expected_str = f"{self.equipment} - 250h"
        self.assertEqual(str(record), expected_str)

    def test_get_equipment_by_category(self):
        url = reverse('get_equipment_by_category')
        response = self.client.get(url, {"category_id": self.category.id})
        self.assertEqual(response.status_code, 200)
        self.assertIn("equipments", response.json())

    def test_get_maintenance_tasks_unauthenticated(self):
        # Kiểm tra API bảo dưỡng yêu cầu xác thực
        self.client.logout()
        url = reverse('get_maintenance_tasks', args=[1])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
