""" API v0 URLs. """
from django.conf.urls import url
from django.urls import path

from .views import (
    EchoDataView,
    ResponseViewSet,
    ErrorViewSet,
    GenReportView,
    CourseReportViewSet,
    HealthCheck,
    OnboardingStatus,
    OnboardingBpAnalysis,
    BestPracticeCreate,
    BestPracticeUpload,
    CourseletViewSet,
    CourseletThreadsViewSet,
)

app_name = 'v0'

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

    url(r'^onboarding-status/$', OnboardingStatus.as_view(), name='onboarding-status'),

    url(r'^bp-analysis/$', OnboardingBpAnalysis.as_view(), name='onboarding_bp2-analysis'),
    path('bp/create/', BestPracticeCreate.as_view(), name='bp-creation'),
    path('bp/upload/', BestPracticeUpload.as_view(), name='bp-upload'),

    path('courselets/<int:pk>/', CourseletViewSet.as_view({'put': 'update', 'get': 'retrieve'}), name='courselet-api'),
    path('courselets/<int:pk>/threads/', CourseletThreadsViewSet.as_view(), name='courselet-threads-api')

]
