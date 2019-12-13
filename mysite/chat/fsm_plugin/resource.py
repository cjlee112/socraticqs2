from ct.models import UnitStatus


def next_lesson(self, edge, fsmStack, request, useCurrent=False, **kwargs):
    """
    Edge method that moves us to right state for next lesson (or END).
    """
    fsm = edge.fromNode.fsm
    nextUL = fsmStack.state.unitLesson
    if nextUL.is_question():
        return fsm.get_node(name='ASK')
    else:  # just a lesson to read
        return edge.toNode


def check_selfassess_and_next_lesson(self, edge, fsmStack, request, useCurrent=False, **kwargs):
    fsm = edge.fromNode.fsm

    if not fsmStack.next_point.content.selfeval == 'correct':
        return fsm.get_node('ERRORS')

    return edge.toNode


def get_lesson_url(self, node, state, request, **kwargs):
    """
    Get URL for any lesson.
    """
    course = state.get_data_attr('course')
    unitStatus = state.get_data_attr('unitStatus')
    ul = unitStatus.get_lesson()
    return ul.get_study_url(course.pk)


class START(object):
    """
    Initialize data for viewing a courselet, and go immediately
    to first lesson (not yet completed).
    """
    def start_event(self, node, fsmStack, request, **kwargs):
        """
        Event handler for START node.
        """
        unit = fsmStack.state.get_data_attr('unit')
        fsmStack.state.title = 'Study: %s' % unit.title

        try:  # use unitStatus if provided
            unitStatus = fsmStack.state.get_data_attr('unitStatus')
        except AttributeError:  # create new, empty unitStatus
            unitStatus = UnitStatus(unit=unit, user=request.user)
            unitStatus.save()
            fsmStack.state.set_data_attr('unitStatus', unitStatus)
        fsmStack.state.unitLesson = kwargs['unitlesson']
        return fsmStack.state.transition(
            fsmStack, request, 'next', useCurrent=True, **kwargs
        )

    next_edge = next_lesson
    # node specification data goes here
    title = 'Start This Courselet'
    edges = (
        dict(name='next', toNode='LESSON', title='View Next Lesson'),
    )


class LESSON(object):
    """
    View a lesson explanation.
    """
    get_path = get_lesson_url
    # node specification data goes here
    title = 'View an explanation'
    edges = (
        dict(name='next', toNode='END', title='View Next Lesson'),
    )


class ASK(object):
    get_path = get_lesson_url
    # node specification data goes here
    title = 'View an explanation'
    edges = (
        dict(name='next', toNode='GET_ANSWER', title='Answer a question'),
    )


class GET_ANSWER(object):
    get_path = get_lesson_url
    # node specification data goes here
    title = 'It is time to answer'
    edges = (
        dict(name='next', toNode='ASSESS', title='Go to self-assessment'),
    )


class ASSESS(object):
    get_path = get_lesson_url
    # node specification data goes here
    title = 'Assess your answer'
    edges = (
        dict(name='next', toNode='GET_ASSESS', title='Assess yourself'),
    )


class GET_ASSESS(object):
    get_path = get_lesson_url
    next_edge = check_selfassess_and_next_lesson
    # node specification data goes here
    title = 'Assess your answer'
    edges = (
        dict(name='next', toNode='END', title='View Next Lesson'),
    )


class ERRORS(object):
    get_path = get_lesson_url
    # node specification data goes here
    title = 'Error options'
    edges = (
        dict(name='next', toNode='GET_ERRORS', title='Choose errors'),
    )


class GET_ERRORS(object):
    get_path = get_lesson_url
    # node specification data goes here
    title = 'Classify your error(s)'
    edges = (
        dict(name='next', toNode='END', title='View Next Lesson'),
    )


class END(object):
    # node specification data goes here
    title = 'Courselet resource lessons completed'
    help = '''Congratulations!  You have completed one of the resources,
    now you can try some more resources from the sidebar.'''


def get_specs():
    """
    Get FSM specifications stored in this file.
    """
    from fsm.fsmspec import FSMSpecification
    spec = FSMSpecification(
        name='resource',
        hideTabs=True,
        title='Take the courselet core lessons',
        pluginNodes=[START, LESSON, ASK, GET_ANSWER,
                     ASSESS, GET_ASSESS, ERRORS,
                     GET_ERRORS, END],
    )
    return (spec,)
