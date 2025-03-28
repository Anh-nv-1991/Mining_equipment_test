from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import redirect
from django.utils.html import format_html
from .models import Manufacturer,EquipmentManagementUnit, EquipmentCategories, Equipment

class MoveUpDownAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'move_up_down_links')
    ordering = ['position']

    def move_up_down_links(self, obj):
        return format_html(
            '<a href="move-up/{}/">⬆ Lên</a> | <a href="move-down/{}/">⬇ Xuống</a>',
            obj.id, obj.id
        )

    move_up_down_links.short_description = 'Sắp xếp'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('move-up/<int:item_id>/', self.move_up, name=f'move_up_{self.model._meta.model_name}'),
            path('move-down/<int:item_id>/', self.move_down, name=f'move_down_{self.model._meta.model_name}'),
        ]
        return custom_urls + urls

    def move_up(self, request, item_id):
        item = self.model.objects.get(id=item_id)
        prev_item = self.model.objects.filter(position__lt=item.position).order_by('-position').first()
        if prev_item:
            item.position, prev_item.position = prev_item.position, item.position
            item.save()
            prev_item.save()
        return redirect(request.META.get('HTTP_REFERER', 'admin:index'))

    def move_down(self, request, item_id):
        item = self.model.objects.get(id=item_id)
        next_item = self.model.objects.filter(position__gt=item.position).order_by('position').first()
        if next_item:
            item.position, next_item.position = next_item.position, item.position
            item.save()
            next_item.save()
        return redirect(request.META.get('HTTP_REFERER', 'admin:index'))

@admin.register(EquipmentManagementUnit)
class EquipmentManagementUnitAdmin(MoveUpDownAdmin):
    pass

@admin.register(EquipmentCategories)
class EquipmentCategoryAdmin(MoveUpDownAdmin):
    pass

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('clickable_name','category', 'manufacturer','management_unit', 'engine_hours')
    search_fields = ('name', 'management_unit')
    list_filter = ('category','management_unit')


    def clickable_name(self, obj):
        """Tạo link click cho Name"""
        url = reverse('admin:equipment_management_equipment_change', args=[obj.id])
        return format_html('<a href="{}">{}</a>', url, obj.name)

    clickable_name.short_description = "Tên thiết bị"

    def clickable_category(self, obj):
        """Tạo link click cho Category"""
        url = reverse('admin:equipment_management_equipment_change', args=[obj.id])
        return format_html('<a href="{}">{}</a>', url, obj.category)

    clickable_category.short_description = "Loại thiết bị"

    @admin.register(Manufacturer)
    class ManufacturerAdmin(admin.ModelAdmin):
        list_display = ("name",)
        search_fields = ("name",)

    Equipment._meta.get_field('management_unit').verbose_name = "Đơn vị quản lý"
    Equipment._meta.get_field('category').verbose_name = "Nhóm thiết bị"
    Equipment._meta.get_field('engine_hours').verbose_name = "Giờ hoạt động (H)"
