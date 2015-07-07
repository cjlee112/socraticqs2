# coding: utf-8
from defaults import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG


# this key is only used for dev localhost testing, not for production
SECRET_KEY = 'm*n5u7jgkbp2b5f&*hp#o+e1e33s^6&730wlpb#-g536l^4es-'

## LTI Parameters
LTI_DEBUG = True
CONSUMER_KEY = "__consumer_key__"  # can be any random python string with enough length for OAuth
LTI_SECRET = "__lti_secret__"  # can be any random python string with enough length for OAuth

INSTALLED_APPS_LOCAL = (
    'django_nose',
)

INSTALLED_APPS += INSTALLED_APPS_LOCAL

# Use nose to run all tests
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

# Tell nose to measure coverage on the 'lti' and 'psa' apps
NOSE_ARGS = [
    '--with-coverage',
    '--cover-package=lti,psa,ct,fsm',
    '--cover-inclusive',
]


try:
    from local_conf import *
except ImportError:
    print '''You must provide a settings/local_conf.py file,
    e.g. by copying the provided local_conf_example.py'''
    raise
