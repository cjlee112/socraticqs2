# coding: utf-8

from base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'mysite.db',
    }
}

SECRET_KEY = 'KEY'

SOCIAL_AUTH_TWITTER_KEY = 'test_key'
SOCIAL_AUTH_TWITTER_SECRET = 'test_secret'

DEBUG = True
LTI_DEBUG = True

EMAIL_USE_TLS = True
EMAIL_HOST = ''
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_PORT = 587
EMAIL_FROM = ''
