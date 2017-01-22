# coding: utf-8

import sys
import os


DB_BAND = {
    'docker': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('DB_NAME', 'courselets'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('PGPASSWORD', 'postgres'),
        'HOST': os.environ.get('DB_SERVICE', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432')
    },

    'postgres': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'courselets',
        'USER': 'thatmax',
        'PASSWORD': 'thatmax',
        'HOST': '',
        'PORT': '',
    },

    'sqlite': {
        'ENGINE': 'django.db.backends.sqlite3',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'mysite.db',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': '',
        'PASSWORD': '',
        'PORT': '',  # Set to empty string for default.
    }

}

DATABASES = {
    'default': DB_BAND.get('sqlite', DB_BAND.get('sqlite'))
}


# ElasticSearch
ELASTICSEARCH_URL = os.environ.get('ELASTIC_HOST', 'elastic')


SOCIAL_AUTH_TWITTER_KEY = 'mrdueT4hYQETck6UMEs4fJv9q'
SOCIAL_AUTH_TWITTER_SECRET = 'Xo7nprRa9PCcmA9DWDwCYkoxNKLkDfixOYIze8BN5Q5kjHXhVY'

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
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'misokolsky@gmail.com'
EMAIL_HOST_PASSWORD = 'kwnibrcqlwpouxqk'
EMAIL_PORT = 587
EMAIL_FROM = 'misokolsky@gmail.com'

DEBUG = True
LTI_DEBUG = True

if 'test' in sys.argv or 'test_coverage' in sys.argv:
    DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'

# GetSentry config

# RAVEN_CONFIG = {
#     'dsn': 'https://9768691b36264d85a76352143181dd9b:91d701a5d9bc45d28f72dc5015973fe9@app.getsentry.com/60893',
# }
