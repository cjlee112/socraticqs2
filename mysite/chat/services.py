"""
Handler container module.
"""

from fsm.fsm_base import FSMStack
from ct.models import Unit


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
    def start_point(self, unit):
        try:
            return unit.get_exercises()[0]
        except IndexError:
            return None

    def next_point(self):
        return 'Non FSM'
