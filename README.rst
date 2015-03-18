Socraticqs2
===========

Socraticqs2 is the web engine for courselets.org.

Developer documentation is available at http://cjlee112.github.io/socraticqs2



Example setting_local.py to add 'lti' and 'python-social-auth'
--------------------------------------------------------------
::
    # coding: utf-8

    from settings import INSTALLED_APPS


    INSTALLED_APPS_LOCAL = (
        # LTI
        'lti',

        # Socials
        'social.apps.django_app.default',
    )

    INSTALLED_APPS += INSTALLED_APPS_LOCAL


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
    )

    AUTHENTICATION_BACKENDS = (
        'social.backends.facebook.FacebookOAuth2',
        'social.backends.google.GoogleOAuth2',
        'social.backends.twitter.TwitterOAuth',
        'django.contrib.auth.backends.ModelBackend',
    )


    ## LTI Parameters
    X_FRAME_OPTIONS = 'ALLOW-FROM: *'
    LTI_DEBUG = True
    CONSUMER_KEY = "__consumer_key__"
    LTI_SECRET = "__lti_secret__"
    LTI_URL_FIX = {
            "https://localhost:8000/":"http://localhost:8000/"
    }
    ## Heroku SSL proxy fix
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


    LOGIN_REDIRECT_URL = '/'

    SOCIAL_AUTH_TWITTER_KEY = 'twitter_key'
    SOCIAL_AUTH_TWITTER_SECRET = 'twitter_secret'