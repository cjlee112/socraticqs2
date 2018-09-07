""" API v0 URLs. """
from django.conf.urls import url

from .views import (
    EchoDataView,
    ResponseViewSet,
    ErrorViewSet,
    GenReportView,
    CourseReportViewSet,
    HealthCheck
)


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
    url(
        r'^courses/(?P<course_id>\d+)/reports/$',
        CourseReportViewSet.as_view({'get': 'list'}),
        name='reports'
    ),
    url(
        r'^gen-report/$',
        GenReportView.as_view(),
        name='gen-report'
    ),
    url(
        r'^echo/data/$',
        EchoDataView.as_view(),
        name='echo-data',
    ),
    url(r'^health/*$', HealthCheck.as_view(), name='health-check'),
]
