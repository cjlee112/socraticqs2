import injections
from django.conf.urls import patterns, url, include
from django.views.generic import TemplateView
from rest_framework.routers import SimpleRouter

from .views import ChatInitialView
from .api import MessagesView, HistoryView, ProgressView
from .services import SequenceHandler, FsmHandler


inj = injections.Container()
# inj['next_handler'] = SequenceHandler()
inj['next_handler'] = FsmHandler()
# Injects appropriate ProgressHandler
MessagesView = inj.inject(MessagesView)
ChatInitialView = inj.inject(ChatInitialView)

router = SimpleRouter()
router.register(r'messages', MessagesView, base_name='messages')

urlpatterns = patterns(
    '',
    url(r'^enrollcode/(?P<enroll_key>[a-zA-Z0-9]+)/$', ChatInitialView.as_view(), name='chat_enroll'),
    url(r'^history/$', HistoryView.as_view(), name='history'),
    url(r'^progress/$', ProgressView.as_view(), name='progress'),
    url(r'^', include(router.urls)),
)
