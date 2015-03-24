from django.conf.urls import url, patterns, include
from django.utils import importlib


urlpatterns = patterns('',
    url(r'^$', 'lti.views.lti_init', name='lti_init'),
)
