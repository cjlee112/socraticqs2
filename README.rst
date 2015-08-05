Socraticqs2
===========

Socraticqs2 is the web engine for courselets.org.

Developer documentation is available at http://cjlee112.github.io/socraticqs2


For a developer / test version to access social-auth, you will need to add the following social-auth keys to settings/local_conf.py in your development install:
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
       # 'psa.custom_backends.EmailAuth',
       'django.contrib.auth.backends.ModelBackend',
    )


Quality check
-------------

We can check code quality using ``./check-quality.sh {pep8|pylint} {lti|psa|fsm|ct|mysite|all}`` script.
We encourage you to run this script before each commit.
