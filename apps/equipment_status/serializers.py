from rest_framework import serializers
from apps.maintenance.models import CompletedMaintenanceRecord
from .status_helper import get_completed_record_and_tasks
from .models import EquipmentStatus


class CompletedMaintenanceRecordSerializer(serializers.ModelSerializer):
    grouped_tasks = serializers.SerializerMethodField()
    notes = serializers.CharField(read_only=True)

    class Meta:
        model = CompletedMaintenanceRecord
        fields = ['id', 'maintenance_record', 'notes', 'grouped_tasks']

    def get_grouped_tasks(self, obj):
        _, grouped = get_completed_record_and_tasks(obj.maintenance_record_id)
        return grouped


class EquipmentStatusSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='equipment.name', read_only=True)
    machine_type = serializers.CharField(source='equipment.category.name', read_only=True)
    management_unit = serializers.CharField(source='equipment.management_unit.name', read_only=True)
    engine_hours = serializers.IntegerField(source='equipment.engine_hours', read_only=True)
    maintenance_records = serializers.SerializerMethodField()
    class Meta:
        model = EquipmentStatus
        fields = [
            'name', 'machine_type', 'management_unit', 'engine_hours',
            'operation_team', 'maintenance_records', 'updated_at',
        ]

    def get_maintenance_records(self, obj):
        # Lấy danh sách id của maintenance_records từ equipment
        return list(obj.equipment.maintenance_records.values_list('id', flat=True))