Socraticqs2
===========

Socraticqs2 is the web engine for courselets.org.

Developer documentation is available at http://cjlee112.github.io/socraticqs2


In setting_local.py we need to describe all needed KEY/SECRET for social-auth:
::

    # coding: utf-8

    SOCIAL_AUTH_TWITTER_KEY = 'key'
    SOCIAL_AUTH_TWITTER_SECRET = 'secret'

    SOCIAL_AUTH_FACEBOOK_KEY = 'key'
    SOCIAL_AUTH_FACEBOOK_SECRET = 'secret'

    SOCIAL_AUTH_LINKEDIN_OAUTH2_KEY = 'key'
    SOCIAL_AUTH_LINKEDIN_OAUTH2_SECRET = 'secret'

    SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = 'key'
    SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = 'secret'

    SOCIAL_AUTH_KHANACADEMY_OAUTH1_KEY = 'key'
    SOCIAL_AUTH_KHANACADEMY_OAUTH1_SECRET = 'secret'

    # Will be changed to JSONSerializer, not finished yet
    SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

    # When we will use email auth we need to define SMTP settings
    EMAIL_USE_TLS = True
    EMAIL_HOST = ''
    EMAIL_HOST_USER = ''
    EMAIL_HOST_PASSWORD = ''
    EMAIL_PORT = 587
    EMAIL_FROM = ''

    #We can re-define auth backend(s)
    AUTHENTICATION_BACKENDS = (
       # 'social.backends.twitter.TwitterOAuth',
       # 'social.backends.facebook.FacebookOAuth2',
       # 'social.backends.google.GoogleOAuth2',
       # 'social.backends.linkedin.LinkedinOAuth2',
       # 'social.backends.khanacademy.KhanAcademyOAuth1',
       # 'social.backends.email.EmailAuth',
       'django.contrib.auth.backends.ModelBackend',
    )

    # For production we need to set DEBUG to False
    DEBUG = False


For testing purposes we can add django-nose to setting_local.py:
::

    from settings import INSTALLED_APPS

    INSTALLED_APPS_LOCAL = (
        'django_nose',
    )

    INSTALLED_APPS += INSTALLED_APPS_LOCAL

    # Use nose to run all tests
    TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

    # Tell nose to measure coverage on the 'lti' and 'psa' apps
    NOSE_ARGS = [
        '--with-coverage',
        '--cover-package=lti,psa',
        '--cover-inclusive',
    ]
