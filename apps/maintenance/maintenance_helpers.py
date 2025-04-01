
import re
import math
from datetime import datetime
from django.db.models import Q
from apps.wear_part_stock.models import WearPartStock
from django.utils.safestring import mark_safe


def generate_record_id(record):
    cat_name = record.category.name if record.category and record.category.name else ""
    parts = cat_name.split("||", 1)
    cat_sub = parts[1] if len(parts) == 2 else cat_name
    cat_code = cat_sub.replace(" ", "").upper() if cat_sub else "XXX"

    equip_code = record.equipment.name.replace(" ", "")[:3].upper() if record.equipment and record.equipment.name else "EQP"
    level_str = f"{record.maintenance_level}"
    date_part = record.start_time.strftime("%y%m%d") if record.start_time else "000000"

    return f"{cat_code}-{equip_code}-{level_str}-{date_part}"

def calculate_shift_count(start: datetime, end: datetime) -> int:
    total_hours = (end - start).total_seconds() / 3600
    return math.ceil(total_hours / 8)

def generate_csv_filename(record) -> str:
    rid = generate_record_id(record)
    shift_count = calculate_shift_count(record.start_time, record.end_time)
    return f"{rid}_{shift_count}.csv"

def check_inventory_for_template(template):
    required = getattr(template, 'quantity', 0) or 0
    manufacturer_id = getattr(template, 'manufacturer_id', '') or ''
    codes = [c.strip() for c in re.split(r"[\/,]", manufacturer_id) if c.strip()]

    qs = WearPartStock.objects.filter(
        Q(manufacturer_id__in=codes) | Q(alternative_id__in=codes)
    )
    total_stock = sum(item.stock_quantity for item in qs)

    if total_stock >= required:
        return {"status": "ok", "available": total_stock, "shortage": 0}
    return {"status": "warning", "available": total_stock, "shortage": required - total_stock}

def sanitize_name(name: str) -> str:
    """
    Chuẩn hóa tên file/thư mục: bỏ ký tự đặc biệt, thay dấu cách bằng _, viết thường.
    Dùng để tạo tên thư mục an toàn trên hệ thống file.
    """
    if not name:
        return "unknown"
    name = name.strip().lower()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^\w\-]", "", name)
    return name

def get_replacement_status(result):
    """
    Trả về trạng thái hoàn thành của 1 ReplacementResult:
    - Not Started: chưa thay gì
    - Incomplete: thay 1 phần
    - Completed: thay đủ
    - Overdone: thay quá mức
    """
    if not result or not hasattr(result, 'actual_quantity') or not hasattr(result, 'task'):
        return "Invalid"

    planned = getattr(result.task, 'quantity', 0)
    actual = result.actual_quantity or 0

    if actual == 0:
        return "Not Started"
    elif actual < planned:
        return "Incomplete"
    elif actual == planned:
        return "Completed"
    else:
        return "Overdone"

def map_status_to_vietnamese(status):
    return {
        "Not Started": "Chưa thực hiện",
        "Incomplete": "Không đủ số lượng",
        "Completed": "Đã thực hiện",
        "Overdone": "Thừa số lượng yêu cầu",
        "Invalid": "Không xác định"
    }.get(status, status)

def get_grouped_data(completed_record):
    """
    Trả về cấu trúc dữ liệu đã nhóm:
    {
      "replacementtemplate": [(task_dict, result_dict), ...],
      "supplementtemplate": [...],
      "inspectiontemplate": [...],
      "cleaningtemplate": [...],
      "others": [...]
    }
    Hoặc tuỳ cấu trúc bạn cần.
    """
    tasks_field = completed_record.tasks
    results_field = completed_record.results

    # final_grouped: { "replacementtemplate": [(task, result), ...], ... }
    final_grouped = {}

    if isinstance(tasks_field, list):
        # Dữ liệu cũ: tasks là list phẳng
        # 1. Gom nhóm tasks
        grouped_temp = {}
        for t in tasks_field:
            ttype = t.get('task_type', 'others')
            grouped_temp.setdefault(ttype, []).append(t)
        # 2. Map result
        results_map = {r.get('task_id'): r for r in results_field}
        # 3. Ghép
        for ttype, tasks_list in grouped_temp.items():
            combined = []
            for t_dict in tasks_list:
                r_dict = results_map.get(t_dict.get('id'), {})
                combined.append((t_dict, r_dict))
            final_grouped[ttype] = combined
    elif isinstance(tasks_field, dict):
        # Dữ liệu mới: tasks là dict {"replacementtemplate": {"tasks": [...], "results": [...]}, ...}
        for ttype, data in tasks_field.items():
            combined = list(zip(data.get("tasks", []), data.get("results", [])))
            final_grouped[ttype] = combined

    return final_grouped

def render_grouped_table(grouped):
    """
    Tạo HTML table cho mỗi nhóm. Trả về chuỗi HTML đã mark_safe.
    """
    html = ""
    for group, items in grouped.items():
        group_upper = group.upper()
        html += f"<h3>{group_upper}</h3>"

        # Tuỳ group, dựng header khác nhau
        if group == "replacementtemplate":
            header = (
                "<tr>"
                "<th>Task ID</th><th>Task Name</th><th>Replacement Type</th>"
                "<th>Manufacturer ID</th><th>Alternative ID</th><th>Quantity</th>"
                "<th>Actual Quantity</th><th>Inventory Status</th><th>Status</th><th>Notes</th>"
                "</tr>"
            )
        elif group == "supplementtemplate":
            header = (
                "<tr>"
                "<th>Task ID</th><th>Task Name</th><th>Position</th>"
                "<th>Quantity</th><th>Completed</th><th>Notes</th>"
                "</tr>"
            )
        else:  # inspectiontemplate, cleaningtemplate, others
            header = (
                "<tr>"
                "<th>Task ID</th><th>Task Name</th><th>Condition</th><th>Notes</th>"
                "</tr>"
            )

        html += f"<table border='1' style='border-collapse: collapse; width:100%;'>{header}"

        for t_dict, r_dict in items:
            html += "<tr>"
            html += f"<td>{t_dict.get('id')}</td>"
            html += f"<td>{t_dict.get('task_name')}</td>"

            if group == "replacementtemplate":
                html += f"<td>{t_dict.get('replacement_type')}</td>"
                html += f"<td>{t_dict.get('manufacturer_id')}</td>"
                html += f"<td>{t_dict.get('alternative_id')}</td>"
                html += f"<td>{t_dict.get('quantity')}</td>"
                html += f"<td>{r_dict.get('actual_quantity')}</td>"
                html += f"<td>{r_dict.get('inventory_status')}</td>"
                html += f"<td>{r_dict.get('status')}</td>"
                html += f"<td>{r_dict.get('notes')}</td>"
            elif group == "supplementtemplate":
                html += f"<td>{t_dict.get('position')}</td>"
                html += f"<td>{t_dict.get('quantity')}</td>"
                completed = "Đã bổ sung" if r_dict.get("completed") else "Chưa bổ sung"
                html += f"<td>{completed}</td>"
                html += f"<td>{r_dict.get('notes')}</td>"
            else:
                # inspectiontemplate, cleaningtemplate, others
                html += f"<td>{r_dict.get('condition')}</td>"
                html += f"<td>{r_dict.get('notes')}</td>"

            html += "</tr>"
        html += "</table><br/>"
    return mark_safe(html)