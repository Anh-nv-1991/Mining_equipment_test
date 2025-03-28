from django.db import models

# Bảng danh mục chủng loại thiết bị
class EquipmentCategories(models.Model):
    name = models.CharField(max_length=255, unique=True)
    position = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ['position']
        verbose_name_plural = "Equipment Categories"

    @classmethod
    def create_if_not_exists(cls, name):
        category, created = cls.objects.get_or_create(name=name)
        if created:
            last_item = cls.objects.order_by('-position').first()
            category.position = (last_item.position + 1) if last_item else 0
            category.save(update_fields=['position'])
        return category

    def __str__(self):
        return self.name


# Manufacturer mới
class Manufacturer(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Manufacturer"
        verbose_name_plural = "Manufacturers"

    def __str__(self):
        return self.name


# Bảng danh mục đơn vị quản lý thiết bị
class EquipmentManagementUnit(models.Model):
    name = models.CharField(max_length=255, unique=True)
    position = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ['position']

    def save(self, *args, **kwargs):
        if not self.id:
            last_item = EquipmentManagementUnit.objects.order_by('-position').first()
            self.position = (last_item.position + 1) if last_item else 0
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# Bảng thiết bị
class Equipment(models.Model):
    name = models.CharField(max_length=255, verbose_name="Tên thiết bị")
    category = models.ForeignKey(
        EquipmentCategories,
        on_delete=models.CASCADE,
        related_name="equipments",
        verbose_name="Loại máy"
    )
    management_unit = models.ForeignKey(
        EquipmentManagementUnit,
        on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name="Đơn vị quản lý"
    )
    engine_hours = models.IntegerField(default=0, verbose_name="Giờ hoạt động (H)")
    manufacturer = models.ForeignKey(
        Manufacturer,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Hãng sản xuất"
    )

    def __str__(self):
        return f"{self.name} ({self.category.name})"
