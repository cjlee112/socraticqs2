import injections
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from rest_framework.parsers import JSONParser
from rest_framework import viewsets, generics
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from .models import Message, Chat, ChatDivider
from .serializers import (
    MessageSerializer,
    ChatHistorySerializer,
    ChatProgressSerializer,
    ChatResourcesSerializer
)
from .services import ProgressHandler, FsmHandler
from .permissions import IsOwner
from ct.models import Response as StudentResponse
from ct.models import UnitLesson

inj_alternative = injections.Container()
inj_alternative['next_handler'] = FsmHandler()
MessageSerializer = inj_alternative.inject(MessageSerializer)


def get_additional_messages(response, chat):
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
            reversed(each.errorModel.get_em_resolutions()[1]))


class ValidateMixin(object):
    """
    Validate request for `chat_id`.

    Can raise ValidationError.

    params: chat_id
    return: Chat instance
    """
    def validate_and_get_chat(self, chat_id):
        if not chat_id:
            raise ValidationError('Request should include chat_id.')
        chat = Chat.objects.filter(id=chat_id).first()
        if not chat:
            raise ValidationError('There is no chat by chat_id.')
        return chat


@injections.has
class MessagesView(ValidateMixin, generics.RetrieveUpdateAPIView, viewsets.GenericViewSet):
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
        try:
            chat = self.validate_and_get_chat(chat_id)
        except ValidationError as e:
            return Response({'errors': str(e)})
        self.check_object_permissions(self.request, chat)
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
            serializer = self.get_serializer(message)
            return Response(serializer.data)

        if message and message.kind != 'button':
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

    def update(self, request, *args, **kwargs):
        chat_id = self.request.data.get('chat_id')
        try:
            chat = self.validate_and_get_chat(chat_id)
        except ValidationError as e:
            return Response({'errors': str(e)})
        self.check_object_permissions(self.request, chat)

        message = self.get_object()
        if message.input_type == 'text' and not self.request.data.get('text'):
            return Response({'error': 'Empty response. Enter something!'})
        return super(MessagesView, self).update(request, *args, **kwargs)

    def perform_update(self, serializer):
        chat_id = self.request.data.get('chat_id')
        message = self.get_object()
        chat = Chat.objects.get(id=chat_id, user=self.request.user)
        activity = chat.state and chat.state.activity

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
                resp.activity = activity
                # NOTE: next line is a temporary solution.
                resp.confidence = StudentResponse.SURE
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
                    selected = self.request.data.get(
                        'selected'
                    )[str(message.id)]['errorModel']
                except KeyError:
                    selected = []
                uniterror = message.content
                uniterror.save_response(user=self.request.user, response_list=selected)
                if not message.chat.is_live:
                    get_additional_messages(uniterror.response, chat)

                chat.next_point = self.next_handler.next_point(
                    current=message.content,
                    chat=chat,
                    message=message,
                    request=self.request
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
                current=message.content,
                chat=chat,
                message=message,
                request=self.request
            )
            chat.save()


class HistoryView(ValidateMixin, generics.RetrieveAPIView):
    """
    List all messages in chat w/ additional info.
    """
    permission_classes = (IsAuthenticated, IsOwner)

    def get(self, request, *args, **kwargs):
        chat_id = self.request.GET.get('chat_id')
        try:
            chat = self.validate_and_get_chat(chat_id)
        except ValidationError as e:
            return Response({'errors': str(e)})
        self.check_object_permissions(self.request, chat)
        serializer = ChatHistorySerializer(chat)
        return Response(serializer.data)


class ProgressView(ValidateMixin, generics.RetrieveAPIView):
    """
    Return progress for chat.
    """
    permission_classes = (IsAuthenticated, IsOwner)

    def get(self, request, *args, **kwargs):
        chat_id = self.request.GET.get('chat_id')
        try:
            chat = self.validate_and_get_chat(chat_id)
        except ValidationError as e:
            return Response({'errors': str(e)})
        self.check_object_permissions(self.request, chat)
        serializer = ChatProgressSerializer(chat)
        return Response(serializer.data)


@injections.has
class ResourcesView(ValidateMixin, viewsets.ModelViewSet):
    """
    Return resources for chat.
    """
    next_handler = FsmHandler()
    permission_classes = (IsAuthenticated, IsOwner)
    serializer_class = ChatResourcesSerializer

    def list(self, request, *args, **kwargs):
        chat_id = self.request.GET.get('chat_id')
        try:
            chat = self.validate_and_get_chat(chat_id)
        except ValidationError as e:
            return Response({'errors': str(e)})
        self.check_object_permissions(self.request, chat)
        serializer = ChatResourcesSerializer(chat)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        chat_id = self.request.GET.get('chat_id')
        try:
            chat = self.validate_and_get_chat(chat_id)
        except ValidationError as e:
            return Response({'errors': str(e)})
        self.check_object_permissions(self.request, chat)

        unitlesson = get_object_or_404(UnitLesson, pk=pk)

        divider = ChatDivider(
            text=unitlesson.lesson.title, unitlesson=unitlesson
        )

        divider.save()
        m = Message.objects.get_or_create(
            contenttype='chatdivider',
            content_id=divider.id,
            input_type='custom',
            type='breakpoint',
            chat=chat,
            owner=chat.user,
            kind='message',
            is_additional=True
        )[0]
        chat.next_point = self.next_handler.next_point(
            current=unitlesson, chat=chat, message=m, request=request, resources=True
        )
        serializer = MessageSerializer(m)
        return Response(serializer.data)
