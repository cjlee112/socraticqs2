# coding: utf-8
import os
import sys

from .base import *


DEBUG = True


# this key is only used for dev localhost testing, not for production
SECRET_KEY = 'm*n5u7jgkbp2b5f&*hp#o+e1e33s^6&730wlpb#-g536l^4es-'

# LTI Parameters
LTI_DEBUG = True

INSTALLED_APPS_LOCAL = (
    'django_nose',
    'behave_django',
)
MIDDLEWARE_LOCAL = ()

debug_toolbar_enabled = False
try:
    import debug_toolbar
    INSTALLED_APPS_LOCAL += ('debug_toolbar',)
    MIDDLEWARE_LOCAL += (
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    )

    DEBUG_TOOLBAR_PANELS = [
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        # 'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
    ]
    debug_toolbar_enabled = True
except ImportError:
    pass

INSTALLED_APPS += INSTALLED_APPS_LOCAL
INTERNAL_IPS = (
    '127.0.0.1',  # local development
    '172.18.0.1',  # in docker development
)
MIDDLEWARE += MIDDLEWARE_LOCAL

# Use nose to run all tests
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

# Tell nose to measure coverage on the 'lti' and 'psa' apps
NOSE_ARGS = [
    '--with-coverage',
    '--cover-package=lti,psa,ct,fsm,chat',
    '--cover-inclusive',
]

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

GOOGLE_ANALYTICS_CODE = ''


if 'test' in sys.argv or 'test_coverage' in sys.argv:
    DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'


try:
    from .local import *
except ImportError:
    print('''You must provide a settings/local.py file,
    e.g. by copying the provided local_example.py''')
    pass
