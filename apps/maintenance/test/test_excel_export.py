import os
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from apps.maintenance.excel_export import export_record_to_excel


class ExcelExportTest(TestCase):
    @patch("apps.maintenance.excel_export.os.makedirs")
    @patch("apps.maintenance.excel_export.os.listdir", return_value=["123_1_1.xlsx"])
    @patch("apps.maintenance.excel_export.os.remove")
    @patch("apps.maintenance.excel_export.Workbook")
    @patch("apps.maintenance.excel_export.calculate_shift_count", return_value=1)
    @patch("apps.maintenance.excel_export.sanitize_name", side_effect=lambda x: x.lower())
    @patch("apps.maintenance.excel_export.get_replacement_status", return_value="Completed")
    @patch("apps.maintenance.excel_export.map_status_to_vietnamese", return_value="Đã thực hiện")
    def test_export_success(
        self, mock_map_status, mock_get_status, mock_sanitize, mock_shift,
        mock_wb_class, mock_remove, mock_listdir, mock_makedirs
    ):
        # Fake workbook & sheet
        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.create_sheet.return_value = mock_ws
        mock_wb_class.return_value = mock_wb

        # Fake record
        record = Mock()
        record.record_id = "123"
        record.category.name = "Cat A"
        record.equipment.name = "EQ A"
        record.start_time = record.end_time = Mock()
        record.completed_record.pk = 1

        # Fake task queryset
        task = Mock()
        task.template.task_name = "Task X"
        task.template.replacement_type = "Type A"
        task.template.manufacturer_id = "M123"
        task.template.alternative_id = "ALT456"
        task.template.check_inventory.return_value = {"status": "ok"}
        task.quantity = 1
        task.replacement_result.actual_quantity = 1
        task.replacement_result.notes = ""
        task.replacement_result.task = task
        task.content_type.model = "replacementtemplate"
        task.template = task.template

        mock_qs = MagicMock()
        mock_qs.filter.return_value = [task]
        record.tasks.select_related.return_value = mock_qs

        result = export_record_to_excel(record)

        self.assertIn(".xlsx", result)
        mock_wb.save.assert_called_once()

    @patch("apps.maintenance.excel_export.Workbook")
    @patch("apps.maintenance.excel_export.os.makedirs")
    @patch("apps.maintenance.excel_export.os.listdir", return_value=[])
    def test_export_permission_error(self, mock_listdir, mock_makedirs, mock_wb_class):
        # Setup
        mock_wb = MagicMock()
        mock_wb.save.side_effect = PermissionError("File is open")
        mock_wb_class.return_value = mock_wb

        record = Mock()
        record.record_id = "XYZ"
        record.category.name = "Cat"
        record.equipment.name = "EQ"
        record.start_time = datetime(2025, 4, 1, 8, 0)
        record.end_time = datetime(2025, 4, 1, 16, 0)
        record.completed_record.pk = 1
        record.tasks.select_related.return_value.filter.return_value = []

        with self.assertRaises(PermissionError) as context:
            export_record_to_excel(record)

        self.assertIn("File Excel đang mở", str(context.exception))
