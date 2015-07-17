from django.conf.urls import url, patterns

from lti.views import create_courseref


urlpatterns = patterns(
    '',
    url(
        r'^ct/courses/(?P<course_id>\d+)/units/(?P<unit_id>\d+)/$',
        'lti.views.lti_init',
        name='lti_init_course_directly_with_unit'
    ),
    url(
        r'^ct/courses/(?P<course_id>\d+)/$',
        'lti.views.lti_init',
        name='lti_init_course_directly'
    ),
    url(r'(^$|^unit/(?P<unit_id>\d+)/$)', 'lti.views.lti_init', name='lti_init'),
    url(r'^create_courseref/$', create_courseref, name='create_courseref'),
)
