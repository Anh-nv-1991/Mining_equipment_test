import os
from openpyxl import Workbook
from django.conf import settings

from .maintenance_helpers import calculate_shift_count, sanitize_name, get_replacement_status, map_status_to_vietnamese

def export_record_to_excel(record):
    """
    Ghi file Excel cho một MaintenanceRecord đã hoàn thành.
    Xóa file cũ nếu có cùng record_pk trước khi ghi.
    """
    record_id = record.record_id
    completed = getattr(record, 'completed_record', None)
    record_pk = completed.pk if completed else None

    folder = os.path.join(
        settings.CSV_EXPORT_ROOT,
        sanitize_name(record.category.name),
        sanitize_name(record.equipment.name)
    )
    os.makedirs(folder, exist_ok=True)

    # 🔁 XÓA FILE CŨ THEO record_pk
    try:
        for fname in os.listdir(folder):
            if fname.endswith(".xlsx") and record_pk and f"_{record_pk}_" in fname:
                os.remove(os.path.join(folder, fname))
    except Exception:
        pass  # Có thể thêm logging ở đây nếu cần

    # 📄 Tên file mới
    shift_count = calculate_shift_count(record.start_time, record.end_time)
    filename = f"{record_id}_{record_pk}_{shift_count}.xlsx"
    file_path = os.path.join(folder, filename)

    wb = Workbook()
    wb.remove(wb.active)

    # Sheet định nghĩa
    sheet_defs = {
        "Replacement Maintenance": {
            "model": "replacementtemplate",
            "headers": ["#", "Task Name", "Replacement Type", "Manufacturer ID", "Alternative ID",
                        "Quantity","Actual Quantity", "Check Inventory", "Completed", "Notes"]
        },
        "Supplement Maintenance": {
            "model": "supplementtemplate",
            "headers": ["#", "Position", "Supplement Type", "Quantity", "Completed", "Notes"]
        },
        "Inspection Maintenance": {
            "model": "inspectiontemplate",
            "headers": ["#", "Task Name", "Condition", "Notes"]
        },
        "Cleaning Maintenance": {
            "model": "cleaningtemplate",
            "headers": ["#", "Task Name", "Condition", "Notes"]
        }
    }

    result_map = {
        "replacementtemplate": "replacement_result",
        "supplementtemplate": "supplement_result",
        "inspectiontemplate": "inspection_result",
        "cleaningtemplate": "cleaning_result",
    }

    tasks_qs = record.tasks.select_related(
        "replacement_result", "supplement_result", "inspection_result", "cleaning_result"
    )

    for sheet_name, cfg in sheet_defs.items():
        ws = wb.create_sheet(sheet_name)
        ws.append(cfg["headers"])

        model_name = cfg["model"]
        related_name = result_map[model_name]

        for idx, task in enumerate(tasks_qs.filter(content_type__model=model_name), start=1):
            tmpl = task.template
            result = getattr(task, related_name, None)

            if result:
                if model_name == "replacementtemplate":
                    raw_status = get_replacement_status(result)
                else:
                    raw_status = "Completed" if getattr(result, "completed", False) else "Not Started"
            else:
                raw_status = "Not Started"
            completed = map_status_to_vietnamese(raw_status)
            notes = getattr(result, "notes", "") if result else ""
            condition = getattr(result, "condition", "") if result else ""
            quantity = task.quantity

            if model_name == "replacementtemplate":
                inv = tmpl.check_inventory()
                inv_status = "OK" if inv.get("status") == "ok" else f"Thiếu - {inv.get('shortage', 0)}"
                actual_qty = getattr(result, "actual_quantity", 0) if result else 0
                row = [
                    idx, tmpl.task_name, tmpl.replacement_type, tmpl.manufacturer_id,
                    tmpl.alternative_id, quantity,actual_qty, inv_status, completed, notes
                ]
            elif model_name == "supplementtemplate":
                row = [
                    idx, getattr(tmpl, "task_name", tmpl.change_type),
                    tmpl.position or "", quantity, completed, notes
                ]
            else:
                row = [idx, tmpl.task_name, condition, notes]

            ws.append(row)

    try:
        wb.save(file_path)
    except PermissionError:
        # Báo lỗi rõ ràng lên caller
        raise PermissionError(f"File Excel đang mở — vui lòng đóng file tại:\n{file_path}")
    return file_path
