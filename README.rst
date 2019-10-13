Socraticqs2
===========

.. image:: https://coveralls.io/repos/github/cjlee112/socraticqs2/badge.svg?branch=master
    :target: https://coveralls.io/github/cjlee112/socraticqs2?branch=master

.. image:: https://codecov.io/gh/cjlee112/socraticqs2/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/cjlee112/socraticqs2

.. image:: https://circleci.com/gh/raccoongang/socraticqs2/tree/development.svg?style=svg
  :target: https://circleci.com/gh/raccoongang/socraticqs2/tree/development

Socraticqs2 is the web engine for courselets.org.

Local development environment
-------------------------------

To run project locally
::

    make run

To develop/debug project locally
::

    make debug

To build project locally
::

    make build


To run tests:
::

    make test

To stop containers:
::

    make stop

To clean/rm containers:
::

    make rm

To run production/staging environment locally:
::

    make run env=stage


To build production/staging environment locally:
::

    make build env=stage


CI/CD
-----

CI/CD configuration is described by `.gitlab-ci.yml`_ file.

.. _.gitlab-ci.yml: ./.gitlab-ci.yml


Current deployment scheme is the following:

* any commit pushed in development branch is deployed on **dev** environment
* any commit pushed in master branch is deployed on **stage** environment
* to publish version on **production** you need to create an annotated tag in format of "vX.X.X" (where X.X.X is version number) and push it to repository.

There is a helper that creates a tag for you:
::

    make version VERSION=vX.X.X


    Onboarding settings
-------------------

Switches
::

    ctms_onboarding_enabled set to Active in admin page /admin/waffle/switch/


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

    docker-compose up courselets


Here we have 2 docker config files:
 - Dockerfile - runs docker-commands.sh file
 - Dockerfile-prepare - installs requirements (python libs and so on)

There are a couple of files related to docker. They are:
 - docker-compose.yml - config file
 - docker-commands.sh - clear *.pyc files and starts web server



New Interactions Features:
--------------------------
 * Multiple Choices Feature
 * Equation Feature
 * Numbers Feature
 * Canvas Feature


Multiple Choices Feature:
-------------------------

How to test this functionality:
* setup project
* load fixtures from dumpdata/debug-wo-fsm.json
* load fixtures from dumpdata/ct_mult_choices.json
* open admin UI and create roles for your user and course named `test MultChoices`
* observe Courses Dashboard and you will see `test MultChoices` course with a couple of cocurselets inside of it.
* .....
* Profit!


To create unit with multiple choices:
 * create course, courselet in old UI
 * create thread with ``kind`` ``Question`` (``ORCT``)
 * input this text in question text area:

::

   [choices]
   () a
   (*) b
   () c
   () d


Where: not correct answer is empty parenthes ``()`` and correct answer is ``(*)``
 * change field ``sub_kind`` to ``Multiple choices``
 * save
 * go to New IU and click ``Courselet Preview`` to view changes.


Equation Feature:
-----------------
To create a thread with numbers answer (and grading):
 * create course, courselet (or use existing one) in old UI
 * create thread with ``kind`` ``Question`` (``ORCT``)
 * input this text in `Question` field for example: ``.. math:: F=mg``


 Please note that ``..`` and ``::`` are required ``.. math::`` is a prefix to find formulas.
 * input some text in ``Answer`` field
 * change field ``sub_kind`` to ``Equation``
 * save
 * go to new UI and click ``Preview Courselet``



Numbers Feature:
-----------------
To create a thread with numbers answer (and grading):
 * create course, courselet (or use existing one) in old UI
 * create thread with ``kind`` ``Question`` (``ORCT``)
 * input this text in ``Question`` field for example: ``1+1=?``
 * input answer in field ``Answer``
 * change field ``sub_kind`` to ``Numbers``, also you can enable autograding with ``Enable autograding checkbox``
 * go to answer and change ``Number value`` - it's exact answer for this question
 * change  and ``Number max value`` and ``Number min value`` - this is precision.
 * Please note that ``Number min value <= Number value <= Number max value``
 * save
 * go to new UI and click ``Preview Courselet``


Canvas Feature:
---------------
To create a thread with canvas answer:
 * create course, courselet (or use existing one) (in old UI)
 * create thread with ``kind`` ``Question`` (``ORCT``)
 * input this text in ``Question`` field for example: ``Paint number 1``
 * change field ``sub_kind`` to ``Canvas``
 * you also can upload image that will be used as a back ground for space where user will draw image
 * save
 * go to new UI and click ``Preview Courselet``



Quality check
-------------

We can check code quality using ``./check-quality.sh {pep8|pylint} {lti|psa|fsm|ct|mysite|all}`` script.
We encourage you to run this script before each commit.


Feature Switches
----------------

We can switch on and switch off different features.
By default all features are switched off.
Here's a list of switches:

 * ctms_invite_students - to invite user as a student
 * live_session_enabled - to enable button "Live session"
 * menu_activity_center_link_enabled - to enable activity center link in top menu
 * add_unit_by_chat - to enable add unit by chat feature in CTMS
 * ctms_bp_courseletes_enabled - to enable button "Best Practices" for courselet in sidebar


GitLab configuration
-------------

Need to set following secret variables:
* DOCKER_IMG_NAME
* DOCKER_PASSWORD
* DOCKER_USERNAME


Instructor Agreement
--------------------

When user tries to go to CTMS page, but has no Instructor instance attached, user will not see page but will see the error message.
Error 404, because user's who are not instructor has no access to this part of site.

That's why we created new page named `Instructor Agreement`, which should be added through admin CMS with custom content.

* Go to `/admin/cms/page`
* Create new page named `Instructor Agreement` (or with any other name, but remember URL to this page)
* Open `mysite/settings/base.py` file and check `BECOME_INSTRUCTOR_URL`.
* `BECOME_INSTRUCTOR_URL` must be the same as URL of `Instructor Agreement` page.
* Reload server.

SES configuration
-----------------

fill the following settings in order to have ability to send emails
AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''
AWS_SES_REGION_NAME = ''
AWS_SES_REGION_ENDPOINT = ''
