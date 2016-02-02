from django.conf.urls import patterns, include, url
from django.apps import apps
from rest_framework import routers

from mysite.views import *
from ct.api import ResponseViewSet, ErrorViewSet

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

router = routers.DefaultRouter()
router.register(r'api/courses/responses', ResponseViewSet)
router.register(r'api/courses/errors', ErrorViewSet)

urlpatterns = patterns(
    '',
    (r'^$', home_page),
    # Examples:
    # url(r'^$', 'mysite.views.home', name='home'),
    # url(r'^mysite/', include('mysite.foo.urls')),

    (r'^ct/', include('ct.urls', namespace='ct')),
    (r'^fsm/', include('fsm.urls', namespace='fsm')),
    (r'^chat/', include('chat.urls', namespace='chat')),

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

    url(r'^api/courses/(?P<course_id>\d+)/responses/$', ResponseViewSet.as_view({'get': 'list'}), name='responses'),
    url(r'^api/courses/(?P<course_id>\d+)/errors/$', ErrorViewSet.as_view({'get': 'list'}), name='errors'),
    url(r'^', include(router.urls)),
)

if apps.is_installed('lti'):
    urlpatterns += patterns(
        '',
        url(r'^lti/', include('lti.urls', namespace='lti')),
    )
