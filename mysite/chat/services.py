"""
Handler container module.
"""
from datetime import timedelta

from django.utils import timezone
from chat.models import TYPE_CHOICES, MESSAGE_TYPES

from fsm.fsm_base import FSMStack
from fsm.models import FSMNode
from ct.models import Unit, Lesson, UnitLesson, Response, CourseUnit
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
        Lesson.BASE_EXPLANATION: (Lesson.ORCT_QUESTION, 'message', 'button'),
        Lesson.EXPLANATION: ('message', 'button'),
        Lesson.ERROR_MODEL: ('message', 'button'),
        'response': ('message',
                     'answers',
                     'button',
                     Lesson.ORCT_QUESTION,
                     Lesson.BASE_EXPLANATION),
        'button': (),
        # 'answers': ('response'),
        'message': ('message',
                    'uniterror',
                    'button',
                    Lesson.EXPLANATION,
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
    FMS_name = 'chat'

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
        print "SERVICE.START_POINT = {}, FSM_NAME = {}".format(self, self.FSM_name)
        self.push_state(chat, request, self.FMS_name)
        m = chat.state.fsmNode.get_message(chat)
        chat.next_point = self.next_point(m.content, chat, m, request)
        chat.save()
        return chat.next_point

    def next_point(self, current, chat, message, request, resources=False):
        next_point = None
        additionals = Message.objects.filter(is_additional=True,
                                             chat=chat,
                                             student_error__isnull=False,
                                             timestamp__isnull=True)

        if chat.state and chat.state.fsmNode.name == 'END':
            self.pop_state(chat)
        if additionals and chat.state.fsmNode.fsm.name != 'additional':
            unitlesson = additionals.first().content
            self.push_state(chat, request, 'additional', {'unitlesson': unitlesson})
            next_point = chat.state.fsmNode.get_message(chat, current=current, message=message)
        elif resources:
            self.push_state(chat, request, 'resource', {'unitlesson': current})
            next_point = chat.state.fsmNode.get_message(chat)
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

        # import ipdb; ipdb.set_trace()
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


class LiveChatFsmHandler(FsmHandler):
    """
    FSM  handler to implement specific for FSM logic.
    """
    FMS_name = 'live_chat'

    def push_state(self, chat, request, name, start_args=None, **kwargs):
        fsm_stack = FSMStack(request)
        # import ipdb; ipdb.set_trace()
        linkState = kwargs.get('linkState')
        # data = linkState.get_all_state_data()
        course_unit = kwargs.get('courseUnit', chat.enroll_code.courseUnit)
        fsm_stack.push(request, name,
                       stateData={'unit': course_unit.unit,
                                  'course': course_unit.course},
                       startArgs=start_args,
                       isLiveSession=True,
                       linkState=linkState
        )
        fsm_stack.state.parentState = chat.state
        fsm_stack.state.save()
        chat.state = fsm_stack.state
        chat.save()

    def start_point(self, unit, chat, request, **kwargs):
        self.push_state(chat, request, self.FMS_name, **kwargs)
        # import ipdb; ipdb.set_trace()
        m = chat.state.fsmNode.get_message(chat)
        chat.next_point = self.next_point(m.content, chat, m, request)
        chat.save()
        return chat.next_point


class TestHandler(GroupMessageMixin, ProgressHandler):
    """
    Test handler to implement specific for mocked FSM logic.
    """
    pass
