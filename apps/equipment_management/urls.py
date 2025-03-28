app_name = "equipment_management"

from django.urls import path, include
from . import views
from .views import move_up, move_down

urlpatterns = [
    path('', views.home, name='home'),
    path('grappelli/', include('grappelli.urls')),
]