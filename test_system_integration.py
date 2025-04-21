import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone

# Import models từ các app liên quan
from apps.equipment_management.models import (
    Equipment, EquipmentCategories, EquipmentManagementUnit, Manufacturer
)
from apps.maintenance.models import MaintenanceRecord, CompletedMaintenanceRecord
from apps.equipment_status.models import EquipmentStatus
from apps.wear_part_stock.models import WearPartStock, StockMovementLog


class SystemIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Tạo user và đăng nhập
        self.user = User.objects.create_user(username='integration_user', password='pass123')
        self.client.login(username='integration_user', password='pass123')

        # --- Equipment Management Setup ---
        self.category = EquipmentCategories.create_if_not_exists("Test Category")
        self.management_unit = EquipmentManagementUnit.objects.create(name="Test Unit")
        self.manufacturer = Manufacturer.objects.create(name="Test Manufacturer")
        self.equipment = Equipment.objects.create(
            name="Integration Equipment",
            category=self.category,
            management_unit=self.management_unit,
            engine_hours=200,
            manufacturer=self.manufacturer
        )

        # --- Maintenance Setup ---
        self.maintenance_record = MaintenanceRecord.objects.create(
            category=self.category,
            equipment=self.equipment,
            maintenance_level=250,  # Giá trị hợp lệ trong choices
            location="Site Integration",
            start_time=timezone.now(),
            responsible_units="Maintenance Team",
            created_by=self.user,
            updated_by=self.user
        )
        # Tạo CompletedMaintenanceRecord (giả lập snapshot rỗng)
        self.completed_record = CompletedMaintenanceRecord.objects.create(
            maintenance_record=self.maintenance_record,
            completed_at=timezone.now()
        )
        # Giả sử không có tasks hay results để đơn giản hóa
        self.completed_record.tasks = {}
        self.completed_record.results = []
        self.completed_record.save()

        # --- Equipment Status Setup ---
        self.equipment_status = EquipmentStatus.objects.create(
            equipment=self.equipment,
            operation_team="Ops Team"
        )

        # --- Wear Part Stock Setup ---
        self.wearpart = WearPartStock.objects.create(
            name="Wear Part A",
            stock_quantity=100,
            min_threshold=10,
            unit="pcs",
            manufacturer_id="WP-A-001",
            alternative_id="WP-A-ALT"
        )

    def test_equipment_management_home(self):
        """
        Test trang chủ của equipment_management.
        """
        url = reverse('equipment_management:home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_maintenance_record_api(self):
        """
        Test API của maintenance app (ví dụ: retrieve một MaintenanceRecord).
        """
        url = reverse('maintenance:maintenance-record-detail', kwargs={'pk': self.maintenance_record.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("equipment"), self.equipment.name)

    def test_equipment_status_endpoints(self):
        """
        Test một số endpoint của equipment_status:
         - GET EquipmentStatus detail (thông qua EquipmentStatusViewSet).
         - View lịch sử bảo trì của thiết bị.
         - View chi tiết snapshot của CompletedMaintenanceRecord.
         - View readonly của IntermediateMaintenance (nếu có).
        """
        # EquipmentStatus detail endpoint
        url_status = reverse('equipment_status:equipment-status-detail', kwargs={'equipment_id': self.equipment.id})
        response_status = self.client.get(url_status)
        self.assertEqual(response_status.status_code, 200)
        data_status = response_status.json()
        self.assertEqual(data_status.get('name'), self.equipment.name)
        self.assertEqual(data_status.get('operation_team'), self.equipment_status.operation_team)

        # maintenance_history_for_equipment (HTML view)
        url_history = reverse('equipment_status:maintenance_history_for_equipment',
                              kwargs={'equipment_id': self.equipment.id})
        response_history = self.client.get(url_history)
        self.assertEqual(response_history.status_code, 200)
        self.assertContains(response_history, self.equipment.name)

        # maintenance_record_readonly_view (HTML view)
        url_readonly = reverse('equipment_status:maintenance_record_readonly',
                               kwargs={'record_id': self.maintenance_record.id})
        response_readonly = self.client.get(url_readonly)
        self.assertEqual(response_readonly.status_code, 200)
        self.assertContains(response_readonly, self.equipment.name)

        # completed_record_detail (HTML view)
        url_completed = reverse('equipment_status:completed_record_detail',
                                kwargs={'record_id': self.completed_record.id})
        response_completed = self.client.get(url_completed)
        self.assertEqual(response_completed.status_code, 200)
        self.assertContains(response_completed, self.equipment.name)

    def test_wear_part_stock_deduct(self):
        """
        Test endpoint của wear_part_stock để giảm tồn kho.
        Vì không có task nào đáp ứng điều kiện trong MaintenanceRecord,
        dự kiến deductions sẽ rỗng.
        """
        url_deduct = reverse('wearpartstock_deduct', kwargs={'record_id': self.maintenance_record.id})
        response = self.client.post(url_deduct, data=json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("deductions"), [])
