# tests/test_maintenance.py
import logging
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.equipment_management.models import (
    Equipment,
    EquipmentCategories,
    EquipmentManagementUnit,
    Manufacturer
)
from apps.equipment_status.models import EquipmentStatus
from apps.maintenance.models import MaintenanceRecord
from apps.maintenance.serializers import MaintenanceRecordSerializer

User = get_user_model()
logger = logging.getLogger(__name__)


class MaintenanceRecordTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="test_admin", password="4791")
        self.client.login(username="test_admin", password="4791")

        # Equipment setup
        self.category = EquipmentCategories.objects.create(name="Test Category")
        self.management_unit = EquipmentManagementUnit.objects.create(name="Test Unit")
        self.manufacturer = Manufacturer.objects.create(name="Test Manufacturer")

        self.equipment = Equipment.objects.create(
            name="Test Equipment",
            category=self.category,
            management_unit=self.management_unit,
            engine_hours=100,
            manufacturer=self.manufacturer,
        )

        self.status = EquipmentStatus.objects.create(
            equipment=self.equipment,
            operation_team="Team A",
        )

        self.record1 = MaintenanceRecord.objects.create(
            equipment=self.equipment,
            category=self.category,
            maintenance_level=250,
            location="Site A",
            start_time=timezone.now(),
            responsible_units="Team A"
        )
        self.record2 = MaintenanceRecord.objects.create(
            equipment=self.equipment,
            category=self.category,
            maintenance_level=500,
            location="Site B",
            start_time=timezone.now(),
            responsible_units="Team A"
        )

    def test_create_maintenance_record_str(self):
        expected_str = f"{self.equipment.name} ({self.category}) - 250h"
        self.assertEqual(str(self.record1), expected_str)

    def test_get_equipment_by_category(self):
        url = reverse("maintenance:get_equipment_by_category")
        response = self.client.get(url, {"category_id": self.category.id})
        self.assertEqual(response.status_code, 200)
        self.assertIn("equipments", response.json())

    def test_list_maintenance_records(self):
        url = reverse("maintenance:maintenance-record-list")
        response = self.client.get(url, {"limit": 1, "offset": 0})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)

    def test_retrieve_maintenance_record(self):
        url = reverse("maintenance:maintenance-record-detail", args=[self.record1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = MaintenanceRecordSerializer(self.record1)
        response_start = parse_datetime(response.data.get('start_time'))
        expected_start = parse_datetime(serializer.data.get('start_time'))
        self.assertEqual(response_start, expected_start, "Giá trị start_time không khớp")

        self.assertEqual(response.data.get('id'), serializer.data.get('id'))
        self.assertEqual(response.data.get('end_time'), serializer.data.get('end_time'))
