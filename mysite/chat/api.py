import injections
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from .models import Message, Chat
from .serializers import MessageSerializer
from .services import ProgressHandler


@injections.has
class MessagesView(viewsets.ModelViewSet):
    next_handler = injections.depends(ProgressHandler)

    serializer_class = MessageSerializer
    queryset = Message.objects.all()
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = super(MessagesView, self).get_queryset()
        return queryset

    def get_object(self):
        queryset = super(MessagesView, self).get_queryset()
        message = queryset.filter(pk=self.kwargs[self.lookup_field]).first()
        if message and not message.chat:
            chat = Chat.objects.filter(user=self.request.user).first()
            chat.next_point = self.next_handler.next_point(current=message.content, chat=chat)
            chat.save()
            message.chat = chat
            message.save()
        return message
