from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from apps.secure_admin import OTPAdminSite

# Import file my_two_factor_urls.py (đặt ở thư mục apps/)
from apps.my_two_factor_urls import urlpatterns as my_twofactor_patterns

# Secure admin setup...
secure_admin_site = OTPAdminSite(name='secure_admin')
router = DefaultRouter()

urlpatterns = [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

    # Include các URL của two_factor với namespace 'two_factor'
    path('account/', include((my_twofactor_patterns, 'two_factor'), namespace='two_factor')),

    path('grappelli/', include('grappelli.urls')),
    path("api/v1/maintenance/", include(("apps.maintenance.urls", "maintenance"), namespace="maintenance")),
    path("api/v1/equipment-status/",
         include(("apps.equipment_status.urls", "equipment_status"), namespace="equipment_status")),
    path('wear-parts/', include('apps.wear_part_stock.urls')),
    path('favicon.ico', RedirectView.as_view(url='/static/images/favicon.ico')),
    path('admin/', admin.site.urls),
    path('secure-admin/', secure_admin_site.urls),
    path('equipment_management/', include("apps.equipment_management.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
