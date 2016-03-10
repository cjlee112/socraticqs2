"""
Handler container module.
"""

from fsm.fsm_base import FSMStack
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
    def start_point(self, request):
        fsm = FSMStack(request)
        fsm.push(request, 'lessonseq')

    def next_point(self, request):
        return fsm.pop(request)


class SequenceHandler(ProgressHandler):
    """
    Simple handler for non FSM logic.
    """
    def start_point(self, unit, chat, request):
        try:
            unit_lesson = unit.unitlesson_set.get(order=0)
            m = Message(contenttype='unitlesson', content_id=unit_lesson.id)
            m.save()
            chat.next_point = m
            chat.save(request)
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
                m = Message(contenttype='unitlesson', content_id=next_lesson.id)
            except UnitLesson.DoesNotExist:
                divider = ChatDivider(text="You have finished lesson sequence. Well done.")
                divider.save()
                m = Message(
                    contenttype='chatdivider',
                    content_id=divider.id,
                    input_type='finish',
                    type='breakpoint')
            m.save()
            next_point = m
        elif isinstance(current, UnitLesson) and current.lesson.kind == Lesson.ORCT_QUESTION:
            m = Message(
                contenttype='response',
                input_type='text',
                lesson_to_answer=current,
                type='user')
            m.save()
            next_point = m
        elif isinstance(current, Response) and not current.selfeval:
            m = Message(
                contenttype='unitlesson',
                content_id=current.unitLesson.get_answers().first().id,
                response_to_check=current
            )
            m.save()
            next_point = m
        elif isinstance(current, UnitLesson) and current.lesson.kind == Lesson.ANSWER:
            m = Message(
                contenttype='response',
                content_id=message.response_to_check.id,
                input_type='options',
                type='user'
            )
            m.save()
            next_point = m
        elif isinstance(current, Response) and current.selfeval:
            if current.selfeval == Response.CORRECT:
                m = Message(
                    contenttype='unitlesson',
                    content_id=current.unitLesson.get_next_lesson().id,
                )
                m.save()
                next_point = m
            else:
                uniterror = UnitError.get_by_message(message)
                m = Message(
                    contenttype='uniterror',
                    content_id=uniterror.id,
                    input_type='errors'
                )
                m.save()
                next_point = m
        elif isinstance(current, UnitError):
            m = Message(
                contenttype='unitlesson',
                content_id=current.response.unitLesson.get_next_lesson().id,
            )
            m.save()
            next_point = m
        return next_point
