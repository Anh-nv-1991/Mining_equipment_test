import pytest
from apps.wear_part_stock.serializers import WearPartStockSerializer
from apps.wear_part_stock.test_factories.wear_part_stock_factories import WearPartStockFactory

@pytest.mark.django_db
def test_wear_part_stock_serializer():
    """
    Test WearPartStockSerializer:
      - Tạo một instance WearPartStock mẫu qua factory.
      - Kiểm tra rằng dữ liệu được serialize chứa đầy đủ các trường cần thiết.
    """
    stock = WearPartStockFactory()
    serializer = WearPartStockSerializer(stock)
    data = serializer.data

    expected_fields = [
        "id",
        "manufacturer_fk",  # Có thể là ID hoặc object tùy thuộc vào cách bạn serialize
        "name",
        "stock_quantity",
        "min_threshold",
        "unit",
        "manufacturer_id",
        "alternative_id",
    ]

    for field in expected_fields:
        assert field in data, f"Thiếu trường '{field}' trong dữ liệu serialize của WearPartStock"
