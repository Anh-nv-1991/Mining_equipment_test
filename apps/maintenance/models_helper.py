# models_helper.py
from .maintenance_helpers import get_replacement_status, map_status_to_vietnamese


def group_tasks_and_results(maintenance_record):
    grouped = {
        "replacementtemplate": {"tasks": [], "results": []},
        "supplementtemplate": {"tasks": [], "results": []},
        "inspectiontemplate": {"tasks": [], "results": []},
        "cleaningtemplate": {"tasks": [], "results": []},
    }

    tasks = maintenance_record.tasks.all().order_by('id')

    for t in tasks:
        model_name = t.content_type.model.lower()
        template = t.template

        # Chuẩn hóa task_name theo loại
        if model_name == "supplementtemplate":
            task_name = template.position  # "Mỡ", "Dầu TO30", ...
        elif hasattr(template, "task_name"):
            task_name = template.task_name
        else:
            task_name = ""

        task_dict = {
            "id": t.id,
            "task_name": task_name,
            "quantity": t.quantity,
            "task_type": model_name,
        }

        if model_name == "replacementtemplate":
            task_dict.update({
                "replacement_type": template.replacement_type,
                "manufacturer_id": template.manufacturer_id,
                "alternative_id": template.alternative_id,
            })

        if model_name == "supplementtemplate":
            task_dict.update({
                "position": template.change_type,
            })

        # Build result
        result = (
            getattr(t, 'replacement_result', None)
            or getattr(t, 'supplement_result', None)
            or getattr(t, 'inspection_result', None)
            or getattr(t, 'cleaning_result', None)
        )

        result_dict = {
            "task_id": t.id,
            "notes": getattr(result, "notes", ""),
            "condition": getattr(result, "condition", ""),
            "actual_quantity": getattr(result, "actual_quantity", 0),
            "status": map_status_to_vietnamese(get_replacement_status(result)),
        }

        if model_name == "replacementtemplate":
            result_dict["inventory_status"] = template.check_inventory().get("status", "")

        if model_name == "supplementtemplate":
            result_dict["completed"] = getattr(result, "completed", False)

        # Phân nhóm
        if model_name not in grouped:
            grouped.setdefault("others", {"tasks": [], "results": []})
            grouped["others"]["tasks"].append(task_dict)
            grouped["others"]["results"].append(result_dict)
        else:
            grouped[model_name]["tasks"].append(task_dict)
            grouped[model_name]["results"].append(result_dict)

    return grouped