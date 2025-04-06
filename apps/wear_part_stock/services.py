from apps.maintenance.maintenance_helpers import get_replacement_status
from django.db import models
from apps.wear_part_stock.models import WearPartStock, StockMovementLog


def deduct_inventory_for_record(record):
    logs = []

    for task in record.tasks.filter(content_type__model='replacementtemplate'):
        result = getattr(task, 'replacement_result', None)
        print(f"\n🧪 Task ID: {task.id} | Template: {task.template}")
        if not result:
            print("❌ Không có replacement_result")
            continue
        existing_logs = StockMovementLog.objects.filter(maintenance_record=record, task=task)
        if not existing_logs.exists() and not result.completed:
            print("⚠️ Task chưa được đánh dấu hoàn thành")
            continue
        # Sử dụng actual_quantity từ result làm số lượng yêu cầu hiện tại
        required_new = result.actual_quantity
        print(f"Required (actual quantity): {required_new}")

        # Tính tổng số đã trừ từ các log cho task này
        existing_logs = StockMovementLog.objects.filter(maintenance_record=record, task=task)
        total_deducted = sum(log.quantity for log in existing_logs)
        delta = required_new - total_deducted
        print(f"Total deducted: {total_deducted}, Delta: {delta}")
        if delta == 0:
            continue

        codes = [c.strip() for c in (task.template.manufacturer_id or "").split("/")]
        stocks = WearPartStock.objects.filter(
            models.Q(manufacturer_id__in=codes) | models.Q(alternative_id__in=codes)
        ).order_by('-stock_quantity')
        print(f"🔎 Tìm thấy {stocks.count()} stock phù hợp")

        if delta > 0:
            remaining = delta
            if stocks.count() == 1:
                stock = stocks.first()
                deduct = min(stock.stock_quantity, remaining)
                stock.stock_quantity -= deduct
                stock.save(update_fields=["stock_quantity"])
                logs.append(StockMovementLog.objects.create(
                    stock=stock,
                    maintenance_record=record,
                    task=task,
                    quantity=deduct,
                    shortage=remaining - deduct
                ))
            else:
                for stock in stocks:
                    if remaining <= 0:
                        break
                    deduct = min(stock.stock_quantity, remaining)
                    if deduct <= 0:
                        continue
                    stock.stock_quantity -= deduct
                    stock.save(update_fields=["stock_quantity"])
                    logs.append(StockMovementLog.objects.create(
                        stock=stock,
                        maintenance_record=record,
                        task=task,
                        quantity=deduct,
                        shortage=0
                    ))
                    remaining -= deduct
                if remaining > 0:
                    logs.append(StockMovementLog.objects.create(
                        stock=None,
                        maintenance_record=record,
                        task=task,
                        quantity=0,
                        shortage=remaining
                    ))

        elif delta < 0:

            refund_amount = -delta

            # Re-fetch existing logs cho task sau khi kết quả đã update.

            existing_logs = StockMovementLog.objects.filter(maintenance_record=record, task=task)

            if existing_logs.exists():

                existing_log = existing_logs.first()

                if existing_log and existing_log.stock:

                    stock = existing_log.stock

                    print(f"💰 Hoàn trả {refund_amount} vào {stock.manufacturer_id} (trước: {stock.stock_quantity})")

                    stock.stock_quantity += refund_amount

                    stock.save(update_fields=["stock_quantity"])

                    # Update log: giảm số lượng trừ đi refund_amount.

                    existing_log.quantity = existing_log.quantity - refund_amount

                    existing_log.save(update_fields=['quantity'])

                else:

                    print("⚠️ Không tìm thấy stock để hoàn trả")

            else:

                print("⚠️ Không có log để hoàn trả")

    return logs
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

