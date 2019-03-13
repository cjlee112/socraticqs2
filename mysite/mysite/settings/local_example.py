# coding: utf-8
import sys

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration


sentry_sdk.init(
    dsn="",
    integrations=[DjangoIntegration(), CeleryIntegration()]
)


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'courselets',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

SOCIAL_AUTH_TWITTER_KEY = ''
SOCIAL_AUTH_TWITTER_SECRET = ''

SOCIAL_AUTH_FACEBOOK_KEY = ''
SOCIAL_AUTH_FACEBOOK_SECRET = ''

SOCIAL_AUTH_LINKEDIN_OAUTH2_KEY = ''
SOCIAL_AUTH_LINKEDIN_OAUTH2_SECRET = ''

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = ''
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = ''

SOCIAL_AUTH_KHANACADEMY_OAUTH1_KEY = ''
SOCIAL_AUTH_KHANACADEMY_OAUTH1_SECRET = ''

# When we will use email auth we need to define SMTP settings
EMAIL_USE_TLS = True
EMAIL_HOST = ''
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_PORT = 587
EMAIL_FROM = ''

GOOGLE_ANALYTICS_CODE = ""

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# SES settings
AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''
AWS_SES_REGION_NAME = ''
AWS_SES_REGION_ENDPOINT = ''

# Intercom settings
INTERCOM_APPID = ''
INTERCOM_SECURE_KEY = ''
INTERCOM_ACCESS_TOKEN = ''


if 'test' in sys.argv or 'test_coverage' in sys.argv:
    DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'
