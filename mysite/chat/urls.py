import injections
from django.conf.urls import patterns, url, include
from django.views.generic import TemplateView
from rest_framework.routers import SimpleRouter

from .views import ChatInitialView
from .api import MessagesView
from .services import SequenceHandler


inj = injections.Container()
inj['next_handler'] = SequenceHandler()
# Injects appropriate ProgressHandler
MessagesView = inj.inject(MessagesView)
ChatInitialView = inj.inject(ChatInitialView)

router = SimpleRouter()
router.register(r'messages', MessagesView, base_name='messages')

urlpatterns = patterns(
    '',
    url(r'^$', ChatInitialView.as_view(), name='chat_init'),
    url(r'^', include(router.urls)),
)
