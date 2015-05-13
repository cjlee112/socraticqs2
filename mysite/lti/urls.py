from django.conf.urls import url, patterns, include
from django.utils import importlib


urlpatterns = patterns('',
	url(r'^ct/courses/(?P<course_id>\d+)/$', 'lti.views.lti_init', name='lti_init'),
    url(r'^ct/courses/(?P<course_id>\d+)/units/(?P<unit_id>\d+)/$', 'lti.views.lti_init', name='lti_init'),
)
