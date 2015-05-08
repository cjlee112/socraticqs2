from defaults import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG


# this key is only used for dev localhost testing, not for production
SECRET_KEY = 'm*n5u7jgkbp2b5f&*hp#o+e1e33s^6&730wlpb#-g536l^4es-'

## LTI Parameters
LTI_DEBUG = True
CONSUMER_KEY = "__consumer_key__"  # can be any random python string with enough length for OAuth
LTI_SECRET = "__lti_secret__"  # can be any random python string with enough length for OAuth

try:
    from local_conf import *
except ImportError as e:
    print 'No settings.local_conf loaded:', e
    pass
