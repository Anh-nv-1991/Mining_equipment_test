from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'test_db_name',
        'USER': 'root',
        'PASSWORD': '4791',
        'HOST': 'localhost',  # hoặc địa chỉ server MySQL
        'PORT': '3306',       # cổng mặc định của MySQL
    }
}

PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

DEBUG = False
