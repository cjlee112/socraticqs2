# coding: utf-8
from base import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG


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
    MIDDLEWARE_LOCAL = (
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

print "\n\n\n debug_toolbar == {}\n\n\n".format(debug_toolbar_enabled)

INSTALLED_APPS += INSTALLED_APPS_LOCAL
MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + MIDDLEWARE_LOCAL
INTERNAL_IPS = (
    '127.0.0.1',  # local development
    '172.18.0.1',  # in docker development
)

# Use nose to run all tests
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

# Tell nose to measure coverage on the 'lti' and 'psa' apps
NOSE_ARGS = [
    '--with-coverage',
    '--cover-package=lti,psa,ct,fsm,chat',
    '--cover-inclusive',
]

GOOGLE_ANALYTICS_CODE = ""

try:
    from local import *
except ImportError:
    print '''You must provide a settings/local.py file,
    e.g. by copying the provided local_example.py'''
    raise
