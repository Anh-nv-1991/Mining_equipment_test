# apps/equipment_status/urls.py

app_name = "equipment_status"

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    EquipmentStatusViewSet,
    maintenance_history_for_equipment,
    maintenance_record_readonly_view,
    completed_record_detail,
    intermediate_readonly_view,
)

router = DefaultRouter()
router.register(r"", EquipmentStatusViewSet, basename="equipment-status")

urlpatterns = [
    path(
        "maintenance-history/<int:equipment_id>/",
        maintenance_history_for_equipment,
        name="maintenance_history_for_equipment",
    ),
    path(
        "maintenance-record/<int:record_id>/readonly/",
        maintenance_record_readonly_view,
        name="maintenance_record_readonly",
    ),
    path(
        "completed-record/<int:record_id>/",
        completed_record_detail,
        name="completed_record_detail",
    ),
    path(
        "maintenance-intermediate/<int:pk>/readonly/",
        intermediate_readonly_view,
        name="maintenance_intermediate_readonly",
    ),
] + router.urls
