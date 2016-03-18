"""
Handler container module.
"""
from datetime import timedelta

from django.utils import timezone

from fsm.fsm_base import FSMStack
from fsm.models import FSMNode
from ct.models import Unit, Lesson, UnitLesson, Response
from .models import Message, UnitError, ChatDivider, MODEL_CHOISES, Message


class ProgressHandler(object):
    """
    Base class for handling Student progress.
    """
    def start_point(self):
        raise NotImplementedError

    def next_point(self):
        raise NotImplementedError


class GroupMessageMixin(object):
    """
    Should be used by MessageSerializer.

    Mixin should create additional messages via `self.next_point`.
    """
    available_steps = {
        Lesson.BASE_EXPLANATION: (Lesson.ORCT_QUESTION,),
        Lesson.ERROR_MODEL: ('message'),
        'response': ('message'),
        'message': ('message'),
    }

    def group_filter(self, message, next_message=None):
        """
        Return True if next message is allowed to group with current message.
        """
        if not next_message:
            return False
        elif next_message.kind in self.available_steps.get(message.kind, []):
            return True


class FsmHandler(GroupMessageMixin, ProgressHandler):
    """
    FSM  handler to implement specific for FSM logic.
    """
    def start_fsm(self, chat, request, name, start_args=None):
        fsm_stack = FSMStack(request)
        course_unit = chat.enroll_code.courseUnit
        fsm_stack.push(request, name,
                       stateData={'unit': course_unit.unit,
                                  'course': course_unit.course},
                       startArgs=start_args)
        chat.state = fsm_stack.state

    def start_point(self, unit, chat, request):
        self.start_fsm(chat, request, 'chat')
        m = chat.state.fsmNode.get_message(chat)
        chat.next_point = m
        chat.save()
        return m

    def next_point(self, current, chat, message, request):
        next_point = None

        if isinstance(current, UnitLesson) and chat.state.fsmNode.name == 'ASK':
            m = Message(contenttype='response',
                        input_type='text',
                        lesson_to_answer=current,
                        type='user',
                        chat=chat,
                        owner=chat.user)
            m.save()
            next_point = m
        elif isinstance(current, UnitLesson) and chat.state.fsmNode.name == 'ASSESS':
            m = Message(
                contenttype='response',
                content_id=message.response_to_check.id,
                input_type='options',
                type='user',
                chat=chat,
                owner=chat.user
            )
            m.save()
            next_point = m
        elif isinstance(current, Response) and current.selfeval:
            if current.selfeval == Response.CORRECT:
                edge = chat.state.fsmNode.outgoing.get(name='next')
            else:
                edge = chat.state.fsmNode.outgoing.get(name='error')
        elif not chat.state.fsmNode.name == 'END':
            edge = chat.state.fsmNode.outgoing.get(name='next')
        if not next_point and not chat.state.fsmNode.name == 'END':
            chat.state.fsmNode = edge.transition(chat, {})
            chat.state.save()
            next_point = chat.state.fsmNode.get_message(chat, current=current, message=message)
        elif chat.state.fsmNode.name == 'END':
            unitlesson = Message.objects.filter(is_additional=True,
                                                timestamp__isnull=True).first().content
            if unitlesson:
                self.start_fsm(chat, request, 'additional', {'unitlesson': unitlesson})
                print "Getting additional lessons"
                print unitlesson
                chat.state.unitLesson = unitlesson
                next_point = chat.state.fsmNode.get_message(chat, current=current, message=message)
                print next_point.__dict__
        # if current message is additional then the next one also will be additional
        if message.is_additional:
            next_point.is_additional = True
            next_point.save()

        return next_point


