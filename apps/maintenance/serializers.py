from rest_framework import serializers
from .models import MaintenanceRecord
from .models import MaintenanceTask


class ModalMaintenanceTaskSerializer(serializers.ModelSerializer):
    task_type = serializers.SerializerMethodField()
    task_name = serializers.SerializerMethodField()
    position = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()
    replacement_type = serializers.SerializerMethodField()
    manufacturer_id = serializers.SerializerMethodField()
    alternative_id = serializers.SerializerMethodField()
    actual_quantity = serializers.SerializerMethodField()
    completed = serializers.SerializerMethodField()
    condition = serializers.SerializerMethodField()
    check_inventory = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()

    def get_task_type(self, obj):
        model = obj.content_type.model.lower()
        return {'replacementtemplate':'replacement','supplementtemplate':'supplement',
                'inspectiontemplate':'inspection','cleaningtemplate':'cleaning'}.get(model,'unknown')

    def get_task_name(self, obj):
        tpl = obj.template
        return getattr(tpl,'task_name', getattr(tpl,'change_type','N/A'))

    def get_position(self, obj):
        return getattr(obj.template,'position','')

    def get_quantity(self, obj):
        return getattr(obj.template,'quantity',1)

    def get_replacement_type(self, obj):
        return getattr(obj.template,'replacement_type','')

    def get_manufacturer_id(self, obj):
        return getattr(obj.template,'manufacturer_id','')

    def get_alternative_id(self, obj):
        return getattr(obj.template,'alternative_id','')

    def get_actual_quantity(self, obj):
        return getattr(obj.replacement_result,'actual_quantity',0) if hasattr(obj,'replacement_result') else ''

    def get_completed(self, obj):
        res = getattr(obj, "supplement_result", None)
        return res.completed if res else False

    def get_condition(self, obj):
        res = getattr(obj, "inspection_result", None)
        if res:
            return res.condition
        res = getattr(obj, "cleaning_result", None)
        if res:
            return res.condition
        return ""

    def get_notes(self, obj):
        for attr in ("supplement_result", "replacement_result", "inspection_result", "cleaning_result"):
            res = getattr(obj, attr, None)
            if res:
                return res.notes
        return ""

    def get_check_inventory(self, obj):
        # Chỉ áp dụng cho replacementtemplate
        if hasattr(obj, "template") and callable(getattr(obj.template, "check_inventory", None)):
            return obj.template.check_inventory()
        return ""

    class Meta:
        model = MaintenanceTask
        fields = [
            "id","task_type","task_name","position","quantity",
            "replacement_type","manufacturer_id","alternative_id",
            "actual_quantity","completed","condition","check_inventory","notes"
        ]
class MaintenanceRecordSerializer(serializers.ModelSerializer):
    equipment = serializers.CharField(source="equipment.name", read_only=True)
    category = serializers.CharField(source="category.name", read_only=True)
    maintenance_level = serializers.CharField(source="get_maintenance_level_display", read_only=True)

    class Meta:
        model = MaintenanceRecord
        fields = [
            "id",
            "equipment",
            "category",
            "maintenance_level",
            "start_time",
            "end_time",
        ]

    def validate(self, attrs):
        if attrs.get("end_time") and attrs["end_time"] < attrs["start_time"]:
            raise serializers.ValidationError({"end_time": "End time must be after start time."})
        return attrs