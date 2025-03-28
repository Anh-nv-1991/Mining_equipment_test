from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import EquipmentStatus
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.equipment_status.models import EquipmentStatus
from apps.maintenance.models import CompletedMaintenanceRecord
@receiver(post_save, sender=EquipmentStatus)
def update_equipment_status(sender, instance, **kwargs):
    """Cập nhật trạng thái của thiết bị khi có bản ghi mới trong EquipmentStatus"""
    if instance.equipment:
        instance.equipment.status = instance.status
        instance.equipment.save()
@receiver(post_save, sender=CompletedMaintenanceRecord)
def sync_status_from_completed(sender, instance, created, **kwargs):
    eq = instance.maintenance_record.equipment
    status_obj, _ = EquipmentStatus.objects.get_or_create(equipment=eq)
    # Cập nhật operation_team từ CompletedMaintenanceRecord nếu cần
    status_obj.operation_team = instance.maintenance_record.updated_by.username if instance.maintenance_record.updated_by else ''
    # Optionally lưu maintenance level & timestamp
    status_obj.updated_at = timezone.now()
    status_obj.save()