import os

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.equipment_management.models import EquipmentCategories, Equipment
from .maintenance_helpers import (
    generate_record_id,
    check_inventory_for_template,
    sanitize_name
)
from .models_helper import group_tasks_and_results

MAINTENANCE_LEVEL_CHOICES = [
    (250, "Maintenance 250h"),
    (500, "Maintenance 500h"),
    (1000, "Maintenance 1000h"),
    (2000, "Maintenance 2000h"),
    (4000, "Maintenance 4000h"),
    (5000, "Maintenance 5000h"),
    (8000, "Maintenance 8000h"),
]

class MaintenanceRecord(models.Model):
    category = models.ForeignKey(
        EquipmentCategories, on_delete=models.CASCADE, verbose_name="Category"
    )
    equipment = models.ForeignKey(
        Equipment, on_delete=models.CASCADE, related_name="maintenance_records", verbose_name="Equipment"
    )
    # Lưu số giờ bảo dưỡng dưới dạng số, với 5 giá trị cố định
    maintenance_level = models.PositiveIntegerField(
        choices=MAINTENANCE_LEVEL_CHOICES,
        verbose_name="Maintenance Level"
    )
    location = models.CharField(max_length=255, verbose_name="Maintenance Location")
    start_time = models.DateTimeField(verbose_name="Start Time")
    end_time = models.DateTimeField(blank=True, null=True, verbose_name="End Time")
    responsible_units = models.TextField(verbose_name="Responsible Units")
    created_by = models.ForeignKey(
        User, related_name='created_maintenance_records',
        on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Created By"
    )
    updated_by = models.ForeignKey(
        User, related_name='updated_maintenance_records',
        on_delete=models.SET_NULL, null=True, blank=True, default=None, verbose_name="Updated By"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        # Thay self.equipment bằng self.equipment.name
            return f"{self.equipment.name} ({self.category}) - {self.maintenance_level}h"

    class Meta:
        verbose_name = "01. Maintenance Record"
        verbose_name_plural = "01. Maintenance Records"

    def engine_hours(self):
        return self.equipment.engine_hours if self.equipment else None
    engine_hours.short_description = "Engine Hours"

    @property
    def record_id(self):
        """
        Tạo mã định danh duy nhất cho bản ghi bảo dưỡng dùng để tìm kiếm, liên kết lịch sử.
        """
        return generate_record_id(self)

    @property
    def ordered_tasks(self):
        """
        Trả về danh sách MaintenanceTask được gộp từ các mẫu của cấp hiện tại và các mẫu kế thừa
        (từ các cấp thấp hơn có cờ inherit=True) với số thứ tự liên tục cho hiển thị.
        Sắp xếp theo một tiêu chí chung, ví dụ theo id tăng dần.
        (Chú ý: Số thứ tự này chỉ dùng để hiển thị trên giao diện, không lưu vào CSDL.)
        """
        tasks = list(self.tasks.all().order_by('id'))
        return [(i + 1, task) for i, task in enumerate(tasks)]

class MaintenanceTemplate(models.Model):
    category = models.ForeignKey(
        EquipmentCategories, on_delete=models.CASCADE, verbose_name="Category"
    )
    maintenance_level = models.PositiveIntegerField(
        choices=MAINTENANCE_LEVEL_CHOICES,
        verbose_name="Maintenance Level"
    )
    inherit = models.BooleanField(default=False, verbose_name="Inherit?")

    class Meta:
        abstract = True
        # Thứ tự hiển thị trong file Excel ban đầu có thể không liên tục;
        # hệ thống sẽ tính lại thứ tự khi gộp danh sách công việc.
        ordering = []

    def __str__(self):
        # Sử dụng task_name (nếu có) hoặc change_type (cho SupplementTemplate)
        name = getattr(self, 'task_name', None) or getattr(self, 'change_type', 'N/A')
        return f"[{self.category}] {self.maintenance_level}h - {name}"

class ReplacementTemplate(MaintenanceTemplate):
    task_name = models.CharField(max_length=255, verbose_name="Task Name")
    replacement_type = models.CharField(max_length=255, verbose_name="Replacement Type")
    quantity = models.IntegerField(default=1)
    manufacturer_id = models.CharField(max_length=255, verbose_name="Manufacturer ID")
    alternative_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="Alternative ID")

    def check_inventory(self):
        return check_inventory_for_template(self)
    class Meta:
        verbose_name = "02. Replacement Template"
        verbose_name_plural = "02. Replacement Templates"

class SupplementTemplate(MaintenanceTemplate):
    # Ở SupplementTemplate, không có trường task_name; dùng change_type làm tên công việc.
    change_type = models.CharField(max_length=255, verbose_name="Change Type")
    position = models.CharField(max_length=255, blank=True, null=True, verbose_name="Position")
    quantity = models.IntegerField(default=1, verbose_name="Quantity")

    class Meta:
        verbose_name = "03. Supplement Template"
        verbose_name_plural = "03. Supplement Templates"

class InspectionTemplate(MaintenanceTemplate):
    task_name = models.CharField(max_length=255, verbose_name="Task Name")

    class Meta:
        verbose_name = "04. Inspection Template"
        verbose_name_plural = "04. Inspection Templates"

class CleaningTemplate(MaintenanceTemplate):
    task_name = models.CharField(max_length=255, verbose_name="Task Name")

    class Meta:
        verbose_name = "05. Cleaning Template"
        verbose_name_plural = "05. Cleaning Templates"

