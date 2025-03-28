from django.contrib.admin import AdminSite
from django_otp.plugins.otp_totp.models import TOTPDevice

class OTPAdminSite(AdminSite):
    def has_permission(self, request):
        user = request.user

        if not user.is_authenticated:
            return False

        if not user.is_verified():
            return False

        return super().has_permission(request)
