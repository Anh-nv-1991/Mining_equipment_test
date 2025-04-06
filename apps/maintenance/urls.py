app_name = "maintenance"

from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import MaintenanceRecordViewSet
from .views_templates import maintenance_modal_view, get_equipment_by_category
from django.http import HttpResponse

def trigger_error(request):
    division_by_zero = 1 / 0  # deliberate error
    return HttpResponse("This will never return")

router = DefaultRouter()
router.register(r"records", MaintenanceRecordViewSet, basename="maintenance-record")

urlpatterns = [
    # Template‑based views (HTML)
    path("test-sentry/", trigger_error),  # ⬅️ Thêm dòng này
    path("modal/<int:record_id>/", maintenance_modal_view, name="maintenance_modal"),
    path("equipment-by-category/", get_equipment_by_category, name="get_equipment_by_category"),

] + router.urls
