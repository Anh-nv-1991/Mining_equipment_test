from django.test import TestCase
from datetime import datetime
from unittest.mock import Mock
from apps.maintenance.serializers import MaintenanceRecordSerializer, ModalMaintenanceTaskSerializer


class MaintenanceRecordSerializerTest(TestCase):
    def test_serialize_valid_data(self):
        record = Mock()
        record.id = 1
        record.equipment.name = "Xe xúc"
        record.category.name = "Excavator"
        record.get_maintenance_level_display = "500h"
        record.start_time = datetime(2025, 4, 1, 8, 0)
        record.end_time = datetime(2025, 4, 1, 16, 0)

        serializer = MaintenanceRecordSerializer(record)
        data = serializer.data

        self.assertEqual(data["equipment"], "Xe xúc")
        self.assertEqual(data["category"], "Excavator")
        self.assertEqual(data["maintenance_level"], "500h")

    def test_validate_end_time_before_start_time(self):
        data = {
            "start_time": datetime(2025, 4, 1, 10, 0),
            "end_time": datetime(2025, 4, 1, 8, 0),
        }
        serializer = MaintenanceRecordSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("end_time", serializer.errors)


class ModalMaintenanceTaskSerializerTest(TestCase):
    def test_replacement_task_serialization(self):
        task = Mock()
        task.id = 1
        task.content_type.model = "replacementtemplate"
        task.template = Mock(
            task_name="Thay lọc",
            replacement_type="lọc dầu",
            manufacturer_id="A123",
            alternative_id="B456",
            check_inventory=Mock(return_value={"status": "ok"})
        )
        task.quantity = 1
        task.replacement_result = Mock(actual_quantity=2, notes="OK")
        task.supplement_result = None
        task.inspection_result = None
        task.cleaning_result = None

        serializer = ModalMaintenanceTaskSerializer(task)
        data = serializer.data

        self.assertEqual(data["task_type"], "replacement")
        self.assertEqual(data["task_name"], "Thay lọc")
        self.assertEqual(data["actual_quantity"], 2)
        self.assertEqual(data["notes"], "OK")
        self.assertEqual(data["check_inventory"], {"status": "ok"})

    def test_supplement_task_serialization(self):
        task = Mock()
        task.id = 2
        task.content_type.model = "supplementtemplate"
        task.template = Mock(change_type="Đổ nước", position="Bình phụ", quantity=1)
        task.supplement_result = Mock(completed=True, notes="Đã xong")
        task.replacement_result = None
        task.inspection_result = None
        task.cleaning_result = None

        serializer = ModalMaintenanceTaskSerializer(task)
        data = serializer.data

        self.assertEqual(data["task_type"], "supplement")
        self.assertTrue(data["completed"])
        self.assertEqual(data["notes"], "Đã xong")
        self.assertEqual(data["position"], "Bình phụ")

    def test_inspection_task_serialization(self):
        task = Mock()
        task.id = 3
        task.content_type.model = "inspectiontemplate"
        task.template = Mock(task_name="Kiểm tra dầu")
        task.inspection_result = Mock(condition="Tốt", notes="OK")
        task.supplement_result = None
        task.replacement_result = None
        task.cleaning_result = None

        serializer = ModalMaintenanceTaskSerializer(task)
        data = serializer.data

        self.assertEqual(data["task_type"], "inspection")
        self.assertEqual(data["condition"], "Tốt")
        self.assertEqual(data["notes"], "OK")

    def test_cleaning_task_serialization(self):
        task = Mock()
        task.id = 4
        task.content_type.model = "cleaningtemplate"
        task.template = Mock(task_name="Lau cabin")
        task.cleaning_result = Mock(condition="Sạch", notes="OK")
        task.supplement_result = None
        task.replacement_result = None
        task.inspection_result = None

        serializer = ModalMaintenanceTaskSerializer(task)
        data = serializer.data

        self.assertEqual(data["task_type"], "cleaning")
        self.assertEqual(data["condition"], "Sạch")
        self.assertEqual(data["notes"], "OK")

