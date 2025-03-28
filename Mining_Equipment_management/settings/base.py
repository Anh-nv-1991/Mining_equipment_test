import os
from pathlib import Path
import environ


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(PROJECT_ROOT / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
DB_NAME = env("DB_NAME")
DB_USER = env("DB_USER")
DB_PASS = env("DB_PASS")
DB_HOST = env("DB_HOST")
DB_PORT = env.int("DB_PORT", default=3306)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": DB_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASS,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
        "TEST": {
            "NAME": DB_NAME,  # Dùng lại database đã có, không cho Django tự tạo tên mới
        },
    }
}
# Cấu hình bắt buộc để Django boot
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
    "rest_framework",
    "drf_spectacular",
    "django_filters",
    "environ",

]
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
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

ROOT_URLCONF = "Mining_Equipment_management.urls"
WSGI_APPLICATION = "Mining_Equipment_management.wsgi.application"
BASE_DIR = PROJECT_ROOT

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": [
            "django.template.context_processors.debug",
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
        ]},
    },
]

STATIC_URL = "/static/"
LOGIN_URL = 'two_factor:login'
LOGIN_REDIRECT_URL = '/secure-admin/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
CSV_EXPORT_ROOT = os.path.join(BASE_DIR, "exports")
MEDIA_ROOT = CSV_EXPORT_ROOT
MEDIA_URL = '/media/exports/'
MEDIA_ROOT = BASE_DIR / 'exports'
USE_TZ = True
TIME_ZONE = 'Asia/Ho_Chi_Minh'
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ],
    "EXCEPTION_HANDLER": "apps.core.exception_handler.custom_exception_handler",
}
SPECTACULAR_SETTINGS = {"TITLE": "Mining Equipment API", "VERSION": "1.0.0"}
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
            'datefmt': '%d/%b/%Y %H:%M:%S'
        },
    },
    'handlers': {
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'error.log'),
            'formatter': 'verbose'
        },
    },
    'loggers': {
        # Áp dụng cho tất cả các logger trong dự án
        '': {
            'handlers': ['error_file'],
            'level': 'ERROR',
        },
    },
}