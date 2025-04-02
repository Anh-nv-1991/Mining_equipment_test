from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction

from .models import MaintenanceRecord, MaintenanceRecordHistory, ReplacementResult, SupplementResult, InspectionResult, CleaningResult
from .serializers import ModalMaintenanceTaskSerializer
from .excel_export import export_record_to_excel
from apps.wear_part_stock.services import sync_inventory_with_record
from .models import CompletedMaintenanceRecord
from .serializers import MaintenanceRecordSerializer

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import filters, viewsets

class MaintenanceRecordViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceRecord.objects.all().order_by("-start_time")
    serializer_class = MaintenanceRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ["equipment", "category", "maintenance_level"]
    ordering_fields = ["start_time", "end_time"]
    search_fields = ["equipment__name", "category__name"]

    @action(detail=True, methods=["GET","POST"], url_path="tasks")
    def tasks(self, request, pk=None):
        record = self.get_record(pk)

        # GET: trả về danh sách tasks
        if request.method == "GET":
            serializer = ModalMaintenanceTaskSerializer(record.tasks.select_related("content_type"), many=True)
            grouped = {"replacement": [], "supplement": [], "inspection": [], "cleaning": []}
            for task in serializer.data:
                grouped[task["task_type"]].append(task)
            record_data = {
                "id": record.id,
                "equipment": record.equipment.name or "N/A",
                "category": record.category.name or "N/A",
                "maintenance_level": record.get_maintenance_level_display(),
                "start_time": timezone.localtime(record.start_time).strftime("%Y-%m-%d %H:%M") if record.start_time else "",
                "created_by": record.created_by.username if record.created_by else "N/A",
            }
            return Response({
                "record": record_data,
                "replacement_tasks": grouped["replacement"],
                "supplement_tasks": grouped["supplement"],
                "inspection_tasks": grouped["inspection"],
                "cleaning_tasks": grouped["cleaning"],
            })

        # POST: cập nhật kết quả tasks
        result_map = {
            "replacement": ReplacementResult,
            "supplement": SupplementResult,
            "inspection": InspectionResult,
            "cleaning": CleaningResult,
        }
        history_changes = []
        with transaction.atomic():
            for item in request.data.get("results", []):
                task_id = item["id"]
                model_cls = result_map.get(item["task_type"])
                if not model_cls:
                    continue

                result_obj, created = model_cls.objects.get_or_create(task_id=task_id)
                if item["task_type"] == "replacement":
                    old = {
                        "actual_quantity": result_obj.actual_quantity,
                        "notes": result_obj.notes
                    }
                    result_obj.actual_quantity = item.get("actual_quantity", 0)
                    result_obj.notes = item.get("notes", "")
                    fields = ["actual_quantity", "notes"]

                elif item["task_type"] == "supplement":
                    old = {
                        "completed": getattr(result_obj, "completed", None),
                        "notes": result_obj.notes
                    }
                    result_obj.completed = item.get("completed", False)
                    result_obj.notes = item.get("notes", "")
                    fields = ["completed", "notes"]

                elif item["task_type"] in ["inspection", "cleaning"]:
                    old = {
                        "condition": getattr(result_obj, "condition", None),
                        "notes": result_obj.notes
                    }
                    result_obj.condition = item.get("condition", "")
                    result_obj.notes = item.get("notes", "")
                    fields = ["condition", "notes"]

                result_obj.save()

                diff = {}
                if created:
                    diff = {"created": {"old": None, "new": {f: getattr(result_obj, f, None) for f in fields}}}
                else:
                    for f in fields:
                        new_val = getattr(result_obj, f, None)
                        if old.get(f) != new_val:
                            diff[f] = {"old": old.get(f), "new": new_val}

                if diff:
                    history_changes.append({"task_id": task_id, "changed_fields": diff})

            if history_changes:
                MaintenanceRecordHistory.objects.create(record=record, updated_by=request.user, changes=history_changes)

        return Response({"success": True})

    @action(detail=True, methods=["GET"])
    def history(self, request, pk=None):
        record = self.get_record(pk)
        histories = MaintenanceRecordHistory.objects.filter(record=record).order_by('-updated_at')
        return Response({
            "history": [{
                "updated_by": h.updated_by.username if h.updated_by else "N/A",
                "updated_at": timezone.localtime(h.updated_at).strftime("%Y-%m-%d %H:%M:%S"),
                "changes": h.changes or []
            } for h in histories]
        })

    def get_record(self, pk):
        return get_object_or_404(MaintenanceRecord, pk=pk)

    @action(detail=True, methods=["POST"], url_path="complete")
    @transaction.atomic
    def complete(self, request, pk=None):
        """
        Endpoint này được gọi khi người dùng bấm nút “Hoàn tất”.
        Nó sẽ:
          1. Đồng bộ kho nếu cần.
          2. Lấy hoặc tạo CompletedMaintenanceRecord cho record đó.
          3. Gọi save_tasks_and_results() để tạo snapshot cuối cùng.
          4. (Tuỳ chọn) Xuất file Excel nếu cần.
        """
        record = self.get_record(pk)
        if not record.end_time:
            record.end_time = timezone.now()
            record.save(update_fields=["end_time"])
        # Đồng bộ kho trước khi ghi snapshot
        sync_inventory_with_record(record)

        # Lấy hoặc tạo snapshot của CompletedMaintenanceRecord
        comp, created = CompletedMaintenanceRecord.objects.get_or_create(
            maintenance_record=record,
            defaults={"completed_at": record.end_time}
        )
        # Ghi snapshot cuối cùng: lưu lại tasks/results từ MaintenanceRecord hiện tại
        comp.save_tasks_and_results()
        print(">>> DEBUG comp.tasks =", comp.tasks)  # In ra consol
        # (Tuỳ chọn) Xuất file Excel
        try:
            print(">>> DEBUG export_record_to_excel =", export_record_to_excel)
            try:
                file_path = export_record_to_excel(record)
            except PermissionError as e:
                return Response({"error": str(e)}, status=409)
        except PermissionError as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_409_CONFLICT
            )

        return Response(
            {"success": True, "file": file_path},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["GET"], url_path="readonly")
    def readonly_snapshot(self, request, pk=None):
        """
        Trả về dữ liệu snapshot (tasks, results) từ CompletedMaintenanceRecord,
        nếu record đã "complete".
        """
        record = self.get_record(pk)
        comp = getattr(record, 'completed_record', None)
        if not comp:
            # Chưa "complete"
            return Response({
                "completed": False,
                "message": "Chưa hoàn tất. Không có snapshot."
            }, status=status.HTTP_200_OK)

        from collections import defaultdict
        data_out = defaultdict(list)

        if isinstance(comp.tasks, dict):
            for key, grp in comp.tasks.items():
                zipped = []
                t_arr = grp.get("tasks", [])
                r_arr = grp.get("results", [])
                for t, r in zip(t_arr, r_arr):
                    zipped.append({
                        "task": t,
                        "result": r
                    })
                data_out[key] = zipped

        # Xử lý sắp xếp theo thứ tự mong muốn
        desired_order = ["cleaningtemplate", "inspectiontemplate", "supplementtemplate", "replacementtemplate"]
        ordered_data_out = {}
        # Thêm các nhóm theo thứ tự ưu tiên
        for key in desired_order:
            if key in data_out:
                ordered_data_out[key] = data_out[key]
        # Nếu có thêm nhóm khác không nằm trong desired_order thì append thêm sau:
        for key in data_out:
            if key not in ordered_data_out:
                ordered_data_out[key] = data_out[key]

        return Response({
            "completed": True,
            "snapshot": ordered_data_out,
            "record_id": comp.record_id,
            "completed_at": comp.completed_at.strftime("%Y-%m-%d %H:%M:%S") if comp.completed_at else "",
            "notes": comp.notes or ""
        })


