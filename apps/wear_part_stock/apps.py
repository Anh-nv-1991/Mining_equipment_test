from django.apps import AppConfig

class WearPartStockConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.wear_part_stock'
class MaintenanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.maintenance'

    def ready(self):
        import apps.maintenance.signals
