import injections
from rest_framework import viewsets, mixins, views, generics
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from .models import Message, Chat, UnitError
from .serializers import MessageSerializer, ChatHistorySerializer, ChatProgressSerializer
from .services import ProgressHandler
from .permissions import IsOwner
from ct.models import Response as StudentResponse


@injections.has
class MessagesView(generics.RetrieveUpdateAPIView, viewsets.GenericViewSet):
    next_handler = injections.depends(ProgressHandler)

    serializer_class = MessageSerializer
    queryset = Message.objects.all()
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated, IsOwner)

    def retrieve(self, request, *args, **kwargs):
        # TODO it will be better to move custom logic to sirializer
        message = self.get_object()

        if (
            message.input_type == 'text' or
            message.input_type == 'options' or
            message.input_type == 'errors'
        ):
            serializer = self.get_serializer(message)
            return Response(serializer.data)

        if message and not message.chat:
            chat = Chat.objects.filter(user=self.request.user).first()
            if message.input_type != 'finish':
                chat.next_point = self.next_handler.next_point(current=message.content, chat=chat, message=message)
                chat.save()
            message.chat = chat
            message.save()
        serializer = self.get_serializer(message)
        return Response(serializer.data)

    def perform_update(self, serializer):
        # TODO it will be better to move custom logic to sirializer
        message = self.get_object()
        chat = Chat.objects.filter(user=self.request.user).first()
        if message.input_type == 'text':
            message.chat = chat
            text = self.request.data.get('text')
            resp = StudentResponse(text=text)
            resp.lesson = message.lesson_to_answer.lesson
            resp.unitLesson = message.lesson_to_answer
            resp.course = message.chat.enroll_code.courseUnit.course
            resp.author = self.request.user
            resp.save()
            message.content_id = resp.id
            chat.next_point = self.next_handler.next_point(current=message.content, chat=chat, message=message)
            chat.save()
            serializer.save(chat=chat, content_id=resp.id)
        if message.input_type == 'options':
            message.chat = chat
            selfeval = self.request.data.get('selfeval')
            resp = message.content
            resp.selfeval = selfeval
            resp.save()
            chat.next_point = self.next_handler.next_point(current=message.content, chat=chat, message=message)
            chat.save()
            serializer.save(chat=chat, content_id=resp.id)
        if message.input_type == 'errors':
            message.chat = chat
            uniterror = message.content
            uniterror.save_response(user=self.request.user, response_list=self.request.data.get('err_list'))
            chat.next_point = self.next_handler.next_point(current=message.content, chat=chat, message=message)
            chat.save()
            serializer.save(chat=chat)


class HistoryView(generics.RetrieveAPIView):
    """
    List all messages in chat w/ additional info.
    """
    def get(self, request, *args, **kwargs):
        chat = Chat.objects.all().first()
        serializer = ChatHistorySerializer(chat)
        return Response(serializer.data)


class ProgressView(generics.RetrieveAPIView):
    """
    Return progress for chat.
    """
    def get(self, request, *args, **kwargs):
        chat = Chat.objects.all().first()
        serializer = ChatProgressSerializer(chat)
        return Response(serializer.data)
