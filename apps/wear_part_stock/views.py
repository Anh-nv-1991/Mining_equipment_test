from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.maintenance.models import MaintenanceRecord
from .models import WearPartStock, StockMovementLog

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deduct_stock_view(request, record_id):
    record = MaintenanceRecord.objects.get(pk=record_id)
    logs = []
    for task in record.tasks.filter(content_type__model='replacementtemplate'):
        result = getattr(task, 'replacement_result', None)
        if result and result.completed:
            codes = [c.strip() for c in re.split(r"[\/,]", task.template.manufacturer_id)]
            shortage = WearPartStock.deduct_parts(codes, task.quantity)
            log = StockMovementLog.objects.create(
                stock=WearPartStock.objects.filter(manufacturer_id__in=codes).first(),
                maintenance_record=record,
                quantity=task.quantity - shortage,
                shortage=shortage
            )
            logs.append({
                "part": str(log.stock),
                "quantity": log.quantity,
                "shortage": log.shortage
            })
    return Response({"success": True, "deductions": logs})
