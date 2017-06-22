import injections
from django.conf.urls import patterns, url, include
from django.views.generic import TemplateView
from rest_framework.routers import SimpleRouter
from chat.api import AddUnitByChatProgressView

from chat.views import CourseletPreviewView, ChatAddLessonView, TestChatInitialView
from .views import ChatInitialView, InitializeLiveSession
from .api import MessagesView, HistoryView, ProgressView, ResourcesView
from .services import FsmHandler


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
    # open chat
    url(
        r'^enrollcode/(?P<enroll_key>[a-zA-Z0-9]+)/(?P<chat_id>\d+)?/?$',
        ChatInitialViewFSM.as_view(),
        name='chat_enroll'
    ),
    url(
        r'^tester/enrollcode/(?P<enroll_key>[a-zA-Z0-9]+)/$',
        TestChatInitialView.as_view(),
        name='tester_chat_enroll'
    ),
    # preview
    url(
        r'^preview/enrollcode/(?P<enroll_key>[a-zA-Z0-9]+)/$',
        CourseletPreviewView.as_view(),
        name='preview_courselet'
    ),
    # add units
    url(
        r'^course/(?P<course_id>\d+)/courselet/(?P<courselet_id>\d+)/add_units/enrollcode/(?P<enroll_key>[a-zA-Z0-9]+)/$',
        ChatAddLessonView.as_view(),
        name='add_units_by_chat'
    ),
    url(r'^history/$', HistoryView.as_view(), name='history'),
    url(r'^progress/$', ProgressView.as_view(), name='progress'),
    url(r'^progress/add_unit/$', AddUnitByChatProgressView.as_view(), name='add_unit_progress'),


    url(r'^initLiveSession/(?P<state_id>\d+)/$',
        InitializeLiveSession.as_view(), name="init_live_chat"),
    url(r'^', include(router.urls)),
)
