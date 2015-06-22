Socraticqs2 Social Auth registration
====================================


Introduction
------------

Socraticqs2 users can authorize using SSO.

We a using Python Social Auth library for that process.

Source code available at `github`_.

.. _github: https://github.com/omab/python-social-auth

Available backend(s) now are::

  Google OAuth2
  Facebook OAuth2
  Twitter OAuth
  LinkedIn OAuth2
  KhanAcademy OAuth1


Configuration Python Social Auth
--------------------------------

To configure Python Social Auth (PSA) we need to set appropriate KEY/SECRET for available backends on local_conf.py file::

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


Manuals for backend(s) configuration:

* `Google OAuth2`_
* `Facebook OAuth2`_
* `Twitter OAuth`_
* `LinkedIn OAuth2`_
* `KhanAcademy OAuth1`_

.. _Google OAuth2: https://python-social-auth.readthedocs.org/en/latest/backends/google.html#google-oauth2
.. _Facebook OAuth2: https://python-social-auth.readthedocs.org/en/latest/backends/facebook.html#oauth2
.. _Twitter OAuth: https://python-social-auth.readthedocs.org/en/latest/backends/twitter.html
.. _LinkedIn OAuth2: https://python-social-auth.readthedocs.org/en/latest/backends/linkedin.html#oauth2
.. _KhanAcademy OAuth1: https://python-social-auth.readthedocs.org/en/latest/backends/khanacademy.html


Also we can re-define auth backends on local_conf.py::

    AUTHENTICATION_BACKENDS = (
       # 'social.backends.twitter.TwitterOAuth',
       # 'social.backends.facebook.FacebookOAuth2',
       # 'social.backends.google.GoogleOAuth2',
       # 'social.backends.linkedin.LinkedinOAuth2',
       # 'social.backends.khanacademy.KhanAcademyOAuth1',
       # 'social.backends.email.EmailAuth',
       'django.contrib.auth.backends.ModelBackend',
    )



There are main settings for PSA in settings/default.py::

  MIDDLEWARE_CLASSES = (
    .............
    'ct.middleware.MySocialAuthExceptionMiddleware',
  )

  INSTALLED_APPS = (
    ........
    # Socials
    'social.apps.django_app.default',
    'psa',
  )

  TEMPLATE_CONTEXT_PROCESSORS = (
   ................
   'social.apps.django_app.context_processors.backends',
   'social.apps.django_app.context_processors.login_redirect',
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
    'psa.pipeline.associate_user',
    'social.pipeline.social_auth.load_extra_data',
    'social.pipeline.user.user_details',
  )

  SOCIAL_AUTH_DISCONNECT_PIPELINE = (
    'social.pipeline.disconnect.allowed_to_disconnect',
    'social.pipeline.disconnect.get_entries',
    'social.pipeline.disconnect.revoke_tokens',
    'social.pipeline.disconnect.disconnect'
  )

  PROTECTED_USER_FIELDS = ['first_name', 'last_name', 'email']

  FORCE_EMAIL_VALIDATION = True
  PASSWORDLESS = True

  SOCIAL_AUTH_EMAIL_VALIDATION_FUNCTION = 'psa.mail.send_validation'
  SOCIAL_AUTH_EMAIL_VALIDATION_URL = '/email-sent/'

  SOCIAL_AUTH_STRATEGY = 'psa.custom_django_strategy.CustomDjangoStrategy'
  SOCIAL_AUTH_STORAGE = 'psa.custom_django_storage.CustomDjangoStorage'

  SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
      'https://www.googleapis.com/auth/userinfo.email',
      'https://www.googleapis.com/auth/userinfo.profile'
  ]

  # Facebook email scope declaring
  SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']

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

About these and many other parameters you can read at the PSA `docs`_.

.. _docs: https://python-social-auth.readthedocs.org/en/latest/


User Auth flow procedure
------------------------

We have next `providers`:

* Django user, with primary email
* for STRANGER, when he adds email, and we show pop-up with validation link, do search email associated with social accounts, and if there are similar one, and propose to login on the social auth
* LTI user
* Python social-auth accounts: email and social accounts

**Principles:**
do not merge two social account from same providers

**Assumptions:**
We trust LTI and email providers on email validation they send to us

LTI user
........

https://docs.google.com/drawings/d/1ggBJCrCqWFOY0ST3QqWVikBhj-lFAN7dhzOmhn-Coss/edit

Social auth
...........

Stranger clicks on social-auth button on login page
+++++++++++++++++++++++++++++++++++++++++++++++++++

https://docs.google.com/drawings/d/1v3fBfb3Y1V1EwJ6Kwt3sTiX0v-1HGb8Me5cWeMIB55k/edit

TEMPORARY user clicks validation link
+++++++++++++++++++++++++++++++++++++

https://docs.google.com/drawings/d/1fnlXom0eFG7pfnkc80iJtfu_vI_28WDHgsD05js0m_c/edit

VALIDATED user clicks on social-auth button
+++++++++++++++++++++++++++++++++++++++++++

https://docs.google.com/drawings/d/1BfVylifaSDsO97OVP2l7Nxfqj4YwYYYajrJTV8KF9ww/edit


Users merge
+++++++++++

We are VALIDATED user.

When we click to one of social/email buttons to associate with - system search such provider and if found  start to
analyze possible social/email provider conflicts after possible merge.

This mean that if after merge user would have more than one auth records with the same provider (google for example) we prevent this action with pop-up
“warning about intersected providers”.


Temporary user validation
+++++++++++++++++++++++++

We are TEMPORARY user.

We make some progress and click validation link.

After that system will search email provider with email we validating or search django users by primary email.

If found - TEMPORARY user is logged out, start history merging process and new user is logged in.

If we can not find appropriate user via email - we start to modify user detail.

We change username to part before @ in email, remove ‘Temporary user’ full user name. Because of user is currently
logged in and has all history we do not doing logout/login and history merge action.


User login process
++++++++++++++++++
When STRANGER click on social/email auth button on login page system starts login/register process.

It is possible to login at any time by validate social or email (via confirmation link) auth.

If user will set password after login to the system it will be possible to login using username/password method.

When we login using social/email auth system searching for such social auth records.

If found - login user associated with that social auth.


Social Auth pipelines
---------------------

.. automodule:: psa.pipeline
    :members:

Social Auth Models
------------------

.. automodule:: psa.models
    :members:

Social Auth Views
-----------------

.. automodule:: psa.views
    :members:

Custom Django Strategy and Storage
----------------------------------

We used in Socraticqs2 Social Auth implementation custom Strategy and Storage to move around issue `557`_.

.. _557: https://github.com/omab/python-social-auth/issues/577

.. automodule:: psa.custom_django_storage
    :members:

.. automodule:: psa.custom_django_strategy
    :members:
