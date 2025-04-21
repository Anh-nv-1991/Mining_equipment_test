from django.contrib import admin
from .models import WearPartStock, StockMovementLog


@admin.register(WearPartStock)
class WearPartStockAdmin(admin.ModelAdmin):
    list_display = ("name", "stock_quantity", "min_threshold", "unit", "manufacturer_id", "alternative_id")
    search_fields = ( "manufacturer_id", "name")

@admin.register(StockMovementLog)
class StockMovementLogAdmin(admin.ModelAdmin):
    list_display = ('stock', 'maintenance_record', 'quantity', 'shortage', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('stock__manufacturer_id', 'maintenance_record__record_id')