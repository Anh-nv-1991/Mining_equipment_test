from django.shortcuts import render, get_object_or_404
from .models import MaintenanceRecord
from apps.equipment_management.models import Equipment
from django.http import JsonResponse


def maintenance_modal_view(request, record_id):
    if not request.user.is_authenticated:
        return render(request, "403.html", status=403)
    record = get_object_or_404(MaintenanceRecord, pk=record_id)
    return render(request, "admin/maintenance/maintenance_procedure_modal.html", {"record": record})


def get_equipment_by_category(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    category_id = request.GET.get("category_id")
    try:
        equipments = Equipment.objects.filter(category_id=int(category_id)).values("id", "name") if category_id else []
        return JsonResponse({"equipments": list(equipments)})
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid category_id"}, status=400)