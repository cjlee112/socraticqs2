import injections
from django.conf.urls import url, include
from django.urls import path
from django.views.generic import TemplateView
from rest_framework.routers import SimpleRouter

from .views import (
    ChatInitialView, InitializeLiveSession, CourseletPreviewView, CheckChatInitialView
)
from .api import (
    MessagesView, HistoryView, ProgressView, ResourcesView, InitNewChat, UpdatesView, AddUnitByChatProgressView
)
from .services import FsmHandler


inj = injections.Container()
inj['next_handler'] = FsmHandler()
MessagesViewFSM = inj.inject(MessagesView)
ChatInitialViewFSM = inj.inject(ChatInitialView)

router = SimpleRouter()
router.register(r'messages', MessagesViewFSM, base_name='messages')
router.register(r'resources', ResourcesView, base_name='resources')


app_name = 'chat'


urlpatterns = [
    url(r'^ui/$', TemplateView.as_view(template_name="cui/index.html")),
    url(
        r'^enrollcode/(?P<enroll_key>[a-zA-Z0-9]+)/(?P<chat_id>0)/?$',
        InitNewChat.as_view(),
        name='init_chat_api'
    ),

    url(
        r'^enrollcode/(?P<enroll_key>[a-zA-Z0-9]+)/(?P<chat_id>\d+)/history/?$',
        ChatInitialViewFSM.as_view(template_name='chat/chat_history.html'),
        name='courselet_history'
    ),
    url(
        r'^enrollcode/(?P<enroll_key>[a-zA-Z0-9]+)/(?P<chat_id>\d+)?/?$',
        ChatInitialViewFSM.as_view(),
        name='chat_enroll'
    ),
    url(
        r'^tester/enrollcode/(?P<enroll_key>[a-zA-Z0-9]+)/$',
        CheckChatInitialView.as_view(),
        name='tester_chat_enroll'
    ),
    # preview
    url(
        r'^preview/enrollcode/(?P<enroll_key>[a-zA-Z0-9]+)/$',
        CourseletPreviewView.as_view(),
        name='preview_courselet'
    ),
    url(r'^history/$', HistoryView.as_view(), name='history'),
    url(r'^progress/$', ProgressView.as_view(), name='progress'),
    url(r'^progress/add_unit/$', AddUnitByChatProgressView.as_view(), name='add_unit_progress'),
    path('updates/<int:pk>/', UpdatesView.as_view(), name='updates'),

    url(r'^initLiveSession/(?P<state_id>\d+)/$',
        InitializeLiveSession.as_view(), name="init_live_chat"),
    url(r'^', include(router.urls)),
]
