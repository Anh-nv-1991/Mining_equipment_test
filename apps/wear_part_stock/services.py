# wear_part_stock/services.py
from apps.maintenance.maintenance_helpers import get_replacement_status
from django.db import models

def deduct_inventory_for_record(record):
    logs = []

    for task in record.tasks.filter(content_type__model='replacementtemplate'):
        result = getattr(task, 'replacement_result', None)
        print(f"\n🧪 Task ID: {task.id} | Template: {task.template}")

        if not result:
            print("❌ Không có replacement_result")
            continue
        if not result.completed:
            print("⚠️ Task chưa được đánh dấu hoàn thành")
            continue

        codes = [c.strip() for c in (task.template.manufacturer_id or "").split("/")]
        required = task.quantity
        print(f"🔍 Mã tra: {codes} | Số lượng yêu cầu: {required}")

        stocks = WearPartStock.objects.filter(
            models.Q(manufacturer_id__in=codes) | models.Q(alternative_id__in=codes)
        ).order_by('-stock_quantity')

        print(f"🔎 Tìm thấy {stocks.count()} stock phù hợp")

        for stock in stocks:
            if required <= 0:
                break

            deduct = min(stock.stock_quantity, required)
            print(f"✅ Trừ {deduct} từ {stock.manufacturer_id} (trước: {stock.stock_quantity})")

            if deduct <= 0:
                continue

            stock.stock_quantity -= deduct
            stock.save(update_fields=["stock_quantity"])
            logs.append(StockMovementLog.objects.create(
                stock=stock,
                maintenance_record=record,
                quantity=deduct,
                shortage=0
            ))
            required -= deduct

        if required > 0:
            print(f"🚨 Không đủ hàng, thiếu {required} đơn vị")
            logs.append(StockMovementLog.objects.create(
                stock=None,
                maintenance_record=record,
                quantity=0,
                shortage=required
            ))

            print(f"⚠️ Thiếu {required} đơn vị phụ tùng cho: {codes}")

    return logs
from apps.wear_part_stock.models import WearPartStock, StockMovementLog
# hàm sync số liệu tồn kho
def sync_inventory_with_record(record):
    tasks = record.tasks.filter(content_type__model='replacementtemplate')
    logs = StockMovementLog.objects.filter(maintenance_record=record)

    # Xoá log và hoàn trả kho nếu cần
    for log in logs:
        task = getattr(log, 'task', None)
        if not task:
            continue

        # Nếu task không còn hoàn thành → rollback stock
        result = getattr(task, 'replacement_result', None)
        completed_now = getattr(result, 'completed', False)

        if not completed_now:
            if log.stock:
                log.stock.stock_quantity += log.quantity
                log.stock.save(update_fields=["stock_quantity"])
            log.delete()
            continue  # bỏ qua phần trừ lại bên dưới

    # Trừ lại theo actual_quantity mới
    for task in tasks:
        result = getattr(task, 'replacement_result', None)
        if not result:
            continue

        status = get_replacement_status(result)
        # Bỏ qua nếu chưa hoàn thành (Not Started, Incomplete, Overdone)
        if status != "Completed":
            continue

        actual_qty = getattr(result, 'actual_quantity', 0)
        if actual_qty <= 0:
            continue

        # Đã từng có log? → bỏ qua để không trừ lại
        if logs.filter(task_id=task.id).exists():
            continue

        codes = [c.strip() for c in (task.template.manufacturer_id or "").split("/")]
        remaining = actual_qty

        stocks = WearPartStock.objects.filter(
            models.Q(manufacturer_id__in=codes) | models.Q(alternative_id__in=codes)
        ).order_by('-stock_quantity')

        for stock in stocks:
            if remaining <= 0:
                break

            deduct = min(stock.stock_quantity, remaining)
            if deduct <= 0:
                continue

            stock.stock_quantity -= deduct
            stock.save(update_fields=["stock_quantity"])

            StockMovementLog.objects.create(
                stock=stock,
                maintenance_record=record,
                task=task,
                quantity=deduct,
                shortage=0,
            )
            remaining -= deduct

        if remaining > 0:
            StockMovementLog.objects.create(
                stock=None,
                maintenance_record=record,
                task=task,
                quantity=0,
                shortage=remaining,
            )
