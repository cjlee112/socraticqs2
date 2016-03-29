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
        chat.next_point = self.next_point(m.content, chat, m, request)
        chat.save()
        return chat.next_point

    def next_point(self, current, chat, message, request):
        next_point = None
        if (
            isinstance(current, Response) and
            current.selfeval and
            current.selfeval != Response.CORRECT
        ):
            edge = chat.state.fsmNode.outgoing.get(name='error')
        elif not chat.state.fsmNode.name == 'END':
            edge = chat.state.fsmNode.outgoing.get(name='next')

        if not chat.state.fsmNode.name == 'END':
            chat.state.fsmNode = edge.transition(chat, {})
            chat.state.save()
            next_point = chat.state.fsmNode.get_message(chat, current=current, message=message)
        else:
            additionals = Message.objects.filter(is_additional=True,
                                                 chat=chat,
                                                 timestamp__isnull=True)
            if additionals:
                unitlesson = additionals.first().content
                self.start_fsm(chat, request, 'additional', {'unitlesson': unitlesson})
                print "Getting additional lessons"
                # chat.state.unitLesson = unitlesson
                next_point = chat.state.fsmNode.get_message(chat,
                                                            current=current,
                                                            message=message)
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
