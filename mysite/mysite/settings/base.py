# coding: utf-8
import os
from datetime import timedelta

gettext = lambda s: s

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


CMS_TEMPLATES = (
    ('pages/main_page.html', 'Main Page'),
    ('pages/about_page.html', 'About Page'),
    ('pages/landing_page.html', 'Landing Page'),
    ('pages/faq_page.html', 'FAQ Page'),
    ('pages/become_instructor.html', 'Become Instructor'),
)

# Set databases_name
DATABASES_NAME = os.path.join(BASE_DIR, 'mysite.db')

ADMINS = (
    ('Christopher Lee', 'leec@chem.ucla.edu'),
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Add 'django.db.backends.postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': DATABASES_NAME,  # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': '',
        'PASSWORD': '',
        'HOST': '',  # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',  # Set to empty string for default.
    }
}


# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

LANGUAGES = [
    ('en-us', 'English'),
]

# grr, Django testing framework stupidly uses this as signal that
# code is pre-1.6, whereas it STILL seems to be required for app to run.
SITE_ID = 1

# required to stop false positive warning messages
SILENCED_SYSTEM_CHECKS = ['1_6.W001']

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'lms/static'),
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'djangobower.finders.BowerFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# URL of the login page.
LOGIN_URL = '/new_login/'
LOGIN_REDIRECT_URL = '/ctms/'
URL_PATH = ''

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'django.middleware.locale.LocaleMiddleware',
    'cms.middleware.user.CurrentUserMiddleware',
    'cms.middleware.page.CurrentPageMiddleware',
    'cms.middleware.toolbar.ToolbarMiddleware',
    'cms.middleware.language.LanguageCookieMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    'psa.middleware.MySocialAuthExceptionMiddleware',
    'waffle.middleware.WaffleMiddleware',
    'ctms.middleware.SideBarMiddleware',
]

ROOT_URLCONF = 'mysite.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'mysite.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'djangocms_admin_style',
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'crispy_forms',
    'ct',
    'ctms',
    'fsm',
    'analytics',
    # LTI
    'lti',
    # API
    'api',
    # Socials
    'social_django',
    'psa',
    # Chat UI
    'chat',
    'grading',
    'rest_framework',
    'accounts',
    'waffle',
    # Django-CMS
    'cms',
    'treebeard',
    'menus',
    'sekizai',
    'djangocms_text_ckeditor',
    # Filler
    'filer',
    'easy_thumbnails',
    # CMS pages
    'pages',

    # bower requirements
    'djangobower',
    'storages'
)

THUMBNAIL_HIGH_RESOLUTION = True

CRISPY_TEMPLATE_PACK = 'bootstrap3'

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'OPTIONS': {
            'context_processors': (
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.template.context_processors.csrf',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
                'psa.context_processors.debug_settings',
                'mysite.context_processors.google_analytics',
                'mysite.context_processors.onboarding_percentage_of_done',
                'sekizai.context_processors.sekizai',
                'cms.context_processors.cms_settings',
            )
        }
    },
]


AUTHENTICATION_BACKENDS = (
    'social_core.backends.twitter.TwitterOAuth',
    'social_core.backends.facebook.FacebookOAuth2',
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.linkedin.LinkedinOAuth2',
    'social_core.backends.khanacademy.KhanAcademyOAuth1',
    'psa.custom_backends.EmailAuth',
    'django.contrib.auth.backends.ModelBackend',
)

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'psa.pipeline.social_user',
    'social_core.pipeline.user.get_username',
    'psa.pipeline.custom_mail_validation',
    'psa.pipeline.associate_by_email',
    'social_core.pipeline.user.create_user',
    'psa.pipeline.validated_user_details',
    # 'psa.pipeline.password_ask',
    'psa.pipeline.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)

SOCIAL_AUTH_DISCONNECT_PIPELINE = (
    # 'psa.pipeline.password_check',
    'social_core.pipeline.disconnect.allowed_to_disconnect',
    'social_core.pipeline.disconnect.get_entries',
    'social_core.pipeline.disconnect.revoke_tokens',
    'social_core.pipeline.disconnect.disconnect'
)

SOCIAL_AUTH_INACTIVE_USER_URL = '/inactive-user/'

PROTECTED_USER_FIELDS = ['first_name', 'last_name', 'email']

FORCE_EMAIL_VALIDATION = True
PASSWORDLESS = True

SOCIAL_AUTH_EMAIL_VALIDATION_FUNCTION = 'psa.mail.send_validation'
SOCIAL_AUTH_EMAIL_VALIDATION_URL = '/ctms/email_sent/'

