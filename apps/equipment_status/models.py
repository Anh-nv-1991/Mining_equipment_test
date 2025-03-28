from django.db import models
from apps.equipment_management.models import Equipment

class EquipmentStatus(models.Model):
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='status')
    operation_team = models.CharField(max_length=255, verbose_name="Operation Team", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Equipment Status"
        verbose_name_plural = "Equipment Statuses"

    def __str__(self):
        return f"Status of {self.equipment.name}"

    def completed_maintenance_records(self):
        return self.equipment.maintenance_records.filter(completed_record__isnull=False)
