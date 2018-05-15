from django.conf.urls import url
from lms.views import LMSTesterCourseView
from .views import CourseView

urlpatterns = [
    url(
        r'^courses/(?P<course_id>\d+)/$',
        CourseView.as_view(),
        name='course_view'
    ),
    url(r'test/courses/(?P<course_id>\d+)/$', LMSTesterCourseView.as_view(), name='tester_course_view'),
]
