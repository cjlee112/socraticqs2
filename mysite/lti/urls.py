from django.conf.urls import url

from lti.views import create_courseref, lti_init


urlpatterns = [
    url(
        r'^ct/courses/(?P<course_id>\d+)/units/(?P<unit_id>\d+)/$',
        lti_init,
        name='lti_init_course_directly_with_unit'
    ),
    url(
        r'^ct/courses/(?P<course_id>\d+)/$',
        lti_init,
        name='lti_init_course_directly'
    ),
    url(r'(^$|^unit/(?P<unit_id>\d+)/$)', lti_init, name='lti_init'),
    url(r'^create_courseref/$', create_courseref, name='create_courseref'),
]
