import factory
from django.utils import timezone
from apps.maintenance.models import MaintenanceRecord
from apps.equipment_status.models import EquipmentStatus
# Sử dụng EquipmentFactory đúng được định nghĩa trong maintenance_factories.py
from apps.maintenance.test_factories.maintenance_factories import EquipmentFactory

class MaintenanceRecordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MaintenanceRecord

    equipment = factory.SubFactory(EquipmentFactory)
    maintenance_level = 250
    start_time = factory.LazyFunction(timezone.now)
    end_time = None
    location = "Site A"

class EquipmentStatusFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EquipmentStatus

    equipment = factory.SubFactory(EquipmentFactory)
    operation_team = "Team A"
    updated_at = factory.LazyFunction(timezone.now)
