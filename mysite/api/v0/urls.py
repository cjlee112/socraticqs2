""" API v0 URLs. """
from django.conf.urls import url

from .views import ResponseViewSet, ErrorViewSet


urlpatterns = [
    url(
        r'^courses/(?P<course_id>\d+)/responses/$',
        ResponseViewSet.as_view({'get': 'list'}),
        name='responses'
    ),
    url(
        r'^courses/(?P<course_id>\d+)/errors/$',
        ErrorViewSet.as_view({'get': 'list'}),
        name='errors'
    ),
]
