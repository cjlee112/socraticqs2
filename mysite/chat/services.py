"""
Handler container module.
"""

from fsm.fsm_base import FSMStack
from fsm.models import FSMNode
from ct.models import Unit, Lesson, UnitLesson, Response
from .models import Message, UnitError, ChatDivider, MODEL_CHOISES


class ProgressHandler(object):
    """
    Base class for handling Student progress.
    """
    def start_point(self):
        raise NotImplementedError

    def next_point(self):
        raise NotImplementedError


class FsmHandler(ProgressHandler):
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


class SequenceHandler(ProgressHandler):
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
            )
            m.save()
            chat.next_point = m
            chat.save()
            return m
        except IndexError:
            return None

    def next_point(self, current, chat, message):
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
                )
            except UnitLesson.DoesNotExist:
                divider = ChatDivider(text="You have finished lesson sequence. Well done.")
                divider.save()
                m = Message(
                    contenttype='chatdivider',
                    content_id=divider.id,
                    input_type='finish',
                    type='breakpoint',
                    chat=chat,
                    owner=chat.user
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
                owner=chat.user
            )
            m.save()
            next_point = m
        elif isinstance(current, Response) and not current.selfeval:
            m = Message(
                contenttype='unitlesson',
                content_id=current.unitLesson.get_answers().first().id,
                response_to_check=current,
                chat=chat,
                owner=chat.user,
                input_type='custom',
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
                owner=chat.user
            )
            m.save()
            next_point = m
        elif isinstance(current, Response) and current.selfeval:
            if current.selfeval == Response.CORRECT:
                m = Message(
                    contenttype='unitlesson',
                    content_id=current.unitLesson.get_next_lesson().id,
                    chat=chat,
                    owner=chat.user,
                    input_type='custom',
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
                    owner=chat.user
                )
                m.save()
                next_point = m
        elif isinstance(current, UnitError):
            m = Message(
                contenttype='unitlesson',
                content_id=current.response.unitLesson.get_next_lesson().id,
                chat=chat,
                owner=chat.user,
                input_type='custom',
            )
            m.save()
            next_point = m
        # if current message is additional then the next one also will be additional
        if message.is_additional:
            next_point.is_additional = True
            next_point.save()
        return next_point
