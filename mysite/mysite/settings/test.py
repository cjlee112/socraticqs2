# coding: utf-8

from .base import *


# Test DB settings for docker postgres container
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'test_courselets'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('PGPASSWORD', 'postgres'),
        'HOST': os.environ.get('DB_SERVICE', 'postgres'),
        'PORT': os.environ.get('DB_PORT', '5432')
    }
}

SECRET_KEY = 'KEY'

SOCIAL_AUTH_TWITTER_KEY = 'test_key'
SOCIAL_AUTH_TWITTER_SECRET = 'test_secret'

DEBUG = True
LTI_DEBUG = True

EMAIL_FROM = 'me@example.com'

DB_DATA = '{}:test_data'.format(os.getpid())

IN_TESTING = True

EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
CELERY_TASK_ALWAYS_EAGER = True
