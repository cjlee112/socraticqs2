"""
Handler container module.
"""
from django.utils import timezone

from fsm.fsm_base import FSMStack
from ct.models import Lesson, UnitLesson
from core.common.mongo import c_chat_context
from .models import Message


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
        Lesson.ORCT_QUESTION: ('message',),
        Lesson.EXPLANATION: ('message', 'button'),
        Lesson.ERROR_MODEL: ('message', 'button'),
        'abort': ('message', 'button'),
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
                    Lesson.ORCT_QUESTION,
                    'abort',
                    'faqs'
                    ),
        'answers': ('message',),
        'add_faq': ('message', 'button'),
        'get_faq_answer': ('message', 'response'),
        'ask_faq_understanding': ('message', 'response')
    }

    def group_filter(self, message, next_message=None):
        """
        Return True if next message is allowed to group with current message.
        """
        if not next_message:
            return False
        elif next_message.kind in self.available_steps.get(message.kind, []) or \
                (message.kind == 'message' and next_message.sub_kind == 'faq'):
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
        # use chat.is_trial in future
        self.push_state(chat, request, chat.enroll_code.courseUnit.course.FSM_flow)
        m = chat.state.fsmNode.get_message(chat, request)
        chat.next_point = self.next_point(m.content, chat, m, request)
        chat.save()
        return chat.next_point

    # TODO: Simplify
    def next_point(self, current, chat, message, request, resources=False, updates=False):
        next_point = None
        additionals = Message.objects.filter(is_additional=True,
                                             chat=chat,
                                             student_error__isnull=False,
                                             timestamp__isnull=True)
        helps = Message.objects.filter(is_additional=True,
                                       chat=chat,
                                       kind='abort',
                                       timestamp__isnull=True)
        if chat.state and chat.state.fsmNode.node_name_is_one_of('END'):
            if chat.state.fsmNode.fsm.fsm_name_is_one_of('faq'):
                self.pop_state(chat)
                edge = chat.state.fsmNode.outgoing.get(name='next')
                chat.state.fsmNode = edge.transition(chat, request)
                chat.state.save()
                saved_actual_ul = (
                    chat.state.get_data_attr('saved_actual_ul')
                    if 'saved_actual_ul' in chat.state.load_json_data() else None)
                c_chat_context().update_one(
                    {"chat_id": chat.id},
                    {"$set": {"actual_ul_id": saved_actual_ul}}
                ) if saved_actual_ul else None
                next_point = chat.state.fsmNode.get_message(chat, request, current=current, message=message)
            elif chat.state.fsmNode.fsm.fsm_name_is_one_of('updates'):
                self.pop_state(chat)
                edge = chat.state.fsmNode.outgoing.get(name='next')
                chat.state.fsmNode = edge.transition(chat, request)
                chat.state.save()
                next_point = chat.state.fsmNode.get_message(chat, request, current=current, message=message)
            else:
                self.pop_state(chat)

        if chat.state and chat.state.fsmNode.node_name_is_one_of('FAQ'):
            chat_context = c_chat_context().find_one({'chat_id': chat.id})
            self.push_state(chat, request, 'faq', {
                'unitlesson': UnitLesson.objects.filter(id=chat_context.get('actual_ul_id')).first(),
                'chat': chat})
            next_point = chat.state.fsmNode.get_message(chat, request, current=current, message=message)
        if chat.state and chat.state.fsmNode.node_name_is_one_of('FAQ_UPDATES'):
            saved_actual_ul = c_chat_context().find_one({"chat_id": chat.id}).get('actual_ul_id')
            chat.state.set_data_attr('saved_actual_ul', saved_actual_ul)
            chat.state.save_json_data()
            thread_answer = chat.state.unitLesson.get_answers().first()
            self.push_state(chat, request, 'faq', {
                'unitlesson': thread_answer,
                'chat': chat,
                'updates': True,
                'new_faqs': (chat.state.get_data_attr('new_faqs')
                             if 'new_faqs' in chat.state.load_json_data() else None)})
            c_chat_context().update_one(
                {"chat_id": chat.id},
                {"$set": {"actual_ul_id": thread_answer.id}})
            next_point = chat.state.fsmNode.get_message(chat, request, current=current, message=message)
        elif helps and not chat.state.fsmNode.fsm.fsm_name_is_one_of('help'):
            unitlesson = helps.first().content
            self.push_state(chat, request, 'help', {'unitlesson': unitlesson})
            next_point = chat.state.fsmNode.get_message(chat, request, current=current, message=message)
        elif additionals and not chat.state.fsmNode.fsm.fsm_name_is_one_of('additional'):
            unitlesson = additionals.order_by('student_error').first().content
            self.push_state(chat, request, 'additional', {'unitlesson': unitlesson})
            next_point = chat.state.fsmNode.get_message(chat, request, current=current, message=message)
        elif resources:
            self.push_state(chat, request, 'resource', {'unitlesson': current})
            next_point = chat.state.fsmNode.get_message(chat, request)
        elif chat.state and chat.state.fsmNode.node_name_is_one_of('VIEWUPDATES') and 'next_update' in chat.state.load_json_data() and chat.state.get_data_attr('next_update') and chat.state.get_data_attr('next_update').get('enabled'):
            unit_lesson_id = chat.state.get_data_attr('next_update').get('thread_id')
            chat.state.set_data_attr('next_update', None)
            chat.state.save_json_data()
            self.push_state(
                chat,
                request,
                'updates',
                {'unitlesson': UnitLesson.objects.filter(id=unit_lesson_id).first(), 'chat': chat})
            next_point = chat.state.fsmNode.get_message(chat, request)
        elif chat.state:
            if not next_point:
                if not chat.state.fsmNode.node_name_is_one_of('END'):
                    # import ipdb; ipdb.set_trace()
                    edge = chat.state.fsmNode.outgoing.get(name='next')
                    chat.state.fsmNode = edge.transition(chat, request)
                    chat.state.save()
                if not (
                    chat.state.fsmNode.node_name_is_one_of('FAQ') or
                    chat.state.fsmNode.node_name_is_one_of('VIEWUPDATES')):
                    # import ipdb; ipdb.set_trace()
                    next_point = chat.state.fsmNode.get_message(chat, request, current=current, message=message)
                else:
                    next_point = self.next_point(
                        current=current, chat=chat, message=message, request=request
                    )
        else:
            return None

        if not message.timestamp:
            message.timestamp = timezone.now()
            message.save()

        # TODO: move to external function
        group = True
        while group:
            if self.group_filter(message, next_point):
                if next_point.input_type in ['text', 'options'] and next_point.sub_kind != 'faq':
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
        linkState = kwargs.get('linkState')
        course_unit = kwargs.get('courseUnit', chat.enroll_code.courseUnit)
        fsm_stack.push(request, name,
                       stateData={'unit': course_unit.unit,
                                  'course': course_unit.course},
                       startArgs=start_args,
                       isLiveSession=True,
                       linkState=linkState)
        fsm_stack.state.parentState = chat.state
        fsm_stack.state.save()
        chat.state = fsm_stack.state
        chat.save()

    def start_point(self, unit, chat, request, **kwargs):
        self.push_state(chat, request, self.FMS_name, **kwargs)
        m = chat.state.fsmNode.get_message(chat, request)
        chat.next_point = self.next_point(m.content, chat, m, request)
        chat.save()
        return chat.next_point


class ChatPreviewFsmHandler(FsmHandler):
    FMS_name = 'courselet_preview'


class TestHandler(GroupMessageMixin, ProgressHandler):
    """
    Test handler to implement specific for mocked FSM logic.
    """
    pass
