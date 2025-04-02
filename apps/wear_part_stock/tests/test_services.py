# tests/test_wear_part_stock_full.py
import os
import tempfile
import pandas as pd
from io import StringIO
from django.test import TestCase
from django.core.management import call_command, CommandError
from unittest.mock import MagicMock, patch

# --- Dummy objects cho module services ---

class DummyResult:
    def __init__(self, completed, actual_quantity=0):
        self.completed = completed
        self.actual_quantity = actual_quantity

class DummyTemplate:
    def __init__(self, manufacturer_id):
        self.manufacturer_id = manufacturer_id

class DummyTask:
    def __init__(self, id, quantity, template, replacement_result=None):
        self.id = id
        self.quantity = quantity
        self.template = template
        self.replacement_result = replacement_result

class DummyQuerySet:
    def __init__(self, items):
        self.items = items

    def filter(self, *args, **kwargs):
        # Trả về instance mới với cùng danh sách
        return DummyQuerySet(self.items)

    def order_by(self, *args, **kwargs):
        # Nếu sắp xếp theo "-stock_quantity", trả về DummyQuerySet mới với danh sách đã được sắp xếp giảm dần
        if args and args[0] == "-stock_quantity":
            sorted_items = sorted(self.items, key=lambda x: x.stock_quantity, reverse=True)
            return DummyQuerySet(sorted_items)
        return DummyQuerySet(self.items)

    def count(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

class DummyRecord:
    def __init__(self, tasks):
        self.tasks = MagicMock()
        self.tasks.filter.return_value = tasks

class FakeStock:
    def __init__(self, stock_quantity, manufacturer_id):
        self.stock_quantity = stock_quantity
        self.manufacturer_id = manufacturer_id

    def save(self, update_fields=None):
        # Giả lập save: không cần làm gì thêm vì thuộc tính đã được cập nhật trực tiếp.
        pass

# --- Test cho module services ---
from apps.wear_part_stock import services

class ServicesTest(TestCase):
    @patch("apps.wear_part_stock.services.StockMovementLog")
    @patch("apps.wear_part_stock.services.WearPartStock")
    def test_deduct_inventory_sufficient_stock(self, mock_wear_part_stock, mock_stock_movement_log):
        """
        Kiểm tra khi tồn kho đủ để trừ hết số lượng yêu cầu.
        """
        template = DummyTemplate("ABC")
        result = DummyResult(completed=True)
        task = DummyTask(id=1, quantity=5, template=template, replacement_result=result)
        record = DummyRecord([task])

        fake_stock = FakeStock(stock_quantity=10, manufacturer_id="ABC")
        fake_queryset = DummyQuerySet([fake_stock])
        mock_wear_part_stock.objects.filter.return_value = fake_queryset

        dummy_log = MagicMock()
        mock_stock_movement_log.objects.create.return_value = dummy_log

        logs = services.deduct_inventory_for_record(record)
        self.assertEqual(fake_stock.stock_quantity, 5)
        self.assertEqual(len(logs), 1)
        mock_stock_movement_log.objects.create.assert_called_with(
            stock=fake_stock,
            maintenance_record=record,
            quantity=5,
            shortage=0
        )

    @patch("apps.wear_part_stock.services.StockMovementLog")
    @patch("apps.wear_part_stock.services.WearPartStock")
    def test_deduct_inventory_insufficient_stock(self, mock_wear_part_stock, mock_stock_movement_log):
        """
        Kiểm tra khi tồn kho không đủ để trừ hết số lượng yêu cầu, dẫn đến log báo thiếu hàng.
        """
        template = DummyTemplate("ABC")
        result = DummyResult(completed=True)
        task = DummyTask(id=2, quantity=5, template=template, replacement_result=result)
        record = DummyRecord([task])

        fake_stock = FakeStock(stock_quantity=3, manufacturer_id="ABC")
        fake_queryset = DummyQuerySet([fake_stock])
        mock_wear_part_stock.objects.filter.return_value = fake_queryset

        dummy_log = MagicMock()
        mock_stock_movement_log.objects.create.side_effect = [dummy_log, dummy_log]

        logs = services.deduct_inventory_for_record(record)
        self.assertEqual(fake_stock.stock_quantity, 0)
        self.assertEqual(len(logs), 2)
        calls = mock_stock_movement_log.objects.create.call_args_list
        self.assertEqual(calls[0][1]['quantity'], 3)
        self.assertEqual(calls[0][1]['shortage'], 0)
        self.assertEqual(calls[1][1]['quantity'], 0)
        self.assertEqual(calls[1][1]['shortage'], 2)

    @patch("apps.wear_part_stock.services.StockMovementLog")
    @patch("apps.wear_part_stock.services.WearPartStock")
    def test_sync_inventory_with_record(self, mock_wear_part_stock, mock_stock_movement_log):
        """
        Kiểm tra việc đồng bộ tồn kho với record.
        Tạo một task đã hoàn thành với actual_quantity = 4.
        Giả định chưa có log trừ nào được tạo trước đó.
        """
        template = DummyTemplate("XYZ")
        result = DummyResult(completed=True, actual_quantity=4)
        task = DummyTask(id=3, quantity=4, template=template, replacement_result=result)
        # Quan trọng: gán task vào result để get_replacement_status hoạt động đúng.
        result.task = task
        record = DummyRecord([task])

        logs_mock = MagicMock()
        logs_mock.filter.return_value.exists.return_value = False

        with patch("apps.wear_part_stock.services.StockMovementLog.objects.filter", return_value=logs_mock):
            fake_stock1 = FakeStock(stock_quantity=2, manufacturer_id="XYZ")
            fake_stock2 = FakeStock(stock_quantity=3, manufacturer_id="XYZ")
            fake_queryset = DummyQuerySet([fake_stock1, fake_stock2]).order_by("-stock_quantity")
            mock_wear_part_stock.objects.filter.return_value = fake_queryset

            dummy_log = MagicMock()
            mock_stock_movement_log.objects.create.side_effect = [dummy_log, dummy_log]

            services.sync_inventory_with_record(record)
            # Sau khi sync:
            # fake_stock2 (3 đơn vị) dùng đầu tiên: trừ 3 → còn 0
            # fake_stock1 (2 đơn vị) dùng sau: trừ 1 → còn 1
            self.assertEqual(fake_stock2.stock_quantity, 0)
            self.assertEqual(fake_stock1.stock_quantity, 1)

# --- Test cho import_stock command (apps/wear_part_stock/management/commands/import_stock.py) ---

class ImportStockCommandTest(TestCase):
    def setUp(self):
        from apps.equipment_management.models import Manufacturer
        from apps.wear_part_stock.models import WearPartStock
        Manufacturer.objects.all().delete()
        WearPartStock.objects.all().delete()

    def test_import_stock_command_success(self):
        df = pd.DataFrame({
            'manufacturer': ['Test Manufacturer', 'Test Manufacturer'],
            'name': ['Part A', 'Part A'],
            'stock_quantity': [10, 5],
            'min_threshold': [2, 2],
            'unit': ['pcs', 'pcs'],
            'manufacturer_id': ['ABC', 'ABC'],
            'alternative_id': ['ALT', 'ALT']
        })
        temp_file = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        try:
            df.to_excel(temp_file.name, index=False)
            temp_file.close()

            out = StringIO()
            call_command('import_stock', temp_file.name, stdout=out)
            output = out.getvalue()
            self.assertTrue("Created" in output or "Updated" in output)
            self.assertIn("Imported 1 unique parts", output)

            from apps.wear_part_stock.models import WearPartStock
            stock = WearPartStock.objects.get(manufacturer_id="ABC")
            self.assertEqual(stock.stock_quantity, 15)
        finally:
            os.unlink(temp_file.name)

    def test_import_stock_command_missing_columns(self):
        df = pd.DataFrame({
            'manufacturer': ['Test Manufacturer'],
            'name': ['Part A'],
        })
        temp_file = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        try:
            df.to_excel(temp_file.name, index=False)
            temp_file.close()
            with self.assertRaises(CommandError) as context:
                call_command('import_stock', temp_file.name)
            self.assertIn("Missing columns", str(context.exception))
        finally:
            os.unlink(temp_file.name)
