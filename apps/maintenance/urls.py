app_name = "maintenance"

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import MaintenanceRecordViewSet
from .views_templates import maintenance_modal_view, get_equipment_by_category

router = DefaultRouter()
router.register(r"records", MaintenanceRecordViewSet, basename="maintenance-record")

urlpatterns = [
    # Template‑based views (HTML)
    path("modal/<int:record_id>/", maintenance_modal_view, name="maintenance_modal"),
    path("equipment-by-category/", get_equipment_by_category, name="get_equipment_by_category"),

] + router.urls
