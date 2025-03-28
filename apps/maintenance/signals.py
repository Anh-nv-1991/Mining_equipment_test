from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MaintenanceRecord, CompletedMaintenanceRecord

@receiver(post_save, sender=MaintenanceRecord)
def sync_snapshot_on_end_time_change(sender, instance, **kwargs):
    comp = getattr(instance, 'completed_record', None)
    if comp and instance.end_time and comp.completed_at != instance.end_time:
        comp.completed_at = instance.end_time
        comp.save(update_fields=["completed_at"])           # lưu completed_at trước
        comp.save_tasks_and_results()