from collections import OrderedDict
from collections import defaultdict

from django.shortcuts import get_object_or_404, render
from rest_framework import viewsets, mixins
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.equipment_management.models import Equipment
from apps.maintenance.models import CompletedMaintenanceRecord, IntermediateMaintenance
from .models import EquipmentStatus
from .serializers import EquipmentStatusSerializer
from rest_framework import filters

class EquipmentStatusViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    queryset = EquipmentStatus.objects.select_related('equipment')
    serializer_class = EquipmentStatusSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'equipment_id'
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['equipment__name', 'updated_at']
    search_fields = ['equipment__name']
def maintenance_history_for_equipment(request, equipment_id):
    """Hiển thị trang lịch sử bảo dưỡng (HTML) cho thiết bị."""
    equipment = get_object_or_404(Equipment, pk=equipment_id)
    status_obj, _ = EquipmentStatus.objects.get_or_create(equipment=equipment)
    records = status_obj.completed_maintenance_records().order_by('-start_time')

    intermediate_records = IntermediateMaintenance.objects.filter(equipment=equipment).order_by('-start_time')

    return render(request, 'admin/equipment_status/maintenance_recall.html', {
        'equipment': equipment,
        'records': records,
        'intermediate_records': intermediate_records,  # Thêm các bản ghi IntermediateMaintenance vào context
    })

def maintenance_record_readonly_view(request, record_id):
    comp = get_object_or_404(CompletedMaintenanceRecord, maintenance_record_id=record_id)

    # Chuẩn hóa snapshot thành uppercase-key dict
    temp = {
        key.upper(): list(zip(data.get("tasks", []), data.get("results", [])))
        for key, data in comp.tasks.items()
    }

    # Thứ tự mong muốn
    desired = [
        "REPLACEMENTTEMPLATE",
        "SUPPLEMENTTEMPLATE",
        "INSPECTIONTEMPLATE",
        "CLEANINGTEMPLATE",
    ]

    grouped_tasks = OrderedDict()
    # Add theo thứ tự desired
    for name in desired:
        if name in temp:
            grouped_tasks[name] = temp.pop(name)
    # Append các nhóm còn lại (nếu có)
    for name, items in temp.items():
        grouped_tasks[name] = items

    return render(request, "admin/equipment_status/completed_record_readonly.html", {
        "comp": comp,
        "grouped_tasks": grouped_tasks,
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def completed_record_detail(request, record_id):
    comp = get_object_or_404(CompletedMaintenanceRecord, pk=record_id)
    # Tạo map cho results theo task_id
    result_map = { r["task_id"]: r for r in comp.results }

    grouped_tasks = defaultdict(list)
    for task_dict in comp.tasks:
        t_id = task_dict["id"]
        r_dict = result_map.get(t_id, {})
        key = f"{task_dict['task_type']}template".upper()
        grouped_tasks[key].append((task_dict, r_dict))

    return render(request, "admin/equipment_status/completed_record_readonly.html",
                  {"comp": comp, "grouped_tasks": grouped_tasks})

    # JSON fallback
    return Response({
        "record": {
            "equipment": record.equipment.name,
            "category": record.equipment.category.name if record.equipment.category else "",
            "maintenance_level": record.get_maintenance_level_display(),
            "start_time": record.start_time.strftime("%Y-%m-%d %H:%M"),
            "end_time": record.end_time.strftime("%Y-%m-%d %H:%M") if record.end_time else "",
            "notes": comp.notes,
        },
        "replacement_tasks": grouped_tasks.get("REPLACEMENTTEMPLATE", []),
        "supplement_tasks": grouped_tasks.get("SUPPLEMENTTEMPLATE", []),
        "inspection_tasks": grouped_tasks.get("INSPECTIONTEMPLATE", []),
        "cleaning_tasks": grouped_tasks.get("CLEANINGTEMPLATE", []),
    })

def intermediate_readonly_view(request, pk):
    im = get_object_or_404(IntermediateMaintenance, pk=pk)
    return render(
        request,
        "admin/equipment_status/intermediate_record_readonly.html",
        {"object": im}
    )