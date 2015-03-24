from django.conf import settings


LTI_DEBUG = getattr(settings, 'LTI_DEBUG', True)
CONSUMER_KEY = getattr(settings, 'CONSUMER_KEY', "__consumer_key__")
LTI_SECRET = getattr(settings, 'LTI_SECRET', "__lti_secret__")
X_FRAME_OPTIONS = getattr(settings, 'X_FRAME_OPTIONS', "GOFORIT")
SECURE_PROXY_SSL_HEADER = getattr(settings, 'SECURE_PROXY_SSL_HEADER',
                                  ('HTTP_X_FORWARDED_PROTO', 'https'))
