# coding: utf-8

from .base import *


DATABASES['default']['NAME'] = 'test.db'

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
