from django.db import models
from apps.equipment_management.models import Manufacturer

class WearPartStock(models.Model):
    name = models.CharField("Tên vật tư", max_length=150)
    stock_quantity = models.PositiveIntegerField("Số lượng tồn", default=0)
    min_threshold = models.PositiveIntegerField("Tồn kho tối thiểu", default=0)
    unit = models.CharField("Đơn vị", max_length=10, blank=True)
    manufacturer_id = models.CharField("Mã vật tư hãng", max_length=50, unique=True)
    alternative_id = models.CharField("Mã thay thế", max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = "Wear Part Stock"
        verbose_name_plural = "Wear Part Stocks"

    def __str__(self):
        return self.name
    @classmethod
    def deduct_parts(cls, codes: list[str], quantity: int) -> int:
        """
        Giảm stock theo danh sách mã (manufacturer_id hoặc alternative_id).
        Trả về số lượng thiếu nếu không đủ, hoặc 0 nếu đủ.
        """
        shortage = quantity
        qs = cls.objects.filter(
            models.Q(manufacturer_id__in=codes) | models.Q(alternative_id__in=codes)
        ).order_by('-stock_quantity')

        for stock in qs:
            if shortage <= 0:
                break
            used = min(stock.stock_quantity, shortage)
            stock.stock_quantity -= used
            stock.save(update_fields=['stock_quantity'])
            shortage -= used

        return max(shortage, 0)


class StockMovementLog(models.Model):
    task = models.ForeignKey(
        "maintenance.MaintenanceTask",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Task liên quan"
    )
    stock = models.ForeignKey(WearPartStock, on_delete=models.SET_NULL, null=True, blank=True)
    maintenance_record = models.ForeignKey('maintenance.MaintenanceRecord', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    shortage = models.PositiveIntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Stock Movement Log"
        verbose_name_plural = "Stock Movement Logs"