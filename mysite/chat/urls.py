import injections
from django.conf.urls import patterns, url, include
from django.views.generic import TemplateView
from rest_framework.routers import SimpleRouter

from .views import ChatInitialView
from .api import MessagesView, HistoryView, ProgressView
from .services import FsmHandler


inj = injections.Container()
inj['next_handler'] = FsmHandler()
MessagesViewFSM = inj.inject(MessagesView)
ChatInitialViewFSM = inj.inject(ChatInitialView)

router = SimpleRouter()
router.register(r'messages', MessagesViewFSM, base_name='messages')

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
    url(r'^', include(router.urls)),
)
