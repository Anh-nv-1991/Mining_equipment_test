from django.contrib import admin
from .models import WearPartStock, StockMovementLog


@admin.register(WearPartStock)
class WearPartStockAdmin(admin.ModelAdmin):
    list_display = ("manufacturer_fk", "name", "stock_quantity", "min_threshold", "unit", "manufacturer_id", "alternative_id")
    search_fields = ("manufacturer_fk__name", "manufacturer_id", "name")
    list_filter = ("manufacturer_fk",)
@admin.register(StockMovementLog)
class StockMovementLogAdmin(admin.ModelAdmin):
    list_display = ('stock', 'maintenance_record', 'quantity', 'shortage', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('stock__manufacturer_id', 'maintenance_record__record_id')