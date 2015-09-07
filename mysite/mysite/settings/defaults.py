# coding: utf-8
import os
from datetime import timedelta
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Set template_path and template_dir
TEMPLATE_PATH = os.path.join(BASE_DIR, 'templates')
TEMPLATE_DIRS = (
    TEMPLATE_PATH,
)
# Set databases_name
DATABASES_NAME = os.path.join(BASE_DIR, 'mysite.db')


ADMINS = (
    ('Christopher Lee', 'leec@chem.ucla.edu'),
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': DATABASES_NAME,                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': '',
        'PASSWORD': '',
        'HOST': '',  # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',  # Set to empty string for default.
    }
}


# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# grr, Django testing framework stupidly uses this as signal that
# code is pre-1.6, whereas it STILL seems to be required for app to run.
SITE_ID = 1

# required to stop false positive warning messages
SILENCED_SYSTEM_CHECKS = ['1_6.W001']

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# URL of the login page.
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/done/'
URL_PATH = ''

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    # 'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'ct.middleware.MySocialAuthExceptionMiddleware',
)

ROOT_URLCONF = 'mysite.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'mysite.wsgi.application'


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'crispy_forms',
    'ct',
    'fsm',
    # LTI
    'lti',
    # Socials
    'social.apps.django_app.default',
    'psa',
)

CRISPY_TEMPLATE_PACK = 'bootstrap3'

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

TEMPLATE_CONTEXT_PROCESSORS = (
   'django.contrib.auth.context_processors.auth',
   'django.core.context_processors.debug',
   'django.core.context_processors.i18n',
   'django.core.context_processors.media',
   'django.core.context_processors.static',
   'django.core.context_processors.tz',
   'django.contrib.messages.context_processors.messages',
   'social.apps.django_app.context_processors.backends',
   'social.apps.django_app.context_processors.login_redirect',
   'psa.context_processors.debug_settings',
)

AUTHENTICATION_BACKENDS = (
   'social.backends.twitter.TwitterOAuth',
   'social.backends.facebook.FacebookOAuth2',
   'social.backends.google.GoogleOAuth2',
   'social.backends.linkedin.LinkedinOAuth2',
   'social.backends.khanacademy.KhanAcademyOAuth1',
   'psa.custom_backends.EmailAuth',
   'django.contrib.auth.backends.ModelBackend',
)


SOCIAL_AUTH_PIPELINE = (
    'social.pipeline.social_auth.social_details',
    'social.pipeline.social_auth.social_uid',
    'social.pipeline.social_auth.auth_allowed',
    'psa.pipeline.social_user',
    'social.pipeline.user.get_username',
    'psa.pipeline.custom_mail_validation',
    'psa.pipeline.associate_by_email',
    'social.pipeline.user.create_user',
    'psa.pipeline.validated_user_details',
    # 'psa.pipeline.password_ask',
    'psa.pipeline.associate_user',
    'social.pipeline.social_auth.load_extra_data',
    'social.pipeline.user.user_details',
)

SOCIAL_AUTH_DISCONNECT_PIPELINE = (
    # 'psa.pipeline.password_check',
    'social.pipeline.disconnect.allowed_to_disconnect',
    'social.pipeline.disconnect.get_entries',
    'social.pipeline.disconnect.revoke_tokens',
    'social.pipeline.disconnect.disconnect'
)

PROTECTED_USER_FIELDS = ['first_name', 'last_name', 'email']

FORCE_EMAIL_VALIDATION = True
PASSWORDLESS = True

SOCIAL_AUTH_EMAIL_VALIDATION_FUNCTION = 'psa.mail.send_validation'
SOCIAL_AUTH_EMAIL_VALIDATION_URL = '/email-sent/'

SOCIAL_AUTH_STRATEGY = 'psa.custom_django_strategy.CustomDjangoStrategy'
SOCIAL_AUTH_STORAGE = 'psa.custom_django_storage.CustomDjangoStorage'

SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]

# Facebook email scope declaring
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']

# Add email to requested authorizations.
SOCIAL_AUTH_LINKEDIN_OAUTH2_SCOPE = ['r_basicprofile', 'r_emailaddress']
# Add the fields so they will be requested from linkedin.
SOCIAL_AUTH_LINKEDIN_OAUTH2_FIELD_SELECTORS = ['email-address', 'headline', 'industry']
# Arrange to add the fields to UserSocialAuth.extra_data
SOCIAL_AUTH_LINKEDIN_OAUTH2_EXTRA_DATA = [('id', 'id'),
                                          ('firstName', 'first_name'),
                                          ('lastName', 'last_name'),
                                          ('emailAddress', 'email_address'),
                                          ('headline', 'headline'),
                                          ('industry', 'industry')]

# LTI Parameters
X_FRAME_OPTIONS = "GOFORIT"

# SSL proxy fix
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

BROKER_URL = 'amqp://'
CELERY_RESULT_BACKEND = 'amqp://'
CELERY_TIMEZONE = 'UTC'

CELERYBEAT_SCHEDULE = {
    'check_anonymous': {
        'task': 'mysite.celery.check_anonymous',
        'schedule': timedelta(days=1),
    }
}

# Cache settings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}


# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'lti_debug': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'celery_warn': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    }
}
