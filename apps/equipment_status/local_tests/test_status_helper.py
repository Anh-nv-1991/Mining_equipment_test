from django.test import TestCase
from unittest.mock import patch
from apps.maintenance.models import CompletedMaintenanceRecord, MaintenanceTask, ReplacementTemplate, MaintenanceRecord
from apps.equipment_status.status_helper import get_completed_record_and_tasks
from apps.maintenance.models import EquipmentCategories, Equipment
from datetime import datetime
from django.contrib.contenttypes.models import ContentType

class StatusHelperTest(TestCase):

    @patch('apps.equipment_status.status_helper.get_object_or_404')
    def test_get_completed_record_and_tasks_valid(self, mock_get_object_or_404):
        # Tạo đối tượng EquipmentCategory
        category = EquipmentCategories.objects.create(name="Test Category")

        # Tạo đối tượng Equipment và liên kết với category
        equipment = Equipment.objects.create(name="Test Equipment", category=category)

        # Tạo đối tượng MaintenanceRecord với start_time là datetime
        maintenance_record = MaintenanceRecord.objects.create(
            category=category,  # Gán category cho MaintenanceRecord
            equipment=equipment,  # Gán Equipment
            maintenance_level=250,
            location="Test Location",
            start_time=datetime(2025, 4, 3, 0, 0, 0),
            end_time=None,
            responsible_units="Test Unit",
            created_by=None,
            updated_by=None
        )

        # Tạo đối tượng CompletedMaintenanceRecord và liên kết với MaintenanceRecord
        completed_record = CompletedMaintenanceRecord.objects.create(
            maintenance_record=maintenance_record,
            completed_at=datetime(2025, 4, 3, 12, 0, 0)
        )

        # Giả lập get_object_or_404
        mock_get_object_or_404.return_value = completed_record

        # Tạo một template giả
        replacement_template = ReplacementTemplate.objects.create(
            category=category,
            maintenance_level=250,# Thêm trường category với đối tượng EquipmentCategories đã tạo ở trên
            task_name="Test Task",
            replacement_type="Type A",
            quantity=1,
            manufacturer_id="M001"
        )

        # Lấy ContentType cho ReplacementTemplate
        ct = ContentType.objects.get_for_model(ReplacementTemplate)

        # Tạo một tác vụ và liên kết với MaintenanceRecord (không phải CompletedMaintenanceRecord)
        task = MaintenanceTask.objects.create(
            maintenance_record=maintenance_record,
            content_type=ct,
            object_id=replacement_template.id,
            quantity=1
        )

        # Gọi hàm cần kiểm tra
        comp, grouped_tasks = get_completed_record_and_tasks(1)

        # Kiểm tra rằng bản ghi được lấy đúng
        self.assertEqual(comp, completed_record)

        # Kiểm tra rằng các tác vụ được nhóm đúng
        self.assertIn('REPLACEMENTTEMPLATE', grouped_tasks)
        self.assertEqual(len(grouped_tasks['REPLACEMENTTEMPLATE']), 1)

    @patch('apps.equipment_status.status_helper.get_object_or_404')
    def test_get_completed_record_and_tasks_no_tasks(self, mock_get_object_or_404):
        # Tạo dữ liệu giả không có task
        category = EquipmentCategories.objects.create(name="Test Category")
        equipment = Equipment.objects.create(name="Test Equipment", category=category)
        maintenance_record = MaintenanceRecord.objects.create(
            category=category,
            equipment=equipment,
            maintenance_level=250,
            location="Test Location",
            start_time=datetime(2025, 4, 3, 0, 0, 0),  # Sử dụng datetime thay vì chuỗi
            end_time=None,
            responsible_units="Test Unit",
            created_by=None,
            updated_by=None
        )
        completed_record = CompletedMaintenanceRecord.objects.create(
            maintenance_record=maintenance_record,
            completed_at=datetime(2025, 4, 3, 12, 0, 0)
        )

        # Giả lập get_object_or_404
        mock_get_object_or_404.return_value = completed_record

        # Gọi hàm cần kiểm tra
        comp, grouped_tasks = get_completed_record_and_tasks(1)

        # Kiểm tra rằng không có nhóm nào
        self.assertEqual(grouped_tasks, {})

    @patch('apps.equipment_status.status_helper.get_object_or_404')
    def test_get_completed_record_and_tasks_invalid_record_id(self, mock_get_object_or_404):
        # Giả lập trường hợp không tìm thấy bản ghi
        mock_get_object_or_404.side_effect = Exception("Record not found")

        # Kiểm tra trường hợp ngoại lệ
        with self.assertRaises(Exception):
            get_completed_record_and_tasks(999)
