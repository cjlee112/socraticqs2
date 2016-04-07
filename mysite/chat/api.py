import injections
from django.utils import timezone
from rest_framework.parsers import JSONParser
from rest_framework import viewsets, generics
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from .models import Message, Chat
from .serializers import MessageSerializer, ChatHistorySerializer, ChatProgressSerializer, ChatResourcesSerializer
from .services import ProgressHandler, FsmHandler
from .permissions import IsOwner, IsOwnerUser
from ct.models import Response as StudentResponse
from ct.models import UnitLesson


inj_alternative = injections.Container()
inj_alternative['next_handler'] = FsmHandler()
MessageSerializer = inj_alternative.inject(MessageSerializer)


def get_additional_messages(response, chat):
    print 'additional lessons'
    student_errors = response.studenterror_set.all()
    for each in student_errors:
        map(lambda ul: Message.objects.get_or_create(contenttype='unitlesson',
                                                     content_id=ul.id,
                                                     chat=chat,
                                                     owner=chat.user,
                                                     input_type='custom',
                                                     student_error=each,
                                                     kind='message',
                                                     is_additional=True),
            each.errorModel.get_em_resolutions()[1])


@injections.has
class MessagesView(generics.RetrieveUpdateAPIView, viewsets.GenericViewSet):
    """
    GET or UPDATE one message.
    """

    parser_classes = (JSONParser,)
    next_handler = injections.depends(ProgressHandler)

    serializer_class = MessageSerializer
    queryset = Message.objects.all()
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated, IsOwner)

    def retrieve(self, request, *args, **kwargs):
        message = self.get_object()
        chat_id = self.request.GET.get('chat_id')
        chat = Chat.objects.get(id=chat_id, user=self.request.user)
        next_point = chat.next_point

        if (
            message.contenttype in ['response', 'uniterror'] and
            message.content_id and
            next_point == message
        ):
            chat.next_point = self.next_handler.next_point(
                current=message.content, chat=chat, message=message, request=request
            )
            chat.save()
            serializer = self.get_serializer(message)
            return Response(serializer.data)

        if not message.chat or message.chat != chat or message.timestamp:
            print('FAULT')
            serializer = self.get_serializer(message)
            return Response(serializer.data)

        if message:
            # Set next message for user
            if not message.timestamp:
                message.timestamp = timezone.now()
                message.save()
            chat.next_point = self.next_handler.next_point(
                current=message.content, chat=chat, message=message, request=request
            )
            chat.save()
            message.chat = chat

        serializer = self.get_serializer(message)
        return Response(serializer.data)

    def perform_update(self, serializer):
        chat_id = self.request.data.get('chat_id')
        message = self.get_object()
        chat = Chat.objects.get(id=chat_id, user=self.request.user)

        # Check if message is not in current chat
        if not message.chat or message.chat != chat:
            return
        if message.input_type == 'text':
            message.chat = chat
            text = self.request.data.get('text')
            if not message.content_id:
                resp = StudentResponse(text=text)
                resp.lesson = message.lesson_to_answer.lesson
                resp.unitLesson = message.lesson_to_answer
                resp.course = message.chat.enroll_code.courseUnit.course
                resp.author = self.request.user
            else:
                resp = message.content
                resp.text = text
            resp.save()
            if not message.timestamp:
                message.content_id = resp.id
                chat.next_point = message
                chat.save()
                serializer.save(content_id=resp.id, timestamp=timezone.now(), chat=chat)
            else:
                serializer.save()
        if message.input_type == 'options' and message.kind != 'button':
            if (
                message.contenttype == 'uniterror' and
                'selected' in self.request.data
            ):
                message.chat = chat
                try:
                    selected = self.request.data.get('selected')[str(message.id)]['errorModel']
                except KeyError:
                    selected = []
                uniterror = message.content
                uniterror.save_response(user=self.request.user, response_list=selected)
                get_additional_messages(uniterror.response, chat)

                chat.next_point = self.next_handler.next_point(
                    current=message.content, chat=chat, message=message, request=self.request
                )
                chat.save()
                serializer.save(chat=chat)
            elif message.content_id and not message.student_error:
                message.chat = chat
                selfeval = self.request.data.get('option')
                resp = message.content
                resp.selfeval = selfeval
                resp.save()
                chat.next_point = message
                chat.save()
                serializer.save(content_id=resp.id, chat=chat)
            else:
                message.chat = chat
                selfeval = self.request.data.get('option')
                resp = message.student_error
                resp.status = selfeval
                resp.save()
                chat.next_point = message
                chat.save()
                message.text = selfeval
                message.save()
        if message.kind == 'button':
            chat.next_point = self.next_handler.next_point(
                current=message.content, chat=chat, message=message, request=self.request
            )
            chat.save()


class GetObjectMixin(object):
    """
    Implement get_object method.
    """
    def get_object(self):
        chat_id = self.request.GET.get('chat_id')
        obj = Chat.objects.get(id=chat_id)
        self.check_object_permissions(self.request, obj)
        return obj


class HistoryView(GetObjectMixin, generics.RetrieveAPIView):
    """
    List all messages in chat w/ additional info.
    """
    permission_classes = (IsAuthenticated, IsOwnerUser)

    def get(self, request, *args, **kwargs):
        chat = self.get_object()
        serializer = ChatHistorySerializer(chat)
        return Response(serializer.data)


class ProgressView(GetObjectMixin, generics.RetrieveAPIView):
    """
    Return progress for chat.
    """
    permission_classes = (IsAuthenticated, IsOwnerUser)

    def get(self, request, *args, **kwargs):
        chat = self.get_object()
        serializer = ChatProgressSerializer(chat)
        return Response(serializer.data)


@injections.has
class ResourcesView(viewsets.ModelViewSet):
    """
    Return resources for chat.
    """

    next_handler = FsmHandler()
    permission_classes = (IsAuthenticated, IsOwnerUser)

    def list(self, request, *args, **kwargs):
        chat_id = self.request.GET.get('chat_id')
        chat = Chat.objects.get(id=chat_id)
        self.check_object_permissions(self.request, chat)
        serializer = ChatResourcesSerializer(chat)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        chat_id = self.request.GET.get('chat_id')
        chat = Chat.objects.get(id=chat_id)
        self.check_object_permissions(self.request, chat)

        unitlesson = UnitLesson.objects.get(pk=pk)
        m = Message.objects.get_or_create(
            contenttype='unitlesson',
            content_id=unitlesson.id,
            chat=chat,
            owner=chat.user,
            input_type='custom',
            kind=unitlesson.lesson.kind,
            is_additional=True
        )[0]
        chat.next_point = self.next_handler.next_point(
            current=m.content, chat=chat, message=m, request=request
        )
        serializer = MessageSerializer(m)
        return Response(serializer.data)
