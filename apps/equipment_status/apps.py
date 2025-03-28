from django.apps import AppConfig

class EquipmentStatusConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.equipment_status'
def ready(self):
    import apps.equipment_status.signals
