from ct.models import *
from fsmspec import FSMSpecification

def next_lesson(self, edge, fsmStack, request, unit=None, **kwargs):
    'edge method that moves us to right state for next lesson (or END)'
    fsm = edge.fromNode.fsm
    if unit: # get first lesson
        nextUL = unit.get_exercises()[0]
    else:
        try:
            nextUL = fsmStack.state.unitLesson.get_next_lesson()
        except UnitLesson.DoesNotExist:
            return fsm.get_node('END')
    fsmStack.state.unitLesson = nextUL # set the lesson to display
    return edge.toNode # just show it as a LESSON slide

class START(object):
    '''Initialize data for viewing a courselet, and go immediately
    to first lesson. '''
    def start_event(self, node, fsmStack, request, **kwargs):
        'event handler for START node'
        unit = fsmStack.state.get_data_attr('unit')
        fsmStack.state.title = 'Slideshow: %s' % unit.title
        return fsmStack.state.transition(fsmStack, request, 'next',
                                         unit=unit, **kwargs)
    next_edge = next_lesson
    # node specification data goes here
    title = 'Start This Courselet'
    edges = (
            dict(name='next', toNode='LESSON', title='View Next Lesson'),
        )

class LESSON(object):
    '''View a lesson explanation. '''
    def next_edge(self, edge, fsmStack, request, **kwargs):
        'go to ANSWER if present, or just call next_lesson()'
        fsm = edge.fromNode.fsm
        ul = fsmStack.state.unitLesson
        answers = ul.get_answers()
        if ul.is_question() and len(answers) > 0: # get the answer
            fsmStack.state.unitLesson = answers[0]
            return fsm.get_node(name='ANSWER')
        else:
            return next_lesson(self, edge, fsmStack, request, **kwargs)
    # node specification data goes here
    path = 'ct:lesson'
    title = 'View an explanation or question'
    edges = (
            dict(name='next', toNode='LESSON', title='View Next Slide'),
        )
    
class ANSWER(object):
    '''View answer slide '''
    def next_edge(self, edge, fsmStack, request, **kwargs):
        fsmStack.state.unitLesson = fsmStack.state.unitLesson.parent
        return next_lesson(self, edge, fsmStack, request, **kwargs)
    # node specification data goes here
    path = 'ct:lesson'
    title = 'View an answer'
    edges = (
            dict(name='next', toNode='LESSON', title='View Next Slide'),
        )

class END(object):
    # node specification data goes here
    path = 'ct:unit_concepts_student'
    title = 'Courselet slide show completed'
    help = '''Thanks for viewing this slide show.
    See below for suggested next steps on concepts you can study in
    this courselet.'''

        
def get_specs():
    'get FSM specifications stored in this file'
    spec = FSMSpecification(name='slideshow', hideTabs=True,
            title='View courselet as a slide show',
            pluginNodes=[START, LESSON, ANSWER, END],
        )
    return (spec,)

