from django.conf.urls import url
from django.urls import include, path
from django.conf import settings
from django.contrib import admin
from django.views.static import serve
from social_core.utils import setting_name

from mysite.views import markup_view, logout_page
from pages.views import interested_form
from psa.forms import UsernameLoginForm
from psa.views import (
    complete, social_auth_complete, custom_login, signup,
    validation_sent, ask_stranger, set_pass, done, login_as_user, inactive_user_error
)


admin.autodiscover()


extra = getattr(settings, setting_name('TRAILING_SLASH'), True) and '/' or ''

urlpatterns = [
    url(r'^ct/', include(('ct.urls', 'ct'), namespace='ct')),
    url(r'^ctms/', include(('ctms.urls', 'ctms'), namespace='ctms')),

    url(r'^fsm/', include(('fsm.urls', 'fsm'), namespace='fsm')),
    url(r'^chat/', include(('chat.urls', 'chat'), namespace='chat')),
    url(r'^lms/', include(('lms.urls', 'lms'), namespace='lms')),

    # Login / logout.
    url(r'^login/$', custom_login, {'login_form_cls': UsernameLoginForm}, name='login'),
    url(r'^inactive-user/$', inactive_user_error, name="inactive-user-error"),
    url(r'^signup/$', signup, name='signup'),
    url(r'^new_login/$', custom_login,
        {
            'template_name': 'psa/new_custom_login.html',
        },
        name='new_login'),
    url(r'^logout/$', logout_page, {'next_page': '/new_login/'}, name='logout'),
    url(r'^new_logout/$', logout_page, {'next_page': '/new_login/'}, name='new_logout'),

    url(r'^accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/login_as_user/(?P<user_id>\d+)/?$', login_as_user, name='admin_login_as_user'),
    path('admin/django-ses/', include('django_ses.urls')),
    path('admin/', admin.site.urls),

    url(r'^email-sent/$', validation_sent, name='email_sent'),
    url(r'^complete/email{0}$'.format(extra), complete, name='complete'),
    url(r'^complete/(?P<backend>[^/]+){0}$'.format(extra), social_auth_complete,
        name='soc_complete'),

    url('', include(('social_django.urls', 'social'), namespace='social')),

    url(r'^tmp-email-ask/$', ask_stranger),
    url(r'^set-pass/$', set_pass),

    url(r'^done/$', done, name='done'),

    url(r'^lti/', include(('lti.urls', 'lti'), namespace='lti')),
    url(r'^interested-form/', interested_form, name='interested-form'),
    # Base API
    url(r'^api/', include(('api.urls', 'api'), namespace='api')),
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
        print("No django-debug-toolbar installed. Running without it...")
