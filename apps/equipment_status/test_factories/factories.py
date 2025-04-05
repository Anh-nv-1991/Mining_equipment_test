import factory
from apps.maintenance.models import MaintenanceRecord
from apps.equipment_management.models import Equipment


class EquipmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Equipment

    name = factory.Sequence(lambda n: f"EQ-{n}")
    serial_number = factory.Sequence(lambda n: f"SN-{n}")
    machine_type = "Excavator"
    management_unit = "Team A"


class MaintenanceRecordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MaintenanceRecord

    equipment = factory.SubFactory(EquipmentFactory)
    maintenance_level = "Routine"
    start_time = factory.Faker("date_time_this_year")
    end_time = factory.Faker("date_time_this_year")
    location = "Site A"
