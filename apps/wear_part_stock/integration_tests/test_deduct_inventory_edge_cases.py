import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from apps.maintenance.test_factories.maintenance_factories import (
    MaintenanceRecordFactory,
    MaintenanceTaskFactory,
    ReplacementTemplateFactory,
    CompletedMaintenanceRecordFactory
)
from apps.wear_part_stock.integration_tests.wear_part_stock_factories import WearPartStockFactory
from apps.wear_part_stock.models import StockMovementLog
from apps.wear_part_stock.services import deduct_inventory_for_record
from apps.maintenance.models import ReplacementResult

# Thêm property 'completed' cho ReplacementResult: hoàn thành nếu actual_quantity >= task.quantity
ReplacementResult.completed = property(lambda self: self.actual_quantity >= self.task.quantity)


@pytest.mark.django_db
def test_deduct_inventory_only_once():
    user = User.objects.create_user(username="testuser", password="password")

    record = MaintenanceRecordFactory(created_by=user)
    replacement_template = ReplacementTemplateFactory(quantity=2, manufacturer_id="M001")
    task = MaintenanceTaskFactory(maintenance_record=record, template=replacement_template, quantity=2)

    # Cập nhật content_type cho task
    ct = ContentType.objects.get_for_model(replacement_template.__class__)
    task.content_type = ct
    task.save(update_fields=['content_type'])

    # Tạo ReplacementResult cho task: actual_quantity = task.quantity (2)
    ReplacementResult.objects.create(
        task=task,
        actual_quantity=2,
        notes="Test replacement result"
    )

    record.end_time = timezone.now()
    record.save(update_fields=["end_time"])
    CompletedMaintenanceRecordFactory(maintenance_record=record, completed_at=record.end_time)

    # Tạo tồn kho: số lượng ban đầu là 10
    stock = WearPartStockFactory(manufacturer_id="M001", stock_quantity=10)

    # Lần deduction đầu tiên: với actual_quantity=2, stock giảm từ 10 xuống 8
    deduct_inventory_for_record(record)
    stock.refresh_from_db()
    assert stock.stock_quantity == 8, f"Expected stock_quantity 8 after first deduction, got {stock.stock_quantity}"

    logs = StockMovementLog.objects.filter(maintenance_record=record, task=task)
    assert logs.count() == 1, f"Expected 1 log entry after first deduction, got {logs.count()}"

    # Lần deduction thứ hai: không thay đổi vì delta = 0
    deduct_inventory_for_record(record)
    stock.refresh_from_db()
    assert stock.stock_quantity == 8, f"After second deduction call, expected stock_quantity remains 8, got {stock.stock_quantity}"
    logs = StockMovementLog.objects.filter(maintenance_record=record, task=task)
    assert logs.count() == 1, f"After second deduction call, expected log entry count remains 1, got {logs.count()}"


@pytest.mark.django_db
def test_deduct_inventory_insufficient_stock():
    user = User.objects.create_user(username="testuser2", password="password")

    record = MaintenanceRecordFactory(created_by=user)
    replacement_template = ReplacementTemplateFactory(quantity=2, manufacturer_id="M002")
    task = MaintenanceTaskFactory(maintenance_record=record, template=replacement_template, quantity=2)

    ct = ContentType.objects.get_for_model(replacement_template.__class__)
    task.content_type = ct
    task.save(update_fields=['content_type'])

    ReplacementResult.objects.create(
        task=task,
        actual_quantity=2,
        notes="Test replacement result"
    )

    record.end_time = timezone.now()
    record.save(update_fields=["end_time"])
    CompletedMaintenanceRecordFactory(maintenance_record=record, completed_at=record.end_time)

    # Tạo tồn kho không đủ: chỉ có 1
    stock = WearPartStockFactory(manufacturer_id="M002", stock_quantity=1)

    deduct_inventory_for_record(record)
    stock.refresh_from_db()
    # Với actual_quantity=2, tồn kho chỉ có 1, deduction sẽ trừ hết tồn kho (1) và shortage = 1.
    assert stock.stock_quantity == 0, f"Expected stock_quantity 0, got {stock.stock_quantity}"

    logs = StockMovementLog.objects.filter(maintenance_record=record, task=task)
    assert logs.count() == 1, f"Expected 1 log entry, got {logs.count()}"
    log_entry = logs.first()
    assert log_entry.quantity == 1, f"Expected deducted quantity 1, got {log_entry.quantity}"
    assert log_entry.shortage == 1, f"Expected shortage 1, got {log_entry.shortage}"


@pytest.mark.django_db
def test_deduct_inventory_update_reversal():
    user = User.objects.create_user(username="testuser3", password="password")

    record = MaintenanceRecordFactory(created_by=user)
    replacement_template = ReplacementTemplateFactory(quantity=2, manufacturer_id="M003")
    task = MaintenanceTaskFactory(maintenance_record=record, template=replacement_template, quantity=2)

    ct = ContentType.objects.get_for_model(replacement_template.__class__)
    task.content_type = ct
    task.save(update_fields=['content_type'])

    rep_result = ReplacementResult.objects.create(
        task=task,
        actual_quantity=2,
        notes="Initial replacement result"
    )

    record.end_time = timezone.now()
    record.save(update_fields=["end_time"])
    CompletedMaintenanceRecordFactory(maintenance_record=record, completed_at=record.end_time)

    stock = WearPartStockFactory(manufacturer_id="M003", stock_quantity=10)

    # Lần deduction đầu tiên: với actual_quantity=2, stock giảm từ 10 xuống 8
    deduct_inventory_for_record(record)
    stock.refresh_from_db()
    assert stock.stock_quantity == 8, f"After initial deduction, expected stock_quantity 8, got {stock.stock_quantity}"
    initial_logs = StockMovementLog.objects.filter(maintenance_record=record, task=task)
    initial_net = sum(log.quantity for log in initial_logs)
    assert initial_net == 2, f"Expected initial net deduction 2, got {initial_net}"

    # Giả lập cập nhật kết quả: thay đổi rep_result.actual_quantity từ 2 xuống 1
    rep_result.actual_quantity = 1
    rep_result.save()

    # Gọi lại deduction để đồng bộ lại tồn kho theo kết quả mới (update reversal)
    deduct_inventory_for_record(record)
    stock.refresh_from_db()
    # Mong đợi: hoàn trả 1 đơn vị, tồn kho tăng từ 8 lên 9
    assert stock.stock_quantity == 9, f"After update reversal, expected stock_quantity 9, got {stock.stock_quantity}"

    updated_logs = StockMovementLog.objects.filter(maintenance_record=record, task=task)
    updated_net = sum(log.quantity for log in updated_logs)
    assert updated_net == 1, f"After update reversal, expected net deduction of 1, got {updated_net}"
