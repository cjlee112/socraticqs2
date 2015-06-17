"""Set needed settings for reinsurance"""
from django.conf import settings


# Allow debug information about LTI request
LTI_DEBUG = getattr(settings, 'LTI_DEBUG', True)

# Allow to uniquely identify Tool Consumer
CONSUMER_KEY = getattr(settings, 'CONSUMER_KEY', "__consumer_key__")

# To secure communications between the tool provider and consumer using OAuth
LTI_SECRET = getattr(settings, 'LTI_SECRET', "__lti_secret__")

# To permit cross-origin framing
X_FRAME_OPTIONS = getattr(settings, 'X_FRAME_OPTIONS', "GOFORIT")

# SSL proxy fix
SECURE_PROXY_SSL_HEADER = getattr(settings, 'SECURE_PROXY_SSL_HEADER',
                                  ('HTTP_X_FORWARDED_PROTO', 'https'))
