from django.conf.urls import url, patterns
from lms.views import TesterCourseView
from .views import CourseView

urlpatterns = patterns(
    '',
    url(
        r'^courses/(?P<course_id>\d+)/$',
        CourseView.as_view(),
        name='course_view'
    ),
    url(r'test/courses/(?P<course_id>\d+)/$', TesterCourseView.as_view(), name='tester_course_view'),
)