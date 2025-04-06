import factory
from django.utils import timezone
from django.contrib.auth.models import User
from apps.maintenance.models import ReplacementResult

# --- Equipment Management Factories ---
class EquipmentCategoriesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'equipment_management.EquipmentCategories'
    name = factory.Sequence(lambda n: f"Category {n}")
    position = factory.Sequence(lambda n: n)

class ManufacturerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'equipment_management.Manufacturer'
    name = factory.Sequence(lambda n: f"Manufacturer {n}")

class EquipmentManagementUnitFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'equipment_management.EquipmentManagementUnit'
    name = factory.Sequence(lambda n: f"Management Unit {n}")
    position = factory.Sequence(lambda n: n)

class EquipmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'equipment_management.Equipment'
    name = factory.Sequence(lambda n: f"Equipment {n}")
    category = factory.SubFactory(EquipmentCategoriesFactory)
    management_unit = factory.SubFactory(EquipmentManagementUnitFactory)
    engine_hours = 1000
    manufacturer = factory.SubFactory(ManufacturerFactory)

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    username = factory.Sequence(lambda n: f"user{n}")
    # Đặt mật khẩu sau khi tạo
    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        obj.set_password(extracted or "password")
        if create:
            obj.save()

# --- Maintenance App Factories ---
class MaintenanceRecordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'maintenance.MaintenanceRecord'
    category = factory.SubFactory(EquipmentCategoriesFactory)
    equipment = factory.SubFactory(EquipmentFactory)
    maintenance_level = 250
    location = "Test Location"
    start_time = factory.LazyFunction(timezone.now)
    end_time = None
    responsible_units = "Test Unit"
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SelfAttribute('created_by')

# Giả sử bạn có các template cho task bảo dưỡng
class ReplacementTemplateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'maintenance.ReplacementTemplate'
    category = factory.SubFactory(EquipmentCategoriesFactory)
    maintenance_level = 250
    task_name = "Replacement Task"
    replacement_type = "Type A"
    quantity = 1
    manufacturer_id = "M001"
    alternative_id = "A001"

# Factory cho MaintenanceTask (cho trường hợp Replacement)
class MaintenanceTaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'maintenance.MaintenanceTask'
    maintenance_record = factory.SubFactory(MaintenanceRecordFactory)
    template = factory.SubFactory(ReplacementTemplateFactory)
    quantity = 1

# Khi record được hoàn tất, hệ thống sẽ tạo CompletedMaintenanceRecord
class CompletedMaintenanceRecordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'maintenance.CompletedMaintenanceRecord'
    maintenance_record = factory.SubFactory(MaintenanceRecordFactory)
    completed_at = factory.LazyFunction(timezone.now)
    notes = "Test Completed Record"
    # Giả sử tasks được lưu dưới dạng JSON snapshot, ta để mặc định rỗng
    tasks = {}

# --- Equipment Status Factory ---
class EquipmentStatusFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'equipment_status.EquipmentStatus'
    equipment = factory.SubFactory(EquipmentFactory)
    operation_team = "Team A"

class ReplacementResultFactory(factory.django.DjangoModelFactory):
        class Meta:
            model = ReplacementResult

        task = factory.SubFactory(MaintenanceTaskFactory)  # đảm bảo MaintenanceTaskFactory đã được định nghĩa
        actual_quantity = factory.LazyAttribute(lambda o: o.task.quantity)
        notes = "Test replacement result"
