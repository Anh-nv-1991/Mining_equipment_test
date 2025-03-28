from collections import OrderedDict

from django.contrib import admin
from django.db import transaction
from django.utils.html import format_html
from apps.equipment_management.models import Equipment
from apps.maintenance.models import (
    MaintenanceRecord, MaintenanceTask,
    SupplementTemplate, ReplacementTemplate,
    InspectionTemplate, CleaningTemplate,
    ReplacementResult, SupplementResult,
    InspectionResult, CleaningResult,
    IntermediateMaintenance,
)
from .maintenance_helpers import get_replacement_status, get_grouped_data, render_grouped_table
from .models import CompletedMaintenanceRecord


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    change_list_template = "admin/maintenance/change_list.html"
    list_display = (
        'record_id', 'category', 'equipment_name', 'engine_hours',
        'maintenance_level', 'start_time', 'end_time',
        'created_by_name', 'view_procedure', 'view_history','view_complete'
    )
    exclude = ('updated_by',)
    list_filter = ('category', 'equipment', 'maintenance_level')
    search_fields = ('record_id', 'equipment__name', 'category__name')
    readonly_fields = ('engine_hours', 'created_by', 'record_id')

    class Media:
        js = ('admin/js/custom_admin.js', 'admin/js/adjust_fields.js',)

    def equipment_name(self, obj):
        return obj.equipment.name if obj.equipment else "N/A"
    equipment_name.short_description = "Equipment Name"

    def created_by_name(self, obj):
        return obj.created_by.username if obj.created_by else "-"
    created_by_name.short_description = "Created By"

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def view_procedure(self, obj):
        return format_html(
            '<div style="text-align:center;">'
            '<a href="#" class="open-modal" data-record-id="{}" '
            'style="padding:6px 12px; background:#007bff; color:white; border-radius:5px;">'
            '🔍 View Maintenance Procedure</a>'
            '</div>',
            obj.pk
        )

    def view_history(self, obj):
        return format_html(
            '<div style="text-align:center;">'
            '<a href="#" class="open-history-modal" data-record-id="{}" '
            'style="padding:6px 12px; background:#28a745; color:white; border-radius:5px;">'
            '📜 View History</a>'
            '</div>',
            obj.pk
        )

    def view_complete(self, obj):
        return format_html(
            '<div style="text-align:center;">'
            '<a href="#" class="complete-btn" data-record-id="{}" '
            'style="padding:6px 12px; background:#dc3545; color:white; border-radius:5px;">'
            '✅ Complete</a>'
            '</div>',
            obj.pk
        )

    def save_model(self, request, obj, form, change):
        # Xác định xem đây là bản ghi mới hay không trước khi lưu
        is_new = obj.pk is None

        if not obj.created_by:
            obj.created_by = request.user

        # Lưu bản ghi
        super().save_model(request, obj, form, change)

        # Nếu là bản ghi mới, tạo các MaintenanceTask dựa trên các template (direct & inherited)
        if is_new:
            with transaction.atomic():
                template_classes = [ReplacementTemplate, SupplementTemplate, InspectionTemplate, CleaningTemplate]
                for tmpl_cls in template_classes:
                    direct_templates = list(tmpl_cls.objects.filter(
                        maintenance_level=obj.maintenance_level,
                        category=obj.category
                    ))
                    inherited_templates = list(tmpl_cls.objects.filter(
                        maintenance_level__lt=obj.maintenance_level,
                        category=obj.category,
                        inherit=True
                    ))
                    all_templates = sorted(direct_templates + inherited_templates, key=lambda t: t.id)
                    for tmpl in all_templates:
                        MaintenanceTask.objects.create(
                            maintenance_record=obj,
                            template=tmpl,
                            quantity=getattr(tmpl, 'quantity', 1)
                        )

@admin.register(ReplacementTemplate)
class ReplacementTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'maintenance_level', 'task_name', 'replacement_type','quantity', 'manufacturer_id', 'alternative_id')
    list_filter = ('category', 'maintenance_level')
    search_fields = ('task_name',)

@admin.register(SupplementTemplate)
class SupplementTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'maintenance_level', 'change_type', 'position', 'quantity', 'inherit')
    list_filter = ('category', 'maintenance_level', 'inherit')
    search_fields = ('change_type', 'position')

@admin.register(InspectionTemplate)
class InspectionTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'maintenance_level', 'task_name')
    list_filter = ('category', 'maintenance_level')
    search_fields = ('task_name',)

@admin.register(CleaningTemplate)
class CleaningTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'maintenance_level', 'task_name')
    list_filter = ('category', 'maintenance_level')
    search_fields = ('task_name',)

@admin.register(ReplacementResult)
class ReplacementResultAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'task',
        'actual_quantity',
        'get_status',
    )
    list_filter = ('actual_quantity',)
    search_fields = ('task__name',)

    fields = (
        'task',
        'actual_quantity',
    )

    readonly_fields = ('get_status',)

    def get_status(self, obj):
        status = get_replacement_status(obj)
        color_map = {
            'Not Started': 'red',
            'Incomplete': 'orange',
            'Completed': 'green',
            'Overdone': 'purple',
            'Invalid': 'gray'
        }
        color = color_map.get(status, 'black')
        return format_html('<span style="color:{}; font-weight:bold;">{}</span>', color, status)

@admin.register(SupplementResult)
class SupplementResultAdmin(admin.ModelAdmin):
    list_display = ('task','completed', 'notes')
    list_filter = ('completed',)

@admin.register(InspectionResult)
class InspectionResultAdmin(admin.ModelAdmin):
    list_display = ('task', 'condition', 'notes')
    search_fields = ('condition',)

@admin.register(CleaningResult)
class CleaningResultAdmin(admin.ModelAdmin):
    list_display = ('task', 'condition', 'notes')
    search_fields = ('condition',)

@admin.register(CompletedMaintenanceRecord)
class CompletedMaintenanceRecordAdmin(admin.ModelAdmin):
    exclude = ("tasks", "results",)
    readonly_fields = ("display_grouped_tasks",)
    list_display = ("record_id", "maintenance_record", "completed_at")

    def display_grouped_tasks(self, obj):
        grouped = get_grouped_data(obj)

        # Định nghĩa thứ tự hiển thị ngược lại
        desired = [
            "replacementtemplate",
            "supplementtemplate",
            "inspectiontemplate",
            "cleaningtemplate",
        ]
        ordered = OrderedDict()
        for key in desired:
            if key in grouped:
                ordered[key] = grouped[key]
        # Thêm các nhóm khác (nếu có)
        for key, value in grouped.items():
            if key not in ordered:
                ordered[key] = value

        return render_grouped_table(ordered)
    display_grouped_tasks.short_description = "Grouped Tasks & Results"

@admin.register(IntermediateMaintenance)
class IntermediateMaintenanceAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'category', 'start_time', 'end_time', 'location', 'engine_hours')
    list_filter = ('category', 'start_time', 'end_time')
    search_fields = ('equipment__name', 'category__name', 'location')
    readonly_fields = ('engine_hours',)
    class Media:
        js = ('admin/js/custom_admin.js',)  # Đảm bảo custom_admin.js được tải

    def save_model(self, request, obj, form, change):
        # Cập nhật trường updated_by từ người dùng hiện tại
        if not obj.updated_by:
            obj.updated_by = request.user

        # Lấy giá trị engine_hours từ Equipment nếu chưa có giá trị
        if not obj.engine_hours and obj.equipment:
            obj.engine_hours = obj.equipment.engine_hours  # Lấy engine_hours từ Equipment

        super().save_model(request, obj, form, change)