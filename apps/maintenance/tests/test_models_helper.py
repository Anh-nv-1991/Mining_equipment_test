from django.test import TestCase
from unittest.mock import Mock, patch

from apps.maintenance.models_helper import group_tasks_and_results

class ModelsHelperTest(TestCase):
    def setUp(self):
        self.maintenance_record = Mock()

    @patch("apps.maintenance.models_helper.get_replacement_status")
    @patch("apps.maintenance.models_helper.map_status_to_vietnamese")
    def test_group_tasks_and_results_basic(self, mock_map_status, mock_get_status):
        # Setup mocks for helper functions
        mock_get_status.return_value = "Completed"
        mock_map_status.return_value = "Đã thực hiện"

        # Fake template objects
        replacement_template = Mock()
        replacement_template.task_name = "Thay lọc nhớt"
        replacement_template.replacement_type = "Lọc dầu"
        replacement_template.manufacturer_id = "A123"
        replacement_template.alternative_id = "B456"
        replacement_template.check_inventory.return_value = {"status": "ok"}

        result = Mock()
        result.notes = "Ghi chú test"
        result.actual_quantity = 1
        result.task = Mock(quantity=1)

        # Fake task object
        task = Mock()
        task.id = 1
        task.quantity = 1
        task.content_type.model = "replacementtemplate"
        task.template = replacement_template
        task.replacement_result = result
        task.supplement_result = None
        task.inspection_result = None
        task.cleaning_result = None

        self.maintenance_record.tasks.all.return_value.order_by.return_value = [task]

        grouped = group_tasks_and_results(self.maintenance_record)
        self.assertIn("replacementtemplate", grouped)

        tasks = grouped["replacementtemplate"]["tasks"]
        results = grouped["replacementtemplate"]["results"]

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["task_name"], "Thay lọc nhớt")
        self.assertEqual(results[0]["status"], "Đã thực hiện")
        self.assertEqual(results[0]["inventory_status"], "ok")

    @patch("apps.maintenance.models_helper.get_replacement_status")
    @patch("apps.maintenance.models_helper.map_status_to_vietnamese")
    def test_group_tasks_and_results_supplement(self, mock_map_status, mock_get_status):
        mock_get_status.return_value = "Completed"
        mock_map_status.return_value = "Đã thực hiện"

        supplement_template = Mock()
        supplement_template.position = "Mỡ"
        supplement_template.change_type = "Bôi trơn"

        result = Mock()
        result.notes = "Hoàn tất"
        result.completed = True

        task = Mock()
        task.id = 2
        task.quantity = 2
        task.content_type.model = "supplementtemplate"
        task.template = supplement_template
        task.supplement_result = result
        task.replacement_result = None
        task.inspection_result = None
        task.cleaning_result = None

        self.maintenance_record.tasks.all.return_value.order_by.return_value = [task]

        grouped = group_tasks_and_results(self.maintenance_record)
        self.assertIn("supplementtemplate", grouped)
        self.assertEqual(grouped["supplementtemplate"]["results"][0]["completed"], True)

    @patch("apps.maintenance.models_helper.get_replacement_status")
    @patch("apps.maintenance.models_helper.map_status_to_vietnamese")
    def test_group_tasks_and_results_other_type(self, mock_map_status, mock_get_status):
        mock_get_status.return_value = "Unknown"
        mock_map_status.return_value = "Không xác định"

        unknown_template = Mock()
        unknown_template.task_name = "Tùy biến"

        task = Mock()
        task.id = 3
        task.quantity = 3
        task.content_type.model = "customtemplate"
        task.template = unknown_template
        task.replacement_result = None
        task.supplement_result = None
        task.inspection_result = None
        task.cleaning_result = None

        self.maintenance_record.tasks.all.return_value.order_by.return_value = [task]

        grouped = group_tasks_and_results(self.maintenance_record)
        self.assertIn("others", grouped)
        self.assertEqual(len(grouped["others"]["tasks"]), 1)
