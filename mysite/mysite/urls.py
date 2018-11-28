from django.conf.urls import include, url
from django.conf import settings
from django.apps import apps
from django.contrib import admin
from django.views.static import serve
from social_core.utils import setting_name

from mysite.views import markup_view, logout_page
from pages.views import interested_form
from accounts.views import AccountSettingsView
from psa.forms import UsernameLoginForm, EmailLoginForm
from psa.views import (
    complete, social_auth_complete, custom_login, signup,
    validation_sent, ask_stranger, set_pass, done, login_as_user, inactive_user_error
)


admin.autodiscover()


extra = getattr(settings, setting_name('TRAILING_SLASH'), True) and '/' or ''

urlpatterns = [
    url(r'^ct/', include('ct.urls', namespace='ct')),
    url(r'^ctms/', include('ctms.urls', namespace='ctms')),

    url(r'^fsm/', include('fsm.urls', namespace='fsm')),
    url(r'^chat/', include('chat.urls', namespace='chat')),
    url(r'^lms/', include('lms.urls', namespace='lms')),

    # Login / logout.
    url(r'^login/$', custom_login,
        {
            'next_page': '/ct/',
            'login_form_cls': UsernameLoginForm
        }, name='login'),
    url(r'^inactive-user/$', inactive_user_error, name="inactive-user-error"),
    url(r'^signup/$', signup, name='signup'),
    url(r'^new_login/$', custom_login,
        {
            'template_name': 'psa/new_custom_login.html',
            'next_page': 'accounts:profile_update',
            'login_form_cls': EmailLoginForm
        },
        name='new_login'),
    url(r'^logout/$', logout_page, {'next_page': '/login/'}, name='logout'),
    url(r'^new_logout/$', logout_page, {'next_page': '/ctms/'}, name='new_logout'),

    url(r'^accounts/', include('accounts.urls', namespace='accounts')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/login_as_user/(?P<user_id>\d+)/?$', login_as_user, name='admin_login_as_user'),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^email-sent/$', validation_sent, name='email_sent'),
    url(r'^complete/email{0}$'.format(extra), complete, name='complete'),
    url(r'^complete/(?P<backend>[^/]+){0}$'.format(extra), social_auth_complete,
        name='soc_complete'),

    url('', include('social_django.urls', namespace='social')),

    url(r'^tmp-email-ask/$', ask_stranger),
    url(r'^set-pass/$', set_pass),

    url(r'^done/$', done, name='done'),

    url(r'^lti/', include('lti.urls', namespace='lti')),
    url(r'^interested-form/', interested_form, name='interested-form'),
    # Base API
    url(r'^api/', include('api.urls', namespace='api')),
    # CMS
    url(r'^pages/', include('pages.urls')),
    url(r'^', include('cms.urls')),
]


if settings.DEBUG:
    urlpatterns += [
        url(r'markup/(?P<path>.*)$', markup_view),
        url(
            r'^media/(?P<path>.*)$',
            serve,
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
        url(r'', include('django.contrib.staticfiles.urls')),
    ]
    try:
        import debug_toolbar
        urlpatterns = [
            url(r'^__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        print "No django-debug-toolbar installed. Running without it..."
