from ct.models import UnitStatus


def next_lesson(self, edge, fsmStack, request, useCurrent=False, **kwargs):
    """
    Edge method that moves us to right state for next lesson (or END).
    """
    fsm = edge.fromNode.fsm
    unitStatus = fsmStack.state.get_data_attr('unitStatus')
    if useCurrent:
        nextUL = unitStatus.get_lesson()
    else:
        nextUL = unitStatus.start_next_lesson()
    if not nextUL:
        return fsm.get_node('END')
    elif nextUL.is_question():
        return fsm.get_node(name='ASK')
    else:  # just a lesson to read
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
        try: # use unitStatus if provided
            unitStatus = fsmStack.state.get_data_attr('unitStatus')
        except AttributeError: # create new, empty unitStatus
            unitStatus = UnitStatus(unit=unit, user=request.user)
            unitStatus.save()
            fsmStack.state.set_data_attr('unitStatus', unitStatus)
        return fsmStack.state.transition(fsmStack, request, 'next',
                                         useCurrent=True, **kwargs)
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
    next_edge = next_lesson
    # node specification data goes here
    title = 'View an explanation'
    edges = (
            dict(name='next', toNode='LESSON', title='View Next Lesson'),
        )


class ASK(object):
    get_path = get_lesson_url
    # node specification data goes here
    title = 'View an explanation'
    edges = (
            dict(name='next', toNode='ASSESS', title='Go to self-assessment'),
        )


class ASSESS(object):
    next_edge = next_lesson
    # node specification data goes here
    title = 'Assess your answer'
    edges = (
            dict(name='next', toNode='LESSON', title='View Next Lesson'),
            dict(name='error', toNode='ERRORS', title='Classify your error'),
        )


class ERRORS(object):
    next_edge = next_lesson
    # node specification data goes here
    title = 'Classify your error(s)'
    edges = (
            dict(name='next', toNode='LESSON', title='View Next Lesson'),
        )


class END(object):
    def get_path(self, node, state, request, **kwargs):
        """
        Get URL for next steps in this unit.
        """
        unitStatus = state.get_data_attr('unitStatus')
        return unitStatus.unit.get_study_url(request.path)
    # node specification data goes here
    title = 'Courselet core lessons completed'
    help = '''Congratulations!  You have completed the core lessons for this
    courselet.  See below for suggested next steps for what to study now in
    this courselet.'''


def get_specs():
    """
    Get FSM specifications stored in this file.
    """
    from fsm.fsmspec import FSMSpecification
    spec = FSMSpecification(
        name='lessonseq',
        hideTabs=True,
        title='Take the courselet core lessons',
        pluginNodes=[START, LESSON, ASK, ASSESS, ERRORS, END],
    )
    return (spec,)
