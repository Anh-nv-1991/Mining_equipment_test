from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from django.utils import timezone

from apps.wear_part_stock.models import WearPartStock, StockMovementLog
from apps.equipment_management.models import Manufacturer
from apps.maintenance.models import MaintenanceRecord
from apps.maintenance.models import MaintenanceTask  # cần đúng import nếu task được dùng

class WearPartStockTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.force_authenticate(user=self.user)

        self.manufacturer = Manufacturer.objects.create(name="Test Maker")
        self.part = WearPartStock.objects.create(
            manufacturer_fk=self.manufacturer,
            name="Filter A",
            stock_quantity=10,
            min_threshold=2,
            unit="pcs",
            manufacturer_id="F-A"
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
        # Giả lập record và task nếu cần (giả định có route và logic ready)
        record = MaintenanceRecord.objects.create(
            equipment_id=1,  # hoặc tạo Equipment nếu cần
            category_id=1,
            maintenance_level=250,
            location="Site A",
            start_time=timezone.now(),
            responsible_units="Team A"
        )

        url = reverse("wearpartstock_deduct", args=[record.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("success", response.json())