SOCIAL_AUTH_STRATEGY = 'psa.custom_django_strategy.CustomDjangoStrategy'
SOCIAL_AUTH_STORAGE = 'psa.custom_django_storage.CustomDjangoStorage'

SOCIAL_AUTH_POSTGRES_JSONFIELD = True

SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]

# Facebook email scope declaring
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']

SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
    'fields': 'first_name, last_name, email'
}

# Facebook API version to use
SOCIAL_AUTH_FACEBOOK_API_VERSION = '3.1'

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

# LTI Parameters
X_FRAME_OPTIONS = "GOFORIT"

# SSL proxy fix
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'amqp://')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'amqp://')
CELERY_TIMEZONE = 'UTC'

CELERYBEAT_SCHEDULE = {
    'check_anonymous': {
        'task': 'mysite.celery.check_anonymous',
        'schedule': timedelta(days=1),
    }
}

# Cache settings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}


# Path to GeoIp database to convert users IP to location
GEO_IP_DB_PATH = os.path.join(BASE_DIR, 'GeoLiteCityLocal.dat')

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(message)s'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, '../logs/errs.log'),
            'formatter': 'verbose'
        },
        'notifications': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, '../logs/notifs.log'),
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'lti.views': {
            'handlers': ['console', 'file'],
        },
        'lti.outcomes': {
            'handlers': ['console', 'file'],
        },
        'celery_warn': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'core': {
            'handlers': ['file'],
            'level': 'INFO'
        },
        'ct': {
            'handlers': ['notifications'],
            'level': 'INFO'
        },
        'ctms': {
            'handlers': ['file'],
            'level': 'INFO'
        }
    }
}


CMS_PLACEHOLDER_CONF = {
    'about_page_content': {
        'plugins': ['TextPlugin'],
        'name': 'About Page content',
        'limits': {
            'global': 20,
        },
    },
    'about_page_title': {
        'plugins': ['TextPlugin'],
        'name': 'About Page title',
        'limits': {
            'global': 1,
        },
    },
    'langing_page_placeholder': {
        'plugins': ['LandingPagePlugin']
    },
    'landing_page_active_learning_placeholder': {
        'plugins': ['ActiveLearningRatesPagePlugin']
    },
    'landing_page_list_placeholder': {
        'plugins': ['ListPagePlugin']
    },
    'landing_workshop_description_placeholder': {
        'plugins': ['WorkshopDescriptionPagePlugin']
    },
    'landing_page_benefits_placeholder': {
        'plugins': ['BenefitPagePlugin']
    },
    'share_page_placeholder': {
        'plugins': ['LandingPageSocialPlugin']
    },
    'landing_page_footer': {
        'plugins': ['FooterPagePlugin']
    },
    'faq_page_placeholder': {
        'plugins': ['FAQPagePlugin']
    },
    'interested_page_placeholder': {
        'plugins': ['InterestedPagePlugin']
    },
    'landing_page_banner': {
        'plugins': ['BannerPagePlugin'],
        'limits': {
            'global': 1,
        },
    },
    'landing_page_slideshare_placeholder': {
        'plugins': ['SlideSharePagePlugin', 'InlineSlideSharePagePlugin'],
    },
    'landing_personal_guides': {
        'plugins': ['ParentPersonalGuidesPagePlugin']
    },
    'become_instructor_placeholder': {
        'plugins': ['BecomeInstructorPlugin']
    }
}

CTMS_URL_NAMESPACE = 'ctms'

BOWER_COMPONENTS_ROOT = '{}/chat/static/'.format(BASE_DIR)
BOWER_INSTALLED_APPS = (
    'MathJax#2.6.1',
    'bootstrap#3.3.7',
    'gsap#1.18.5',
    'handlebars#4.0.5',
    'html5shiv#3.7.3',
    'jquery#2.2.4',
    'placeholders#4.0.1',
    'respond#1.4.2',
    'screenfull#3.0.2',
    'zoom.js#0.0.1',
    'bootstrap-sidebar',
)

BECOME_INSTRUCTOR_URL = '/become-instructor/'


# Mongo
DB_DATA = 'data'
MONGO_HOST = os.environ.get('MONGO_HOST', 'mongo')

# Number of students answered to ORCT.
# Used to notify the instructor(s) when N students answer the first/last/middle question in a courselet.
MILESTONE_ORCT_NUMBER = 10

# Configure if Django signals should be suspended
SUSPEND_SIGNALS = False
EMAIL_BACKEND = 'django_ses.SESBackend'

DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

ONBOARDING_INTRODUCTION_COURSE_ID = 1
ONBOARDING_PERCENTAGE_DONE = 100

COURSELETS_EMAIL = 'info@courselets.org'
