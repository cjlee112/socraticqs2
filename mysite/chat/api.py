import injections
from rest_framework import viewsets, mixins, views, generics
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from .models import Message, Chat
from .serializers import MessageSerializer
from .services import ProgressHandler
from ct.models import Response as StudentResponse


@injections.has
class MessagesView(generics.RetrieveUpdateAPIView, viewsets.GenericViewSet):
    next_handler = injections.depends(ProgressHandler)

    serializer_class = MessageSerializer
    queryset = Message.objects.all()
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, *args, **kwargs):
        # TODO it will be better to move custom logic to sirializer
        message = self.get_object()

        if message.input_type == 'text':
            serializer = self.get_serializer(message)
            return Response(serializer.data)

        if message and not message.chat:
            chat = Chat.objects.filter(user=self.request.user).first()
            chat.next_point = self.next_handler.next_point(current=message.content, chat=chat, message=message)
            chat.save(self.request)
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
            text = self.request.data.get('input').get('text')
            resp = StudentResponse(text=text)
            resp.lesson = message.lesson_to_answer.lesson
            resp.unitLesson = message.lesson_to_answer
            resp.course = message.chat.enroll_code.courseUnit.course
            resp.author = self.request.user
            resp.save()
            message.content_id = resp.id
            chat.next_point = self.next_handler.next_point(current=message.content, chat=chat, message=message)
            chat.save()
        if message.input_type == 'errors':
            message.chat = chat
            uniterror = UnitError.get_by_message(message)
            uniterror.save_response(user=request.user, response_list=self.request.data.get('err_list'))
            chat.next_point = self.next_handler.next_point(current=message.content, chat=chat, message=message)
            chat.save()
        serializer.save(chat=chat, content_id=resp.id)
