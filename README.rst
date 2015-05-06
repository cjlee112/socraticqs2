Socraticqs2
===========

Socraticqs2 is the web engine for courselets.org.

Developer documentation is available at http://cjlee112.github.io/socraticqs2


Example setting_local.py to add 'lti' and 'python-social-auth':
::

    # coding: utf-8

    import os
    from datetime import timedelta
    from settings import INSTALLED_APPS


    INSTALLED_APPS_LOCAL = (
        # LTI
        'lti',

        # Socials
        'social.apps.django_app.default',
        'psa',
        'django_nose',
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
       'psa.context_processors.debug_settings',
    )

    AUTHENTICATION_BACKENDS = (
       'social.backends.twitter.TwitterOAuth',
       'social.backends.facebook.FacebookOAuth2',
       'social.backends.google.GoogleOAuth2',
       'social.backends.linkedin.LinkedinOAuth2',
       'social.backends.khanacademy.KhanAcademyOAuth1',
       'social.backends.email.EmailAuth',
       'django.contrib.auth.backends.ModelBackend',
    )


    SOCIAL_AUTH_PIPELINE = (
        'social.pipeline.social_auth.social_details',
        'social.pipeline.social_auth.social_uid',
        'social.pipeline.social_auth.auth_allowed',
        'psa.pipeline.social_user',
        'social.pipeline.user.get_username',
        'psa.pipeline.custom_mail_validation',
        'psa.pipeline.associate_by_email',
        'social.pipeline.user.create_user',
        'psa.pipeline.validated_user_details',
        # 'psa.pipeline.password_ask',
        'psa.pipeline.associate_user',
        'social.pipeline.social_auth.load_extra_data',
        'social.pipeline.user.user_details',
    )

    SOCIAL_AUTH_DISCONNECT_PIPELINE = (
        # 'psa.pipeline.password_check',
        'social.pipeline.disconnect.allowed_to_disconnect',
        'social.pipeline.disconnect.get_entries',
        'social.pipeline.disconnect.revoke_tokens',
        'social.pipeline.disconnect.disconnect'
    )

    PROTECTED_USER_FIELDS = ['first_name', 'last_name', 'email']


    ## LTI Parameters
    X_FRAME_OPTIONS = "GOFORIT"
    LTI_DEBUG = True
    CONSUMER_KEY = "__consumer_key__"
    LTI_SECRET = "__lti_secret__"
    LTI_URL_FIX = {
            "https://localhost:8000/":"http://localhost:8000/",
            'https://edx.raccoongang.com': "http://edx.raccoongang.com"
    }
    ## Heroku SSL proxy fix
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


    LOGIN_REDIRECT_URL = '/'

    SOCIAL_AUTH_TWITTER_KEY = ''
    SOCIAL_AUTH_TWITTER_SECRET = ''

    SOCIAL_AUTH_FACEBOOK_KEY = ''
    SOCIAL_AUTH_FACEBOOK_SECRET = ''
    SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']

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
    SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile'
    ]


    SOCIAL_AUTH_EMAIL_VALIDATION_FUNCTION = 'psa.mail.send_validation'
    SOCIAL_AUTH_EMAIL_VALIDATION_URL = '/email-sent/'
    SOCIAL_AUTH_EMAIL_FORM_HTML = 'psa/email_signup.html'
    SOCIAL_AUTH_USERNAME_FORM_HTML = 'psa/username_signup.html'

    SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

    # LOGIN_URL = '/custom-login/'
    LOGIN_REDIRECT_URL = '/'
    URL_PATH = ''
    SOCIAL_AUTH_STRATEGY = 'social.strategies.django_strategy.DjangoStrategy'
    SOCIAL_AUTH_STORAGE = 'social.apps.django_app.default.models.DjangoStorage'
    SOCIAL_AUTH_GOOGLE_OAUTH_SCOPE = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/userinfo.profile'
    ]


    SOCIAL_AUTH_KHANACADEMY_OAUTH1_KEY = ''
    SOCIAL_AUTH_KHANACADEMY_OAUTH1_SECRET = ''

    SESSION_COOKIE_SECURE = True
    STATIC_ROOT = os.path.join(os.path.dirname(
                    os.path.abspath(__file__)), 'static')

    # URL prefix for static files.
    # Example: "http://media.lawrence.com/static/"
    STATIC_URL = '/static/'



    # Use GMail for testing purpose
    EMAIL_USE_TLS = True
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_HOST_USER = ''
    EMAIL_HOST_PASSWORD = ''
    EMAIL_PORT = 587
    EMAIL_FROM = 'no-reply@gmail.com'

    FORCE_EMAIL_VALIDATION = True
    PASSWORDLESS = True

    DEBUG = False

    LOGIN_URL = '/login/'
    LOGIN_REDIRECT_URL = '/done/'
    URL_PATH = ''

    BROKER_URL = 'amqp://'
    CELERY_RESULT_BACKEND = 'amqp://'
    CELERY_TIMEZONE = 'UTC'

    CELERYBEAT_SCHEDULE = {
        'check_anonymous': {
            'task': 'mysite.celery.check_anonymous',
            'schedule': timedelta(days=1),
        }
    }

    # Use nose to run all tests
    TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

    # Tell nose to measure coverage on the 'foo' and 'bar' apps
    NOSE_ARGS = [
        '--with-coverage',
        '--cover-package=lti,psa',
        '--cover-inclusive',
    ]

