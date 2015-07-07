from django.conf.urls import url, patterns

from fsm.views import fsm_node, fsm_status


urlpatterns = patterns(
    '',
    url(r'^nodes/(?P<node_id>\d+)/$', fsm_node, name='fsm_node'),
    url(r'^nodes/$', fsm_status, name='fsm_status')
)
