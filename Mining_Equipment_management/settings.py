
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-i99$h9znfgoj&)0hspd22jclre(fwc2rplv7*4jw4^d7ygi#dk'
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django_otp',
    'django_otp.plugins.otp_totp',
    'two_factor',
    'grappelli',
    'apps.wear_part_stock',
    'apps.equipment_status',
    'apps.equipment_management',
    'apps.maintenance',
    'django_extensions',
    'corsheaders',
    'adminsortable2',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "environ",
]
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        # 'rest_framework.renderers.BrowsableAPIRenderer',  # Nếu bạn không cần xem API dưới dạng HTML, có thể bỏ dòng này
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}
MIDDLEWARE = [
  'corsheaders.middleware.CorsMiddleware',
  'django.middleware.security.SecurityMiddleware',
  'django.contrib.sessions.middleware.SessionMiddleware',
  'django.middleware.common.CommonMiddleware',
  'django.middleware.csrf.CsrfViewMiddleware',
  'django.contrib.auth.middleware.AuthenticationMiddleware',
  'django_otp.middleware.OTPMiddleware',
  'django.contrib.messages.middleware.MessageMiddleware',
  'django.middleware.clickjacking.XFrameOptionsMiddleware'
]

ROOT_URLCONF = 'Mining_Equipment_management.urls'
WSGI_APPLICATION = 'Mining_Equipment_management.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mining_equipment_db',
        'USER': 'root',
        'PASSWORD': '4791',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Đảm bảo thư mục templates được chỉ định ở đây
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
LOGIN_URL = 'two_factor:login'
LOGIN_REDIRECT_URL = '/secure-admin/'
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
CSV_EXPORT_ROOT = os.path.join(BASE_DIR, "exports")
MEDIA_ROOT = CSV_EXPORT_ROOT
MEDIA_URL = '/media/exports/'
MEDIA_ROOT = BASE_DIR / 'exports'
USE_TZ = True
TIME_ZONE = 'Asia/Ho_Chi_Minh'