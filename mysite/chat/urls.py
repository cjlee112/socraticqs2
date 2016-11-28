import injections
from django.conf.urls import patterns, url, include
from django.views.generic import TemplateView
from rest_framework.routers import SimpleRouter

from .views import ChatInitialView, InitializeLiveSession
from .api import MessagesView, HistoryView, ProgressView, ResourcesView
from .services import FsmHandler, LiveChatFsmHandler


inj = injections.Container()
inj['next_handler'] = FsmHandler()
MessagesViewFSM = inj.inject(MessagesView)
ChatInitialViewFSM = inj.inject(ChatInitialView)

router = SimpleRouter()
router.register(r'messages', MessagesViewFSM, base_name='messages')
router.register(r'resources', ResourcesView, base_name='resources')

urlpatterns = patterns(
    '',
    url(r'^ui/$', TemplateView.as_view(template_name="cui/index.html")),
    url(
        r'^enrollcode/(?P<enroll_key>[a-zA-Z0-9]+)/$',
        ChatInitialViewFSM.as_view(),
        name='chat_enroll'
    ),
    url(r'^history/$', HistoryView.as_view(), name='history'),
    url(r'^progress/$', ProgressView.as_view(), name='progress'),

    url(r'^initLiveSession/(?P<state_id>\d+)/$',
        InitializeLiveSession.as_view(), name="init_live_chat"),
    url(r'^', include(router.urls)),
)
