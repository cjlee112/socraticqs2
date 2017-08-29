Socraticqs2
===========

.. image:: https://travis-ci.org/cjlee112/socraticqs2.svg?branch=master
    :target: https://travis-ci.org/cjlee112/socraticqs2

.. image:: https://coveralls.io/repos/github/cjlee112/socraticqs2/badge.svg?branch=master
    :target: https://coveralls.io/github/cjlee112/socraticqs2?branch=master

.. image:: https://codecov.io/gh/cjlee112/socraticqs2/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/cjlee112/socraticqs2



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

To install requirements:
::

    pip install -r requirements/dev.txt


Download GeoIp database (run commands in the root of the project):
::

    wget http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz
    gunzip GeoLiteCity.dat.gz

To run project in Docker:
-------------------------
Go to the root of the project and run this command:
 ::
    # coding: utf-8

    docker-compose up web

Here we have 2 docker config files:
 - Dockerfile - runs docker-commands.sh file
 - Dockerfile-prepare - installs requirements (python libs and so on)

There are a couple of files related to docker. They are:
 - docker-compose.yml - config file
 - docker-commands.sh - clear *.pyc files and starts web server


Quality check
-------------

We can check code quality using ``./check-quality.sh {pep8|pylint} {lti|psa|fsm|ct|mysite|all}`` script.
We encourage you to run this script before each commit.
