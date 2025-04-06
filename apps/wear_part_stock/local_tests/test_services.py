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
        # Trả về chính nó để giữ nguyên đối tượng đã có
        return self

    def order_by(self, *args, **kwargs):
        # Trả về chính nó
        return self

    def count(self):
        return len(self.items)

    def first(self):
        return self.items[0] if self.items else None

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
        # Giả lập save: thuộc tính được cập nhật trực tiếp
        pass

# --- Test cho module services ---
from apps.wear_part_stock import services

class ServicesTest(TestCase):
    @patch("apps.wear_part_stock.services.StockMovementLog")
    @patch("apps.wear_part_stock.services.WearPartStock")
    def test_deduct_inventory_sufficient_stock(self, mock_wear_part_stock, mock_stock_movement_log):
        """
        Kiểm tra khi tồn kho đủ để trừ hết số lượng yêu cầu.
        Với task yêu cầu 5 và actual_quantity = 5, nếu tồn kho ban đầu là 10,
        deduction sẽ trừ đi 5, cho stock giảm còn 5.
        """
        template = DummyTemplate("ABC")
        result = DummyResult(completed=True, actual_quantity=5)
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
            shortage=0,
            task=task
        )

    @patch("apps.wear_part_stock.services.StockMovementLog")
    @patch("apps.wear_part_stock.services.WearPartStock")
    def test_deduct_inventory_insufficient_stock(self, mock_wear_part_stock, mock_stock_movement_log):
        """
        Kiểm tra khi tồn kho không đủ để trừ hết số lượng yêu cầu, dẫn đến log báo thiếu hàng.
        Với task yêu cầu 5, nhưng tồn kho chỉ có 3, deduction sẽ trừ 3 và thiếu 2.
        """
        template = DummyTemplate("ABC")
        result = DummyResult(completed=True, actual_quantity=5)
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

# --- Các test khác (ví dụ, cho command import_stock) ---
# ...
