from ct.models import *
from fsmspec import FSMSpecification, CallerNode
import random


def push_unit_fsm(self, edge, fsmStack, request, **kwargs):
    'edge method that launches FSM w/ a unit e.g. for pre/post-test'
    course = fsmStack.state.get_data_attr('course')
    unit = fsmStack.state.get_data_attr(self._unitAttr)
    fsmName = fsmStack.state.get_data_attr(self._fsmAttr) # FSM to run
    fsmStack.push(request, fsmName, dict(unit=unit, course=course)) # start it
    return edge.toNode

class START(object):
    '''In this activity you will answer a few preliminary questions, take
    a lesson on your chosen topic, and finally answer a few questions
    again. It should take about 15-30 minutes total.'''
    def start_event(self, node, fsmStack, request, trialName=None,
                    **kwargs):
        'event handler for START node'
        if not trialName:
            raise ValueError('no RT trial name provided!')
        r = random.randint(1, 2) # choose treatment for this student
        unit = fsmStack.state.get_data_attr('treatment%d' % r)
        fsmStack.state.set_data_attr('unit', unit)
        fsmStack.state.title = 'Studying: %s' % unit.title
        logName = 'rt_%s_%d' % (trialName, r) # log for this treatment
        fsmStack.state.activity = ActivityLog.get_or_create(logName)
        return node.get_path(fsmStack.state, request, **kwargs)
    next_edge = push_unit_fsm
    _unitAttr = 'testUnit'
    _fsmAttr = 'testFSM'
    # node specification data goes here
    path = 'ct:fsm_node'
    title = 'Start a Lesson'
    edges = (
            dict(name='next', toNode='PRETEST', title='Start initial questionaire'),
        )

class PRETEST(CallerNode):
    'Answer a few questions before starting the courselet.'
    return_edge = push_unit_fsm
    _unitAttr = 'unit'
    _fsmAttr = 'treatmentFSM'
    # node specification data goes here
    path = 'ct:fsm_node'
    title = 'Brief Questionaire'
    edges = (
            dict(name='return', toNode='TREATMENT', title='Start courselet'),
            dict(name='exceptCancel', toNode='PRETEST', title='run away!'),
        )

class TREATMENT(CallerNode):
    'Study a lesson on your selected topic.'
    return_edge = push_unit_fsm
    _unitAttr = 'testUnit'
    _fsmAttr = 'testFSM'
    # node specification data goes here
    path = 'ct:fsm_node'
    title = 'Courselet to study'
    edges = (
            dict(name='return', toNode='POSTTEST', title='Start final questionaire'),
            dict(name='exceptCancel', toNode='TREATMENT', title='run away!'),
        )

class POSTTEST(CallerNode):
    'Answer a few questions after finishing the courselet.'
    # node specification data goes here
    path = 'ct:fsm_node'
    title = 'Brief Questionaire'
    edges = (
            dict(name='return', toNode='END', title='Complete trial'),
            dict(name='exceptCancel', toNode='POSTTEST', title='run away!'),
        )

class END(object):
    # node specification data goes here
    path = 'ct:unit_tasks_student'
    title = 'Courselet completed'
    help = '''You have successfully completed this courselet.
    See below for suggested next steps for what you can work on next
    to help students with this courselet.'''

def get_specs():
    'get FSM specifications stored in this file'
    spec = FSMSpecification(name='randomtrial', hideTabs=True,
            title='Participate in a randomized trial',
            pluginNodes=[START, PRETEST, TREATMENT, POSTTEST, END],
        )
    return (spec,)
