from django.conf.urls import patterns, include, url
from django.conf import settings
from django.apps import apps

from mysite.views import *
from pages.views import interested_form

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from psa.forms import UsernameLoginForm, EmailLoginForm
from accounts.views import AccountSettingsView

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^ct/', include('ct.urls', namespace='ct')),
    url(r'^fsm/', include('fsm.urls', namespace='fsm')),
    url(r'^chat/', include('chat.urls', namespace='chat')),
    url(r'^lms/', include('lms.urls', namespace='lms')),

    # Login / logout.
    url(r'^login/$',
        'psa.views.custom_login',
        {'next_page': '/ct/',
         'login_form_cls': UsernameLoginForm}, name='login'),
    url(r'^signup/$', 'psa.views.signup', {'next_page': 'login'}, name='signup'),
    url(r'^new_login/$',
        'psa.views.custom_login',
        {
            'template_name': 'psa/new_custom_login.html',
            'next_page': '/',
            'login_form_cls': EmailLoginForm
        },
        name='new_login'),
    url(r'^logout/$', logout_page, {'next_page': '/login/'}, name='logout'),

    url(r'^accounts/', include('accounts.urls', namespace='accounts')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    url(r'^email-sent/$', 'psa.views.validation_sent'),
    url('', include('social.apps.django_app.urls', namespace='social')),

    url(r'^tmp-email-ask/$', 'psa.views.ask_stranger'),
    url(r'^set-pass/$', 'psa.views.set_pass'),

    url(r'^done/$', 'psa.views.done'),
    url(r'^lti/', include('lti.urls', namespace='lti')),
    url(r'^interested-form/', interested_form, name='interested-form'),
    # Base API
    url(r'^api/', include('api.urls', namespace='api')),
    # CMS
    url(r'^', include('cms.urls')),
)


if settings.DEBUG:
    urlpatterns += [
        url(r'markup/(?P<path>.*)$', markup_view),
        url(
            r'^media/(?P<path>.*)$',
            'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
        url(r'', include('django.contrib.staticfiles.urls')),
    ]
