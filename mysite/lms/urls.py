from django.conf.urls import url, patterns

from lti.views import create_courseref


urlpatterns = patterns(
    '',
    url(
        r'^courses/(?P<course_id>\d+)/$',
        'lms.views.course_view',
        name='lms_course_view'
    )
)