class MaintenanceTask(models.Model):
    maintenance_record = models.ForeignKey(
        MaintenanceRecord, on_delete=models.CASCADE, related_name="tasks", verbose_name="Maintenance Record"
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    template = GenericForeignKey("content_type", "object_id")
    quantity = models.IntegerField(default=1, verbose_name="Quantity")

    def __str__(self):
        # Dùng task_name nếu có, hoặc dùng change_type cho SupplementTemplate.
        name = getattr(self.template, 'task_name', None) or getattr(self.template, 'change_type', 'N/A')
        return f"{self.maintenance_record} - {name}"

    class Meta:
        verbose_name = "06. Maintenance Task"
        verbose_name_plural = "06. Maintenance Tasks"

class ReplacementResult(models.Model):
    task = models.OneToOneField(
        MaintenanceTask, on_delete=models.CASCADE, related_name="replacement_result", verbose_name="Maintenance Task"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    actual_quantity = models.PositiveIntegerField(
        default=0,
        verbose_name="Số lượng thực tế đã thay",
        help_text="Nhập số lượng vật tư thực tế đã thay trong quá trình bảo trì"
    )
    class Meta:
        verbose_name = "07. Replacement Result"
        verbose_name_plural = "07. Replacement Results"

class SupplementResult(models.Model):
    task = models.OneToOneField(
        MaintenanceTask, on_delete=models.CASCADE, related_name="supplement_result", verbose_name="Maintenance Task"
    )
    completed = models.BooleanField(default=False, verbose_name="Completed")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")

    class Meta:
        verbose_name = "08. Supplement Result"
        verbose_name_plural = "08. Supplement Results"

class InspectionResult(models.Model):
    task = models.OneToOneField(
        MaintenanceTask, on_delete=models.CASCADE, related_name="inspection_result", verbose_name="Maintenance Task"
    )
    condition = models.TextField(blank=True, null=True, verbose_name="Condition")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")

    class Meta:
        verbose_name = "09. Inspection Result"
        verbose_name_plural = "09. Inspection Results"

class CleaningResult(models.Model):
    task = models.OneToOneField(
        MaintenanceTask, on_delete=models.CASCADE, related_name="cleaning_result", verbose_name="Maintenance Task"
    )
    condition = models.TextField(blank=True, null=True, verbose_name="Condition")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")

    class Meta:
        verbose_name = "10. Cleaning Result"
        verbose_name_plural = "10. Cleaning Results"

class MaintenanceRecordHistory(models.Model):
    record = models.ForeignKey(MaintenanceRecord, on_delete=models.CASCADE, related_name="history")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    changes = models.JSONField(help_text="Lưu các thay đổi dưới dạng JSON", blank=True, null=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Maintenance Record History"
        verbose_name_plural = "Maintenance Record Histories"

    def __str__(self):
        return f"History for {self.record.record_id} at {self.updated_at.strftime('%Y-%m-%d %H:%M:%S')}"

class CompletedMaintenanceRecord(models.Model):
    maintenance_record = models.OneToOneField(
        MaintenanceRecord,
        on_delete=models.CASCADE,
        related_name="completed_record"
    )
    record_id = models.CharField(max_length=50, unique=True, editable=False, null=True, blank=True)
    completed_at = models.DateTimeField(verbose_name="Completed At")
    tasks = models.JSONField(verbose_name="Maintenance Tasks", default=list)
    results = models.JSONField(verbose_name="Task Results", default=list)
    notes = models.TextField(blank=True, null=True, verbose_name="Completion Notes")

    class Meta:
        verbose_name = "Completed Maintenance Record"
        verbose_name_plural = "Completed Maintenance Records"

    def save(self, *args, **kwargs):
        regenerate = False
        old_record_id = None

        record = self.maintenance_record

        if record and record.pk:
            try:
                original = MaintenanceRecord.objects.get(pk=record.pk)
                if original.start_time != record.start_time:
                    regenerate = True
                    old_record_id = generate_record_id(original)
            except MaintenanceRecord.DoesNotExist:
                pass

        new_record_id = generate_record_id(record)
        if not self.record_id or regenerate:
            self.record_id = new_record_id

        super().save(*args, **kwargs)

        if regenerate and old_record_id:
            folder = os.path.join(
                settings.CSV_EXPORT_ROOT,
                sanitize_name(record.category.name),
                sanitize_name(record.equipment.name)
            )
            try:
                for fname in os.listdir(folder):
                    if fname.endswith(".xlsx") and fname.startswith(f"{old_record_id}_"):
                        os.remove(os.path.join(folder, fname))
            except Exception:
                pass

    def save_tasks_and_results(self):
        # Sử dụng helper để gom nhóm dữ liệu từ maintenance_record
        grouped = group_tasks_and_results(self.maintenance_record)
        # Lưu dữ liệu đã nhóm vào trường tasks (bạn có thể đổi tên nếu cần)
        self.tasks = grouped
        # Nếu không cần dùng field results nữa vì dữ liệu đã nằm trong tasks
        self.results = []
        super().save()

class IntermediateMaintenance(models.Model):
    category = models.ForeignKey(
        EquipmentCategories, on_delete=models.CASCADE, verbose_name="Category"
    )
    equipment = models.ForeignKey(
        Equipment, on_delete=models.CASCADE, related_name="intermediate_maintenances", verbose_name="Equipment"
    )
    location = models.CharField(max_length=255, verbose_name="Maintenance Location")
    start_time = models.DateTimeField(verbose_name="Start Time")
    end_time = models.DateTimeField(blank=True, null=True, verbose_name="End Time")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")

    created_by = models.ForeignKey(
        User, related_name='created_intermediate_maintenances',
        on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Created By"
    )
    updated_by = models.ForeignKey(
        User, related_name='updated_intermediate_maintenances',
        on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Updated By"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    engine_hours = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Engine Hours"
    )

    class Meta:
        verbose_name = "Intermediate Maintenance"
        verbose_name_plural = "Intermediate Maintenances"