import factory
from faker import Faker
from apps.wear_part_stock.models import WearPartStock, StockMovementLog
from apps.equipment_management.models import Manufacturer

fake = Faker()
class ManufacturerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'equipment_management.Manufacturer'
        # Nếu muốn lấy lại instance nếu trùng, có thể sử dụng django_get_or_create
        django_get_or_create = ('name',)
    name = factory.LazyAttribute(lambda o: fake.company())

class WearPartStockFactory(factory.django.DjangoModelFactory):
    class Meta:
        # Sử dụng app label đúng theo AppConfig (thường là phần cuối của tên module)
        model = 'wear_part_stock.WearPartStock'
    name = factory.Sequence(lambda n: f"Test Part {n}")
    stock_quantity = 10  # Số lượng tồn kho ban đầu
    min_threshold = 1
    unit = "pcs"
    manufacturer_id = "M001"
    alternative_id = "ALT001"

class StockMovementLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'wear_part_stock.StockMovementLog'
    # Nếu cần, bạn có thể tạo liên kết đến MaintenanceRecord bằng cách dùng factory khác
    maintenance_record = None
    stock = factory.SubFactory(WearPartStockFactory)
    quantity = 1
    shortage = 0
