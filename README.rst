Socraticqs2
===========

Socraticqs2 is the web engine for courselets.org.

Developer documentation is available at http://cjlee112.github.io/socraticqs2


Example setting_local.py to add 'lti' and 'python-social-auth':
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
       'social.backends.twitter.TwitterOAuth',
       'social.backends.facebook.FacebookOAuth2',
       'social.backends.google.GoogleOAuth2',
       'social.backends.linkedin.LinkedinOAuth2',
       'django.contrib.auth.backends.ModelBackend',
    )

    PROTECTED_USER_FIELDS = ['first_name', 'last_name', 'email']


    ## LTI Parameters
    X_FRAME_OPTIONS = "GOFORIT"
    LTI_DEBUG = True
    CONSUMER_KEY = "__consumer_key__"
    LTI_SECRET = "__lti_secret__"
    LTI_URL_FIX = {
            "https://localhost:8000/":"http://localhost:8000/"
    }
    ## Heroku SSL proxy fix
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


    LOGIN_REDIRECT_URL = '/'

    SOCIAL_AUTH_TWITTER_KEY = ''
    SOCIAL_AUTH_TWITTER_SECRET = ''

    SOCIAL_AUTH_FACEBOOK_KEY = ''
    SOCIAL_AUTH_FACEBOOK_SECRET = ''

    SOCIAL_AUTH_LINKEDIN_OAUTH2_KEY = ''
    SOCIAL_AUTH_LINKEDIN_OAUTH2_SECRET = ''
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

    SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = ''
    SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = ''


    import os
    SESSION_COOKIE_SECURE = True
    STATIC_ROOT = os.path.join(os.path.dirname(
                    os.path.abspath(__file__)), 'static')

    # URL prefix for static files.
    STATIC_URL = '/static/'
