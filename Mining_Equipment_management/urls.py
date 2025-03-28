from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from two_factor.urls import urlpatterns as tf_urlpatterns

from apps.secure_admin import OTPAdminSite

# Secure admin setup...
secure_admin_site = OTPAdminSite(name='secure_admin')
router = DefaultRouter()

# Tách tf_urlpatterns thành list các URL patterns và app_name (không dùng nữa ở đây)
tf_patterns, tf_app_name = tf_urlpatterns

urlpatterns = [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
] + tf_patterns + [
    path('grappelli/', include('grappelli.urls')),
    path("api/v1/maintenance/", include(("apps.maintenance.urls", "maintenance"), namespace="maintenance")),
    path("api/v1/equipment-status/", include(("apps.equipment_status.urls", "equipment_status"), namespace="equipment_status")),
    path('wear-parts/', include('apps.wear_part_stock.urls')),
    path('favicon.ico', RedirectView.as_view(url='/static/images/favicon.ico')),
    path('admin/', admin.site.urls),
    path('secure-admin/', secure_admin_site.urls),
    path('equipment_management/', include("apps.equipment_management.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
