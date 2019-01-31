from ct.models import UnitStatus, NEED_HELP_STATUS, NEED_REVIEW_STATUS, DONE_STATUS, StudentError

from ..models import Message


def help_egde_decision(self, edge, fsmStack, request, useCurrent=False, **kwargs):
    fsm = edge.fromNode.fsm
    additionals = Message.objects.filter(is_additional=True,
                                         chat=fsmStack,
                                         timestamp__isnull=True)
    if not additionals:
        return fsm.get_node('END')
    
    return edge.toNode


def next_additional_lesson(self, edge, fsmStack, request, useCurrent=False, **kwargs):
    """
    Edge method that moves us to right state for next lesson (or END).
    """
    fsm = edge.fromNode.fsm
    _status = fsmStack.next_point.student_error.status
    if _status == NEED_HELP_STATUS:
        additionals = Message.objects.filter(is_additional=True,
                                             chat=fsmStack,
                                             timestamp__isnull=True)
    elif _status in [NEED_REVIEW_STATUS, DONE_STATUS]:
        Message.objects.filter(student_error=fsmStack.next_point.student_error,
                               is_additional=True,
                               chat=fsmStack,
                               timestamp__isnull=True).delete()
        additionals = Message.objects.filter(is_additional=True,
                                             chat=fsmStack,
                                             timestamp__isnull=True)
    if additionals:
        next_message = additionals.order_by('student_error').first()
        fsmStack.state.unitLesson = next_message.content
        if next_message.student_error != fsmStack.next_point.student_error:
            return fsm.get_node('NEED_HELP_MESSAGE') if _status == NEED_HELP_STATUS else fsm.get_node('STUDENTERROR')
    else:
        return fsm.get_node('NEED_HELP_MESSAGE') if _status == NEED_HELP_STATUS else fsm.get_node('END')
    return edge.toNode


def check_selfassess_and_next_lesson(self, edge, fsmStack, request, useCurrent=False, **kwargs):
    fsm = edge.fromNode.fsm

    if not fsmStack.next_point.content.selfeval == 'correct':
        return fsm.get_node('ERRORS')

    return next_additional_lesson(self, edge, fsmStack, request, useCurrent=False, **kwargs)


def get_lesson_url(self, node, state, request, **kwargs):
    """
    Get URL for any lesson.
    """
    course = state.get_data_attr('course')
    unitStatus = state.get_data_attr('unitStatus')
    ul = unitStatus.get_lesson()
    return ul.get_study_url(course.pk)


class NEED_HELP_MESSAGE(object):
    get_path = get_lesson_url
    next_edge = help_egde_decision

    title = 'Additional message'
    edges = (
        dict(name='next', toNode='STUDENTERROR', title='Go to self-assessment'),
    )
    help = 'We will try to provide more explanation for this.'


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

    # node specification data goes here
    title = 'Start This Courselet'
    edges = (
            dict(name='next', toNode='STUDENTERROR', title='View Next Lesson'),
        )


class START_MESSAGE(object):
    get_path = get_lesson_url
    # node specification data goes here
    title = 'Let\'s address each blindspot'
    edges = (
        dict(name='next', toNode='STUDENTERROR', title='View Next Lesson'),
    )


class STUDENTERROR(object):
    get_path = get_lesson_url
    # node specification data goes here
    title = 'Additional lessons begin'
    edges = (
        dict(name='next', toNode='RESOLVE', title='View Next Lesson'),
    )


class RESOLVE(object):
    get_path = get_lesson_url
    # node specification data goes here
    title = 'It is time to answer'
    edges = (
            dict(name='next', toNode='MESSAGE_NODE', title='Go to self-assessment'),
        )


class MESSAGE_NODE(object):
    get_path = get_lesson_url
    # node specification data goes here
    title = 'How well do you feel you understand this blindspot now? If you need more clarifications, tell us.'
    edges = (
        dict(name='next', toNode='GET_RESOLVE', title='Go to self-assessment'),
    )


class GET_RESOLVE(object):
    get_path = get_lesson_url
    next_edge = next_additional_lesson

    # node specification data goes here
    title = 'It is time to answer'
    edges = (
            dict(name='next', toNode='RESOLVE', title='Go to self-assessment'),
        )


class END(object):
    def get_path(self, node, state, request, **kwargs):
        """
        Get URL for next steps in this unit.
        """
        unitStatus = state.get_data_attr('unitStatus')
        return unitStatus.unit.get_study_url(request.path)
    # node specification data goes here
    title = 'Additional lessons completed'
    help = '''OK, let's continue.'''


def get_specs():
    """
    Get FSM specifications stored in this file.
    """
    from fsm.fsmspec import FSMSpecification
    spec = FSMSpecification(
        name='additional',
        hideTabs=True,
        title='Take the courselet core lessons',
        pluginNodes=[START, START_MESSAGE, STUDENTERROR, RESOLVE, MESSAGE_NODE, NEED_HELP_MESSAGE, GET_RESOLVE, END],
    )
    return (spec,)
