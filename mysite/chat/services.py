"""
Handler container module.
"""

from fsm.fsm_base import FSMStack
from ct.models import Unit


class ProgressHandler(object):
    """
    Base class for handling Student progress.
    """
    def start(self):
        raise NotImplementedError

    def get_next(self):
        raise NotImplementedError


class FsmHandler(ProgressHandler):
    """
    FSM  handler to implement specific for FSM logic.
    """
    def start(self, request):
        fsm = FSMStack(request)
        fsm.push(request, 'lessonseq')

    def get_next(self, request):
        return fsm.pop(request)


class SequenceHandler(ProgressHandler):
    """
    Simple handler for non FSM logic.
    """
    def start(self):
        pass

    def get_next(self):
        return 'Non FSM'
