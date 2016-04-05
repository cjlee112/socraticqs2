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
        Lesson.BASE_EXPLANATION: (Lesson.ORCT_QUESTION, 'message'),
        Lesson.EXPLANATION: (Lesson.ORCT_QUESTION, Lesson.EXPLANATION, 'message'),
        Lesson.ERROR_MODEL: ('message'),
        'response': ('message',
                     'answers',
                     Lesson.ORCT_QUESTION,
                     Lesson.BASE_EXPLANATION),
        # 'answers': ('response'),
        'message': ('message',
                    'uniterror',
                    Lesson.BASE_EXPLANATION,
                    Lesson.ORCT_QUESTION)
    }

    def group_filter(self, message, next_message=None):
        """
        Return True if next message is allowed to group with current message.
        """
        if not next_message:
            return False
        elif next_message.kind in self.available_steps.get(message.kind, []):
            next_message.timestamp = timezone.now()
            next_message.save()
            return True


class FsmHandler(GroupMessageMixin, ProgressHandler):
    """
    FSM  handler to implement specific for FSM logic.
    """

    def push_state(self, chat, request, name, start_args=None):
        fsm_stack = FSMStack(request)
        course_unit = chat.enroll_code.courseUnit
        fsm_stack.push(request, name,
                       stateData={'unit': course_unit.unit,
                                  'course': course_unit.course},
                       startArgs=start_args)
        fsm_stack.state.parentState = chat.state
        fsm_stack.state.save()
        chat.state = fsm_stack.state
        chat.save()

    def pop_state(self, chat):
        next_state = chat.state.parentState
        current_state = chat.state
        chat.state = next_state
        chat.save()
        current_state.delete()

    def start_point(self, unit, chat, request):
        self.push_state(chat, request, 'chat')
        m = chat.state.fsmNode.get_message(chat)
        chat.next_point = self.next_point(m.content, chat, m, request)
        chat.save()
        return chat.next_point

    def next_point(self, current, chat, message, request):
        next_point = None
        additionals = Message.objects.filter(is_additional=True,
                                             chat=chat,
                                             student_error__isnull=False,
                                             timestamp__isnull=True)
        resources = Message.objects.filter(is_additional=True,
                                           chat=chat,
                                           student_error__isnull=True,
                                           timestamp__isnull=True)

        if chat.state and chat.state.fsmNode.name == 'END':
            self.pop_state(chat)
        if additionals and chat.state.fsmNode.fsm.name != 'additional':
            unitlesson = additionals.order_by('student_error').first().content
            self.push_state(chat, request, 'additional', {'unitlesson': unitlesson})
            next_point = chat.state.fsmNode.get_message(chat, current=current, message=message)
            print "Getting additional lessons"
        elif resources and not chat.state:
            unitlesson = resources.first().content
            self.push_state(chat, request, 'resource', {'unitlesson': unitlesson})
            edge = chat.state.fsmNode.outgoing.get(name='next')
            chat.state.fsmNode = edge.transition(chat, {})
            chat.state.save()
            next_point = chat.state.fsmNode.get_message(chat, current=current, message=message)
            print "Getting resource lessons"
        elif chat.state:
            edge = chat.state.fsmNode.outgoing.get(name='next')
            chat.state.fsmNode = edge.transition(chat, {})
            chat.state.save()
            next_point = chat.state.fsmNode.get_message(chat, current=current, message=message)
        else:
            return None

        if not message.timestamp:
            message.timestamp = timezone.now()
            message.save()
        group = True
        while group:
            if self.group_filter(message, next_point):
                if next_point.input_type in ['text', 'options']:
                    break
                next_point = self.next_point(
                    current=next_point.content, chat=chat, message=next_point, request=request
                )

            else:
                group = False

        return next_point