class SequenceHandler(GroupMessageMixin, ProgressHandler):
    """
    Simple handler for non FSM logic.
    """
    def start_point(self, unit, chat, request):
        try:
            unit_lesson = unit.unitlesson_set.get(order=0)
            m = Message(
                contenttype='unitlesson',
                content_id=unit_lesson.id,
                chat=chat,
                owner=chat.user,
                input_type='custom',
                kind=unit_lesson.lesson.kind
            )
            m.save()
            chat.next_point = m
            chat.save()
            return m
        except IndexError:
            return None

    def next_point(self, current, chat, message, request):
        """
        current: UnitLesson, Response or list of ErrorModels.
        """
        if isinstance(current, UnitLesson) and current.lesson.kind == Lesson.BASE_EXPLANATION:
            try:
                next_lesson = current.get_next_lesson()
                m = Message(
                    contenttype='unitlesson',
                    content_id=next_lesson.id,
                    chat=chat,
                    owner=chat.user,
                    input_type='custom',
                    kind=next_lesson.lesson.kind
                )
            except UnitLesson.DoesNotExist:
                m = Message(
                    input_type='finish',
                    type='custom',
                    chat=chat,
                    owner=chat.user,
                    kind='message',
                    text='You have finished lesson sequence. Well done.'
                )
            m.save()
            next_point = m

        elif isinstance(current, UnitLesson) and current.lesson.kind == Lesson.ORCT_QUESTION:
            m = Message(
                contenttype='response',
                input_type='text',
                lesson_to_answer=current,
                type='user',
                chat=chat,
                owner=chat.user,
                kind='response'
            )
            m.save()
            next_point = m
        elif isinstance(current, Response) and not current.selfeval:
            answer = current.unitLesson.get_answers().first()
            m = Message(
                contenttype='unitlesson',
                content_id=answer.id,
                response_to_check=current,
                chat=chat,
                owner=chat.user,
                input_type='custom',
                kind=answer.kind
            )
            m.save()
            next_point = m
        elif isinstance(current, UnitLesson) and current.lesson.kind == Lesson.ANSWER:
            m = Message(
                contenttype='response',
                content_id=message.response_to_check.id,
                input_type='options',
                type='user',
                chat=chat,
                owner=chat.user,
                kind='response'
            )
            m.save()
            next_point = m
        elif isinstance(current, Response) and current.selfeval:
            if current.selfeval == Response.CORRECT:
                try:
                    ul = current.unitLesson.get_next_lesson()
                    m = Message(
                        contenttype='unitlesson',
                        content_id=ul.id,
                        chat=chat,
                        owner=chat.user,
                        input_type='custom',
                        kind=ul.lesson.kind
                    )
                except UnitLesson.DoesNotExist:
                    m1 = Message(
                        input_type='finish',
                        type='custom',
                        chat=chat,
                        owner=chat.user,
                        kind='message',
                        text='You have finished lesson sequence. Well done.'
                    )
                    m1.timestamp = message.timestamp + timedelta(seconds=1)
                    m1.save()
                    m = Message(
                        input_type='finish',
                        type='custom',
                        chat=chat,
                        owner=chat.user,
                        kind='message',
                        text='Now you can try to learn something else.'
                    )
                m.save()
                next_point = m
            else:
                uniterror = UnitError.get_by_message(message)
                # Creating next Message that wait for selected errorModels
                m = Message(
                    contenttype='uniterror',
                    content_id=uniterror.id,
                    input_type='custom',
                    chat=chat,
                    owner=chat.user,
                    kind='uniterror'
                )
                m.save()
                next_point = m
        elif isinstance(current, UnitError):
            try:
                ul = current.response.unitLesson.get_next_lesson()
                m = Message(
                    contenttype='unitlesson',
                    content_id=ul.id,
                    chat=chat,
                    owner=chat.user,
                    input_type='custom',
                    kind=ul.lesson.kind
                )
            except UnitLesson.DoesNotExist:
                m1 = Message(
                    input_type='finish',
                    type='custom',
                    chat=chat,
                    owner=chat.user,
                    kind='message',
                    text='You have finished lesson sequence. Well done.'
                )
                m1.timestamp = message.timestamp + timedelta(seconds=1)
                m1.save()
                m = Message(
                    input_type='finish',
                    type='custom',
                    chat=chat,
                    owner=chat.user,
                    kind='message',
                    text='Now you can try to learn something else.'
                )
            m.save()
            next_point = m

        # if current message is additional then the next one also will be additional
        if message.is_additional:
            next_point.is_additional = True
            next_point.save()

        group = True
        while group:
            if self.group_filter(message, next_point):
                message.timestamp = timezone.now()
                message.save()
                next_point.timestamp = message.timestamp + timedelta(seconds=1)
                next_point.save()
                next_point = self.next_point(
                    current=next_point.content, chat=chat, message=next_point, request=request
                )
            else:
                group = False

        return next_point
