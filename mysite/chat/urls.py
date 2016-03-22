import injections
from django.conf.urls import patterns, url, include
from django.views.generic import TemplateView
from rest_framework.routers import SimpleRouter

from .views import ChatInitialView
from .api import MessagesView, HistoryView, ProgressView
from .services import SequenceHandler, FsmHandler


inj = injections.Container()
inj['next_handler'] = FsmHandler()
MessagesViewFSM = inj.inject(MessagesView)
ChatInitialViewFSM = inj.inject(ChatInitialView)
#
# inj_alternative = injections.Container()
# inj_alternative['next_handler'] = SequenceHandler()
# MessagesViewAlternative = inj_alternative.inject(MessagesView)
# ChatInitialViewAlternative = inj_alternative.inject(ChatInitialView)


router = SimpleRouter()
router.register(r'messages', MessagesViewFSM, base_name='messages')
# router.register(r'alternative/messages', MessagesViewAlternative, base_name='messages')

urlpatterns = patterns(
    '',
    url(
        r'^enrollcode/(?P<enroll_key>[a-zA-Z0-9]+)/$',
        ChatInitialViewFSM.as_view(),
        name='chat_enroll'
    ),
    # url(
    #     r'^alternative/enrollcode/(?P<enroll_key>[a-zA-Z0-9]+)/$',
    #     ChatInitialViewAlternative.as_view(),
    #     name='chat_enroll'
    # ),
    url(r'^history/$', HistoryView.as_view(), name='history'),
    url(r'^progress/$', ProgressView.as_view(), name='progress'),
    url(r'^', include(router.urls)),
)
