from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import EquipmentStatus

@admin.register(EquipmentStatus)
class EquipmentStatusAdmin(admin.ModelAdmin):
    list_display = ('equipment_name', 'equipment_category', 'operation_team',
                    'view_maintenance_history', 'updated_at')

    def equipment_name(self, obj):
        return obj.equipment.name

    def equipment_category(self, obj):
        return obj.equipment.category.name if obj.equipment and obj.equipment.category else ""

    def view_maintenance_history(self, obj):
        url = reverse("equipment_status:maintenance_history_for_equipment", args=[obj.equipment.id])
        return format_html('<a class="button" href="{}" target="_blank" '
            'style="display: inline-block; padding: 6px 12px; background: #198754; '  # Màu xanh lá đậm
            'color: white; border-radius: 5px; font-size: 14px; font-weight: bold; text-decoration: none;">'
            '🔍 View Completed Maintenance</a>', url)

    view_maintenance_history.short_description = "Maintenance History"
