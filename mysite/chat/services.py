"""
Handler container module.
"""

from fsm.fsm_base import FSMStack
from ct.models import Unit, Lesson, UnitLesson, Response
from .models import Message, MODEL_CHOISES


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
    def start_point(self, unit, chat):
        try:
            unit_lesson = unit.unitlesson_set.get(order=0)
            m = Message(contenttype='unitlesson', content_id=unit_lesson.id)
            m.save()
            chat.next_point = m
            chat.save()
            return m
        except IndexError:
            return None

    def next_point(self, current, chat):
        """
        current: UnitLesson, Response or list of ErrorModels.
        """
        if isinstance(current, UnitLesson) and current.lesson.kind == Lesson.BASE_EXPLANATION:
            m = Message(contenttype='unitlesson', content_id=current.get_next_lesson().id)
            m.save()
            next_point = m
        elif isinstance(current, UnitLesson) and current.lesson.kind == Lesson.ORCT_QUESTION:
            m = Message(contenttype='response')
            m.save()
            next_point = m
        elif isinstance(current, Response) and not current.selfeval:
            next_point = current.unitLesson.get_answers().first()
        elif isinstance(current, UnitLesson) and current.kind == Lesson.ANSWER:
            next_point = 'assess'
        elif isinstance(current, Response) and current.selfeval:
            if current.selfeval == Response.CORRECT:
                next_point = current.unitLesson.get_next_lesson()
            else:
                next_point = list(r.unitLesson.get_errors()) + unit.get_aborts()
        elif isinstance(current, list):
            next_point = current[0].parent.get_next_lesson()
        return next_point
