from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-8pzcsr&%l3uxkc%%68xe*y3kqp4)oesen_$00e9wo4kml!j1q*'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'parser_db',
        'USER': 'wbparser',
        'PASSWORD': 'password',
        'HOST': 'postgres',
        'PORT': 5432,
    }
}