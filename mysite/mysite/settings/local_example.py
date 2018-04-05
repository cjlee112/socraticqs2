# coding: utf-8
import os
import sys
import raven


RAVEN_CONFIG = {
    'dsn': '',
}


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
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

if 'test' in sys.argv or 'test_coverage' in sys.argv:
    DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'
