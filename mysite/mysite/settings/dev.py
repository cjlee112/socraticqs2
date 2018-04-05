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

try:
    import debug_toolbar
    INSTALLED_APPS_LOCAL += ('debug_toolbar',)
    MIDDLEWARE_LOCAL = (
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    )
except ImportError:
    pass

INSTALLED_APPS += INSTALLED_APPS_LOCAL
MIDDLEWARE_CLASSES = MIDDLEWARE_LOCAL + MIDDLEWARE_CLASSES
INTERNAL_IPS = (
    '127.0.0.1',
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
