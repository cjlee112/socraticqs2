from django.utils import timezone

from ct.models import UnitStatus

from ..models import Message


def next_additional_lesson(self, edge, fsmStack, request, useCurrent=False, **kwargs):
    """
    Edge method that moves us to right state for next lesson (or END).
    """
    fsm = edge.fromNode.fsm
    additionals = Message.objects.filter(is_additional=True,
                                         chat=fsmStack,
                                         timestamp__isnull=True)

    if additionals:
        next_message = additionals.first()
        next_message.timestamp = timezone.now()
        next_message.save()
        fsmStack.state.unitLesson = next_message.content
    else:
        return fsm.get_node('END')
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

    # node specification data goes here
    title = 'Start This Courselet'
    edges = (
        dict(name='next', toNode='START_MESSAGE', title='View Next Lesson'),
    )


class START_MESSAGE(object):
    get_path = get_lesson_url
    # node specification data goes here
    title = 'Click continue to get additional materials'
    edges = (
        dict(name='next', toNode='HELP_RESOLVE', title='View Next Lesson'),
    )


class HELP_RESOLVE(object):
    get_path = get_lesson_url
    next_edge = next_additional_lesson
    # node specification data goes here
    title = 'It is time to answer'
    edges = (
            dict(name='next', toNode='HELP_RESOLVE', title='Go to self-assessment'),
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
    help = '''You've finished resolving previous Unit.'''


def get_specs():
    """
    Get FSM specifications stored in this file.
    """
    from fsm.fsmspec import FSMSpecification
    spec = FSMSpecification(
        name='help',
        hideTabs=True,
        title='Take the courselet core lessons',
        pluginNodes=[START, START_MESSAGE, HELP_RESOLVE, END],
    )
    return (spec,)
