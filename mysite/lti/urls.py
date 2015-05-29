from django.conf.urls import url, patterns

from lti.views import create_courseref


urlpatterns = patterns(
    '',
    url(r'(^$|^unit/(?P<unit_id>\d+)/$)', 'lti.views.lti_init', name='lti_init'),
    url(r'^create_courseref/$', create_courseref, name='create_courseref'),
)
