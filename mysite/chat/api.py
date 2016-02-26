import injections
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from .models import Message
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
        return queryset.filter(pk=self.kwargs[self.lookup_field]).first()
