# coding: utf-8
import sys

from base import *


SECRET_KEY = 'm*n5u7jgkbp2b5f&*hp#o+e1e33s^6&730wlpb#-g536l^4es-'


DEBUG = True
TEMPLATE_DEBUG = DEBUG

# LTI Parameters
LTI_DEBUG = True

# Default DB settings for docker postgres container
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('DB_NAME', 'courselets'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('PGPASSWORD', 'postgres'),
        'HOST': os.environ.get('DB_SERVICE', 'postgres'),
        'PORT': os.environ.get('DB_PORT', '5432')
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
