from django.urls import path
from .views import deduct_stock_view

urlpatterns = [
    path('deduct/<int:record_id>/', deduct_stock_view, name='wearpartstock_deduct'),
]
