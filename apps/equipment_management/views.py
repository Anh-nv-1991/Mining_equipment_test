from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    return render(request, 'equipment/home.html')

from django.shortcuts import get_object_or_404, redirect
from .models import EquipmentCategories

def move_up(request, category_id):
    category = get_object_or_404(EquipmentCategories, id=category_id)
    prev_category = EquipmentCategories.objects.filter(position__lt=category.position).order_by('-position').first()

    if prev_category:
        category.position, prev_category.position = prev_category.position, category.position
        category.save()
        prev_category.save()

    return redirect('/admin/equipment_management/equipmentcategories/')

def move_down(request, category_id):
    category = get_object_or_404(EquipmentCategories, id=category_id)
    next_category = EquipmentCategories.objects.filter(position__gt=category.position).order_by('position').first()

    if next_category:
        category.position, next_category.position = next_category.position, category.position
        category.save()
        next_category.save()

    return redirect('/admin/equipment_management/equipmentcategories/')

