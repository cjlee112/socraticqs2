from django.conf.urls import patterns, include, url
from django.conf import settings

from mysite.views import *
from pages.views import interested_form

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    # (r'^$', home_page),
    # Examples:
    # url(r'^$', 'mysite.views.home', name='home'),
    # url(r'^mysite/', include('mysite.foo.urls')),

    (r'^ct/', include('ct.urls', namespace='ct')),
    (r'^fsm/', include('fsm.urls', namespace='fsm')),

    # Login / logout.
    (r'^login/$', 'psa.views.custom_login'),
    (r'^logout/$', logout_page, {'next_page': '/login/'}),


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
