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
            # Giả sử trong trường hợp đơn giản chỉ có 1 stock phù hợp
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
                remaining = 0
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
            # Cập nhật log hiện có thay vì tạo log mới với giá trị âm.
            existing_log = existing_logs.first()
            if existing_log and existing_log.stock:
                stock = existing_log.stock
                print(f"💰 Hoàn trả {refund_amount} vào {stock.manufacturer_id} (trước: {stock.stock_quantity})")
                stock.stock_quantity += refund_amount
                stock.save(update_fields=["stock_quantity"])
                # Cập nhật log: giảm số lượng trừ đi refund_amount.
                existing_log.quantity = existing_log.quantity - refund_amount
                existing_log.save(update_fields=['quantity'])
            else:
                print("⚠️ Không tìm thấy stock để hoàn trả")

    return logs

