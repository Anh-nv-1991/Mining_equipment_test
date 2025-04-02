# tests/test_import_stock_improved.py
import os
import tempfile
import pandas as pd
from io import StringIO
from django.test import TestCase
from django.core.management import call_command, CommandError

class ImportStockCommandTest(TestCase):
    def setUp(self):
        # Dọn dẹp dữ liệu liên quan để bắt đầu test
        from apps.equipment_management.models import Manufacturer
        from apps.wear_part_stock.models import WearPartStock
        Manufacturer.objects.all().delete()
        WearPartStock.objects.all().delete()

    def test_import_stock_command_success(self):
        # Tạo DataFrame với dữ liệu mẫu
        df = pd.DataFrame({
            'manufacturer': ['Test Manufacturer', 'Test Manufacturer'],
            'name': ['Part A', 'Part A'],
            'stock_quantity': [10, 5],
            'min_threshold': [2, 2],
            'unit': ['pcs', 'pcs'],
            'manufacturer_id': ['ABC', 'ABC'],
            'alternative_id': ['ALT', 'ALT']
        })
        # Tạo file Excel tạm thời
        temp_file = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        try:
            df.to_excel(temp_file.name, index=False)
            temp_file.close()

            # Gọi command import_stock và kiểm tra output
            out = StringIO()
            call_command('import_stock', temp_file.name, stdout=out)
            output = out.getvalue()
            self.assertTrue("Created" in output or "Updated" in output)
            self.assertIn("Imported 1 unique parts", output)

            # Kiểm tra dữ liệu được cập nhật vào cơ sở dữ liệu
            from apps.wear_part_stock.models import WearPartStock
            stock = WearPartStock.objects.get(manufacturer_id="ABC")
            # Tổng số lượng: 10 + 5 = 15
            self.assertEqual(stock.stock_quantity, 15)
        finally:
            os.unlink(temp_file.name)

    def test_import_stock_command_missing_columns(self):
        # Tạo DataFrame thiếu các cột bắt buộc
        df = pd.DataFrame({
            'manufacturer': ['Test Manufacturer'],
            'name': ['Part A'],
            # Thiếu: stock_quantity, min_threshold, unit, manufacturer_id, alternative_id
        })
        temp_file = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        try:
            df.to_excel(temp_file.name, index=False)
            temp_file.close()
            # Kiểm tra command báo lỗi khi thiếu cột
            with self.assertRaises(CommandError) as context:
                call_command('import_stock', temp_file.name)
            self.assertIn("Missing columns", str(context.exception))
        finally:
            os.unlink(temp_file.name)
