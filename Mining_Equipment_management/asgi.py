"""
ASGI config for Mining_Equipment_management project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"Mining_Equipment_management.settings.{os.getenv('DJANGO_ENV','dev')}")

application = get_asgi_application()
