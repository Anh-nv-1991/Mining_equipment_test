from django.shortcuts import get_object_or_404
from apps.maintenance.models import CompletedMaintenanceRecord, MaintenanceTask
from collections import defaultdict

def get_completed_record_and_tasks(record_id):
    comp = get_object_or_404(CompletedMaintenanceRecord, maintenance_record_id=record_id)
    tasks = MaintenanceTask.objects.filter(maintenance_record=comp.maintenance_record)
    grouped = defaultdict(list)

    for t in tasks:
        model = t.content_type.model.lower()
        tmpl = t.template
        result = getattr(t, f"{model}_result", None)
        task_dict = {}
        result_dict = {}

        if model == 'replacementtemplate':
            task_dict = {
                'task_name': tmpl.task_name,
                'replacement_type': tmpl.replacement_type,
                'manufacturer_id': tmpl.manufacturer_id,
                'alternative_id': tmpl.alternative_id,
                'quantity': t.quantity
            }
            inv = tmpl.check_inventory()
            result_dict = {
                'completed': getattr(result, 'actual_quantity', 0) >= t.quantity,
                'actual_quantity': getattr(result, 'actual_quantity', 0),
                'inventory_status': inv.get('status'),
                'notes': getattr(result, 'notes', '')
            }
        elif model == 'supplementtemplate':
            task_dict = {'change_type': tmpl.change_type, 'position': tmpl.position, 'quantity': t.quantity}
            result_dict = {'completed': getattr(result, 'completed', False), 'notes': getattr(result, 'notes', '')}
        elif model in ['inspectiontemplate', 'cleaningtemplate']:
            task_dict = {'task_name': tmpl.task_name}
            result_dict = {'condition': getattr(result, 'condition', ''), 'notes': getattr(result, 'notes', '')}

        grouped[model.upper()].append((task_dict, result_dict))

    return comp, dict(grouped)
