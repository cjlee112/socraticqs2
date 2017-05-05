from ct.models import UnitLesson, Lesson


def has_answer_next_edge(self, edge, fsmStack, request, useCurrent=False, **kwargs):
    """
    Edge method that moves us to right state for next (or END).
    """
    fsm = edge.fromNode.fsm
    ul = fsmStack.state.unitLesson
    if ul.is_question():
        return fsm.get_node(name='UNIT_ANSWER')
    else:  # just a lesson to read
        return fsm.get_node(name='WELL_DONE')


def want_to_continue(self, edge, fsmStack, request, useCurrent=False, **kwargs):
    fsm = edge.fromNode.fsm
    # ul = fsmStack.state.unitLesson
    if isinstance(request, dict):
        return fsm.get_node('START')
    nodes_map = {
        'yes': 'START',
        'no': 'END'
    }
    return fsm.get_node(nodes_map.get(request.data.get('option'), 'END'))

class START_(object):
    """
    Typically this involves several steps:
    search Courselets for an existing lesson that matches your goals;
    if not, define the concept your new lesson will be about;
    write a new lesson.
    """
    # node specification data goes here
    path = 'fsm:fsm_node'
    title = 'Define your topic'
    help = ''' Your answers will be saved to your courselet and you can go back and edit them at any time
    by clicking on the back button in the uper left corner.
    '''
    edges = (
        dict(name='next', toNode='UNIT_NAME_TITLE', title='Input topic'),
    )


class GET_TITLE(object):
    """
    In this stage, you search Courselets to see if you can find
    an existing Lesson that you can use as-is or with your own edits.
    """
    # path = 'ct:unit_lessons'
    title = ''
    help = ''
    edges = (
            dict(name='next', toNode='UNIT_NAME_TITLE', title='name your unit'),
            # dict(name='create_UnitLesson', toNode='END', title='Added a lesson'),
        )


class START(object):
    path = 'fsm:fsm_node'
    title = 'Name your unit'
    help = 'Input unit title'
    edges = (
            dict(name='next', toNode='GET_UNIT_NAME_TITLE', title='get title',
                 description='',
                 showOption=True),
            # dict(name='create_UnitLesson', toNode='END', title='Added a lesson'),
        )


class GET_UNIT_NAME_TITLE(object):
    path = 'fsm:fsm_node'
    title = 'unit name title'
    edges = (
        dict(name='next', toNode='UNIT_QUESTION', title='Unit title added'),
    )


class UNIT_QUESTION(object):
    path = 'fsm:fsm_node'
    title = 'Phrase your question'
    edges = (
        dict(name='next', toNode='GET_UNIT_QUESTION', title='get unit question'),
    )


class GET_UNIT_QUESTION(object):
    path = 'fsm:fsm_node'
    title = 'get a question'
    edges = (
        dict(name='next', toNode='HAS_UNIT_ANSWER', title='got unit question'),
    )


class HAS_UNIT_ANSWER(object):
    path = 'fsm:fsm_node'
    title = 'Does this unit has an answer?'
    edges = (
        dict(name='next', toNode='GET_HAS_UNIT_ANSWER', title='get unit answer'),
    )


class GET_HAS_UNIT_ANSWER(object):
    path = 'fsm:fsm_node'
    title = 'get answer'
    next_edge = has_answer_next_edge
    edges = (
        dict(name='next', toNode='UNIT_ANSWER', title='Well done!'),
        dict(name='not_a_question', toNode='WELL_DONE', title='unit is not a question')
    )

class UNIT_ANSWER(object):
    path = 'fsm:fsm_node'
    title = 'Phrase your answer for question of this unit'
    # next_edge = has_answer_next_edge
    edges = (
        dict(name='next', toNode='GET_UNIT_ANSWER', title='got unit answer'),
        # dict(name='not_a_question', toNode='NOT_A_QUESTION', title='unit is not a question')
    )

class GET_UNIT_ANSWER(object):
    path = 'fsm:fsm_node'
    title = ''
    edges = (
        dict(name='next', toNode='WELL_DONE', title='got unit answer'),
    )




class WELL_DONE(object):
    path = 'fsm:fsm_node'
    title = 'Well done!'
    help = '''You have created  new unit in this courselet. Another important concept on Courselets is error models.
    They are lessons based on common misconceptions that your students can select when they self-assess.
    We won't cover error models in this interactive tutorial, but check them out as you start using this courselet with
    students.

    Want to add another unit to this courselet?
    '''
    next_edge = want_to_continue
    edges = (
        dict(name='next', toNode='START', title='unit saved'),
        dict(name='end', toNode='END', title='finish'),
    )


class END(object):
    path = 'fsm:fsm_node'
    # node specification data goes here
    # path = 'ct:ul_tasks'
    title = 'Done writing new lesson'
    help = '''Thanks for writing this new Lesson!
    See below for suggested next steps on concepts you can study in
    this courselet.'''


def get_specs():
    'get FSM specifications stored in this file'
    from fsm.fsmspec import FSMSpecification
    spec = FSMSpecification(
        name='chat_add_lesson',
        hideTabs=True,
        title='Add a New Lesson',
        description='''Guides you through the steps of adding a new
                    lesson to this courselet''',
        pluginNodes=[START, GET_UNIT_NAME_TITLE, UNIT_QUESTION, GET_UNIT_QUESTION, HAS_UNIT_ANSWER, GET_HAS_UNIT_ANSWER,
                    GET_UNIT_ANSWER, UNIT_ANSWER, WELL_DONE, END],
        fsmGroups=('teach/unit_tasks',),
    )
    return (spec,)
