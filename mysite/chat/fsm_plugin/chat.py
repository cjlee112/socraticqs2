from ct.models import UnitStatus, UnitLesson


def next_lesson(self, edge, fsmStack, request, useCurrent=False, **kwargs):
    """
    Edge method that moves us to right state for next lesson (or END).
    """
    fsm = edge.fromNode.fsm
    unitStatus = fsmStack.state.get_data_attr('unitStatus')

    if useCurrent:
        nextUL = unitStatus.get_lesson()
        return edge.toNode
    else:
        nextUL = unitStatus.start_next_lesson()
    if not nextUL:
        unit = fsmStack.state.get_data_attr('unit')
        if unit.unitlesson_set.filter(
            kind=UnitLesson.COMPONENT, order__isnull=True
        ).exists():
            return fsm.get_node('IF_RESOURCES')
        else:
            return fsm.get_node('END')
    else:  # just a lesson to read
        fsmStack.state.unitLesson = nextUL

        return edge.toNode


def next_lesson_after_title(self, edge, fsmStack, request, useCurrent=False, **kwargs):
    """
    Edge method that moves us to right state for next lesson (or END).
    """
    fsm = edge.fromNode.fsm
    unitStatus = fsmStack.state.get_data_attr('unitStatus')
    nextUL = unitStatus.get_lesson()
    if nextUL.is_question():
        return fsm.get_node(name='ASK')
    else:  # just a lesson to read
        return edge.toNode


def check_selfassess_and_next_lesson(self, edge, fsmStack, request, useCurrent=False, **kwargs):
    fsm = edge.fromNode.fsm

    if not fsmStack.next_point.content.selfeval == 'correct':
        return fsm.get_node('ERRORS')

    return next_lesson(self, edge, fsmStack, request, useCurrent=False, **kwargs)


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
        fsmStack.state.unitLesson = unitStatus.get_lesson()
        return fsmStack.state.transition(
            fsmStack, request, 'next', useCurrent=True, **kwargs
        )

    next_edge = next_lesson
    # node specification data goes here
    title = 'Start This Courselet'
    edges = (
            dict(name='next', toNode='TITLE', title='View Next Lesson'),
        )


class TITLE(object):
    """
    View a lesson explanation.
    """
    next_edge = next_lesson_after_title
    get_path = get_lesson_url
    # node specification data goes here
    title = 'View an explanation'
    edges = (
        dict(name='next', toNode='LESSON', title='View Next Lesson'),
    )


class LESSON(object):
    """
    View a lesson explanation.
    """
    get_path = get_lesson_url
    next_edge = next_lesson
    # node specification data goes here
    title = 'View an explanation'
    edges = (
            dict(name='next', toNode='TITLE', title='View Next Lesson'),
        )


class ASK(object):
    get_path = get_lesson_url
    # node specification data goes here
    title = 'View an explanation'
    edges = (
            dict(name='next', toNode='GET_ANSWER', title='Answer a question'),
        )


class GET_ANSWER(object):
    title = 'It is time to answer'
    edges = (
            dict(name='next', toNode='CONFIDENCE', title='Go to confidence'),
        )


class CONFIDENCE(object):
    title = 'Select the level of your confidence?'
    edges = (
        dict(name='next', toNode='GET_CONFIDENCE', title='Go to choosing your confidence'),
    )


class GET_CONFIDENCE(object):
    title = 'Choose confidence'
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
            dict(name='next', toNode='TITLE', title='View Next Lesson'),
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
    next_edge = next_lesson
    # node specification data goes here
    title = 'Classify your error(s)'
    edges = (
            dict(name='next', toNode='TITLE', title='View Next Lesson'),
        )


class IF_RESOURCES(object):
    help = '''Congratulations! You have completed the core lessons for this
              courselet.'''

    title = 'Courselet core lessons completed'
    edges = (
        dict(name='next', toNode='END', title='View Next Lesson'),
    )


class END(object):
    # node specification data goes here
    def get_help(self, node, state, request):
        'provide help messages for all views relevant to this stage.'
        unit = state.get_data_attr('unit')
        lessons = list(
            unit.unitlesson_set.filter(
                kind=UnitLesson.COMPONENT, order__isnull=True
            )
        )
        if lessons:
            return '''Please look over the available resources in the side panel.'''
        else:
            return '''Congratulations! You have completed the core lessons for this
                      courselet.'''
    title = 'Courselet core lessons completed'


def get_specs():
    """
    Get FSM specifications stored in this file.
    """
    from fsm.fsmspec import FSMSpecification
    spec = FSMSpecification(
        name='chat',
        hideTabs=True,
        title='Take the courselet core lessons',
        pluginNodes=[
            START,
            TITLE,
            LESSON,
            ASK,
            GET_ANSWER,
            CONFIDENCE,
            GET_CONFIDENCE,
            ASSESS,
            GET_ASSESS,
            ERRORS,
            GET_ERRORS,
            IF_RESOURCES,
            END
        ],

    )
    return (spec,)
