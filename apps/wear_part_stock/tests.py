from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from django.utils import timezone

from apps.wear_part_stock.models import WearPartStock, StockMovementLog
from apps.equipment_management.models import Manufacturer, EquipmentCategories, EquipmentManagementUnit, Equipment
from apps.maintenance.models import MaintenanceRecord


class WearPartStockTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.force_authenticate(user=self.user)

        # Tạo dữ liệu nền: manufacturer, category, unit, equipment
        self.manufacturer = Manufacturer.objects.create(name="Test Maker")
        self.category = EquipmentCategories.objects.create(name="Test Category")
        self.unit = EquipmentManagementUnit.objects.create(name="Unit A")
        self.equipment = Equipment.objects.create(
            name="Machine A",
            category=self.category,
            management_unit=self.unit
        )

        self.part = WearPartStock.objects.create(
            manufacturer_fk=self.manufacturer,
            name="Filter A",
            stock_quantity=10,
            min_threshold=2,
            unit="pcs",
            manufacturer_id="F-A"
        )

        self.record = MaintenanceRecord.objects.create(
            equipment=self.equipment,
            category=self.category,
            maintenance_level=250,
            location="Site A",
            start_time=timezone.now(),
            responsible_units="Team A"
        )

    def test_deduct_parts_enough_stock(self):
        shortage = WearPartStock.deduct_parts(["F-A"], 5)
        self.part.refresh_from_db()
        self.assertEqual(shortage, 0)
        self.assertEqual(self.part.stock_quantity, 5)

    def test_deduct_parts_not_enough_stock(self):
        shortage = WearPartStock.deduct_parts(["F-A"], 15)
        self.part.refresh_from_db()
        self.assertEqual(shortage, 5)
        self.assertEqual(self.part.stock_quantity, 0)

    def test_api_deduct_stock_view_minimal(self):
        url = reverse("wearpartstock_deduct", args=[self.record.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("success", response.json())
