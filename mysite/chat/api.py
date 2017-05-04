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
from ct.models import Response as StudentResponse, Lesson, CourseUnit
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


is_chat_add_lesson = lambda msg: msg.chat.state and msg.chat.state.fsmNode.fsm.name == 'chat_add_lesson'


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

    def roll_fsm_forward(self, chat, message):
        chat.next_point = self.next_handler.next_point(
            current=message.content, chat=chat, message=message, request=self.request
        )
        chat.save()
        message.chat = chat
        print " ROLL_FSM_FORWARD " * 10
        # import ipdb; ipdb.set_trace()
        serializer = self.get_serializer(message)
        return Response(serializer.data)

    def retrieve(self, *args, **kwargs):
        message = self.get_object()
        chat_id = self.request.GET.get('chat_id')
        try:
            chat = self.validate_and_get_chat(chat_id)
        except ValidationError as e:
            return Response({'errors': str(e)})
        self.check_object_permissions(self.request, chat)
        next_point = chat.next_point


        # import ipdb; ipdb.set_trace()

        if is_chat_add_lesson(message) and message.content_id and next_point == message:
            print " RETRIEVE " * 10
            # import ipdb; ipdb.set_trace()
            return self.roll_fsm_forward(chat, message)

        if (
            message.contenttype in ['response', 'uniterror'] and
            message.content_id and
            next_point == message
        ):
            return self.roll_fsm_forward(chat, message)

        if not message.chat or message.chat != chat or message.timestamp:
            serializer = self.get_serializer(message)
            return Response(serializer.data)

        if message and message.kind != 'button':
            # Set next message for user
            if not message.timestamp:
                message.timestamp = timezone.now()
                message.save()
            chat.next_point = self.next_handler.next_point(
                current=message.content, chat=chat, message=message, request=self.request
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

        is_in_node = lambda node: message.chat.state.fsmNode.name == node

        # import ipdb; ipdb.set_trace()

        # Check if message is not in current chat
        if not message.chat or message.chat != chat:
            return

        # Chat add unit lesson
        if is_chat_add_lesson(message):
            message.chat = chat
            text = self.request.data.get('text')
            option = self.request.data.get('option')
            course_unit = message.chat.enroll_code.courseUnit
            unit = course_unit.unit

            if message.input_type == 'options' and is_in_node('HAS_UNIT_ANSWER'):
                print " HAS_UNIT_ANSWER " * 10
                # import ipdb; ipdb.set_trace()
                # if not message.timestamp:
                    # message.content_id = resp.id
                    #     chat.next_point = message
                    #     chat.save()
                    #     serializer.save(timestamp=timezone.now(), chat=chat)
                    # else:
                    #     serializer.save()
                message = self.next_handler.next_point(
                    current=message.content,
                    chat=chat,
                    message=message,
                    request=self.request
                )
                chat.next_point = message
                chat.save()
                # import ipdb; ipdb.set_trace()
                serializer.save(chat=chat, timestamp=timezone.now())
                # else:
                #     serializer.save()


            # if message.input_type == 'text':
            if is_in_node('GET_UNIT_NAME_TITLE'):
                print " GET_UNIT_NAME_TITLE " * 10
                # import ipdb; ipdb.set_trace()
                if course_unit and unit:
                    if not message.content_id:
                        lesson = Lesson.objects.create(title=text, addedBy=self.request.user,
                                                       kind=Lesson.ORCT_QUESTION, text='')
                        lesson.treeID = lesson.id
                        lesson.save()
                        ul = UnitLesson.create_from_lesson(
                            lesson=lesson, unit=unit, kind=UnitLesson.COMPONENT, order='APPEND',
                            )
                    else:
                        ul = message.content
                    if not message.timestamp:
                        serializer.save(
                            content_id=ul.id,
                            timestamp=timezone.now(),
                            chat=chat,
                            text=text,
                            contenttype='unitlesson'
                        )
                    else:
                        serializer.save()

            if is_in_node('GET_UNIT_QUESTION'):
                print " GET_UNIT_QUESTION " * 10
                # import ipdb; ipdb.set_trace()
                ul = message.content
                ul.lesson.text = text
                ul.lesson.save()
                if not message.timestamp:
                    serializer.save(
                        content_id=ul.id,
                        timestamp=timezone.now(),
                        chat=chat,
                        contenttype='unitlesson',
                        text=text
                    )
                else:
                    serializer.save()

            if is_in_node('GET_UNIT_ANSWER'):
                #  create answer
                ul = message.content

                if not message.timestamp:
                    unit_lesson_answer = UnitLesson.create_from_lesson(
                        unit=ul.unit, lesson=self.lesson, parent=ul, kind=UnitLesson.ANSWERS
                    )
                    # chat.next_point = message
                    chat.save()
                    serializer.save(content_id=ul.id, timestamp=timezone.now(), chat=chat,
                                    contenttype='unitlesson', text=text)
                else:
                    serializer.save()

            # if is_in_node('HAS_UNIT_ANSWER'):
            #     # message =
            #     import ipdb; ipdb.set_trace()

            if is_in_node('GET_HAS_UNIT_ANSWER'):
                print " GET_HAS_UNIT_ANSWER " * 10
                # import ipdb; ipdb.set_trace()
                yes_no_map = {
                    'yes': True,
                    'no': False
                }
                ul = message.content
                has_answer = yes_no_map.get(self.request.data.get('option'))
                if has_answer is None:
                    raise ValueError("Recieved not valid response from user")

                ul.lesson.kind = Lesson.ORCT_QUESTION if has_answer else Lesson.BASE_EXPLANATION
                ul.lesson.save()
                message.text = self.request.data.get('option')
                message.save()

        if message.input_type == 'text' and not is_chat_add_lesson(message):
            message.chat = chat
            text = self.request.data.get('text')
            if not message.content_id:
                resp = StudentResponse(text=text)
                resp.lesson = message.lesson_to_answer.lesson
                resp.unitLesson = message.lesson_to_answer
                resp.course = message.chat.enroll_code.courseUnit.course
                resp.author = self.request.user
                resp.activity = activity
                resp.is_test = chat.is_test
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
