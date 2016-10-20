from django.conf.urls import url, patterns
from .views import CourseView

urlpatterns = patterns(
    '',
    url(
        r'^courses/(?P<course_id>\d+)/$',
        CourseView.as_view(),
        name='course_view'
    )
)