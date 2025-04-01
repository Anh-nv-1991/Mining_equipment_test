from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from django.test import TestCase
from django.utils.safestring import SafeString

from apps.maintenance.maintenance_helpers import (
    generate_record_id,
    calculate_shift_count,
    generate_csv_filename,
    check_inventory_for_template,
    sanitize_name,
    get_replacement_status,
    map_status_to_vietnamese,
    get_grouped_data,
    render_grouped_table
)

class MaintenanceHelpersTest(TestCase):
    def setUp(self):
        self.mock_record = Mock()
        self.mock_record.category.name = "Xe Đào||EX200"
        self.mock_record.equipment.name = "Hitachi ZX"
        self.mock_record.maintenance_level = 250
        self.mock_record.start_time = datetime(2025, 4, 1, 8, 0)
        self.mock_record.end_time = datetime(2025, 4, 1, 16, 0)

    def test_generate_record_id(self):
        record_id = generate_record_id(self.mock_record)
        self.assertTrue(record_id.startswith("EX200-HIT-250-25"))

    def test_calculate_shift_count(self):
        start = datetime(2025, 4, 1, 8, 0)
        end = datetime(2025, 4, 1, 18, 0)
        self.assertEqual(calculate_shift_count(start, end), 2)

    def test_generate_csv_filename(self):
        filename = generate_csv_filename(self.mock_record)
        self.assertTrue(filename.endswith("_1.csv"))

    def test_sanitize_name(self):
        self.assertEqual(sanitize_name("TÊN Máy #1!"), "ten_may_1")
        self.assertEqual(sanitize_name(None), "unknown")

    def test_get_replacement_status(self):
        task = Mock()
        task.quantity = 5

        result = Mock()
        result.task = task

        result.actual_quantity = 0
        self.assertEqual(get_replacement_status(result), "Not Started")

        result.actual_quantity = 3
        self.assertEqual(get_replacement_status(result), "Incomplete")

        result.actual_quantity = 5
        self.assertEqual(get_replacement_status(result), "Completed")

        result.actual_quantity = 7
        self.assertEqual(get_replacement_status(result), "Overdone")

    def test_map_status_to_vietnamese(self):
        self.assertEqual(map_status_to_vietnamese("Not Started"), "Chưa thực hiện")
        self.assertEqual(map_status_to_vietnamese("Invalid"), "Không xác định")
        self.assertEqual(map_status_to_vietnamese("Random"), "Random")

    def test_check_inventory_for_template(self):
        template = Mock()
        template.quantity = 5
        template.manufacturer_id = "A123/B456"

        mock_qs = [Mock(stock_quantity=2), Mock(stock_quantity=4)]

        with patch("apps.maintenance.maintenance_helpers.WearPartStock.objects.filter", return_value=mock_qs):
            result = check_inventory_for_template(template)
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["available"], 6)
            self.assertEqual(result["shortage"], 0)

    def test_get_grouped_data_with_list(self):
        completed_record = Mock()
        completed_record.tasks = [
            {"id": 1, "task_type": "replacementtemplate"},
            {"id": 2, "task_type": "supplementtemplate"},
        ]
        completed_record.results = [
            {"task_id": 1, "status": "Completed"},
            {"task_id": 2, "status": "Not Started"},
        ]

        grouped = get_grouped_data(completed_record)
        self.assertIn("replacementtemplate", grouped)
        self.assertEqual(len(grouped["replacementtemplate"]), 1)

    def test_get_grouped_data_with_dict(self):
        completed_record = Mock()
        completed_record.tasks = {
            "inspectiontemplate": {
                "tasks": [{"id": 3, "task_name": "Kiểm tra dầu"}],
                "results": [{"task_id": 3, "condition": "Tốt"}]
            }
        }
        completed_record.results = []

        grouped = get_grouped_data(completed_record)
        self.assertIn("inspectiontemplate", grouped)
        self.assertEqual(len(grouped["inspectiontemplate"]), 1)

    def test_render_grouped_table_html(self):
        grouped_data = {
            "replacementtemplate": [
                ({"id": 1, "task_name": "Thay lọc"}, {"status": "Completed", "actual_quantity": 1, "inventory_status": "ok", "notes": "", "replacement_type": "lọc dầu", "manufacturer_id": "A123", "alternative_id": "B456", "quantity": 1}),
            ]
        }
        html = render_grouped_table(grouped_data)
        self.assertIsInstance(html, SafeString)
        self.assertIn("<h3>REPLACEMENTTEMPLATE</h3>", html)
        self.assertIn("<td>1</td>", html)
