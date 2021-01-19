from ct.models import UnitStatus, NEED_HELP_STATUS, NEED_REVIEW_STATUS, DONE_STATUS, Lesson, UnitLesson
from core.common.mongo import c_chat_context
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
    additionals = None

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
        if fsmStack.state.unitLesson.lesson.kind in ('orct', 'choices'):
            return fsm.get_node('ORCT_LETS_START_MESSAGE')
    else:
        return fsm.get_node('NEED_HELP_MESSAGE') if _status == NEED_HELP_STATUS else fsm.get_node('END')
    return edge.toNode


def check_selfassess_and_next_lesson(self, edge, fsmStack, request, useCurrent=False, **kwargs):
    fsm = edge.fromNode.fsm

    if fsmStack.state.unitLesson.lesson.enable_auto_grading and not fsmStack.state.fsmNode.name == 'ADDITIONAL_GRADING':
        return fsm.get_node('ADDITIONAL_GRADING')

    if not fsmStack.next_point.content.selfeval == 'correct':
        return fsm.get_node('HOPENESS_MESSAGE')
    else:
        return fsm.get_node('GREAT_MESSAGE')


def get_lesson_url(self, node, state, request, **kwargs):
    """
    Get URL for any lesson.
    """
    course = state.get_data_attr('course')
    unitStatus = state.get_data_attr('unitStatus')
    ul = unitStatus.get_lesson()
    return ul.get_study_url(course.pk)


class ADDITIONAL_GRADING(object):
    get_path = get_lesson_url
    next_edge = check_selfassess_and_next_lesson
    # node specification data goes here
    title = 'Grading for student answer'
    edges = (
        dict(name='next', toNode='HOPENESS_MESSAGE', title='View Next Lesson'),
    )


class ADDITIONAL_CORRECT_ANSWER(object):

    title = 'Show correct answer for Multiple Choices'
    edges = (
        dict(name='next', toNode='GREAT_MESSAGE', title='Assess yourself'),
    )


class ADDITIONAL_INCORRECT_ANSWER(object):
    title = 'Show correct answer for Multiple Choices'
    edges = (
        dict(name='next', toNode='ADDITIONAL_INCORRECT_CHOICE', title='Assess yourself'),
    )


class ADDITIONAL_INCORRECT_CHOICE(object):
    title = 'Show incorrect choice for Multiple Choices'
    edges = (
        dict(name='next', toNode='HOPENESS_MESSAGE', title='Assess yourself'),
    )


class IF_RESOURCES(object):
    help = '''Congratulations! You have completed the core lessons for this
              courselet.'''

    title = 'Courselet core lessons completed'
    edges = (
        dict(name='next', toNode='END', title='View Next Lesson'),
    )


class ORCT_LETS_START_MESSAGE(object):
    title = 'Just show message to user'
    edges = (
        dict(name="next", toNode="ADDITIONAL_ASK", title="title"),
    )
    help = "Let's try another question that could help you with this."


class GREAT_MESSAGE(object):
    title = 'Greate Message'
    help = 'Great! It looks like you understand this now.'
    edges = (
        dict(name='next', toNode='HOPENESS_MESSAGE', title='something'),
    )


class HOPENESS_MESSAGE(object):
    title = 'We all hope you are ok))'
    help = 'I hope this helped you'
    edges = (
        dict(name='next', toNode='MESSAGE_NODE', title='does not metter'),
    )
    # next_edge = next_additional_lesson


class ADDITIONAL_ASK(object):
    get_path = get_lesson_url
    # node specification data goes here
    title = 'View an explanation'
    edges = (
        dict(name='next', toNode='ADDITIONAL_GET_ANSWER', title='Answer a question'),
    )


class ADDITIONAL_GET_ANSWER(object):
    title = 'ADDITIONAL_GET_ANSWER'
    edges = (
        dict(
            name='next',
            toNode='CONFIDENCE',
            title='Answer a question'
        )
    )

    def next_edge(self, edge, fsmStack, request, useCurrent=False, **kwargs):
        fsm = edge.fromNode.fsm

        unitStatus = fsmStack.state.get_data_attr('unitStatus')
        unit_lesson = unitStatus.get_lesson()
        if unit_lesson.sub_kind == Lesson.MULTIPLE_CHOICES and unit_lesson.lesson.mc_simplified:
            nextUL = unitStatus.start_next_lesson()
            if not nextUL:  # pragma: no cover
                unit = fsmStack.state.get_data_attr('unit')
                if unit.unitlesson_set.filter(
                    kind=UnitLesson.COMPONENT, order__isnull=True
                ).exists():
                    return fsm.get_node('IF_RESOURCES')
                else:
                    return fsm.get_node('END')
            else:  # just a lesson to read
                fsmStack.state.unitLesson = nextUL
                return fsm.get_node('TITLE')
        else:
            return edge.toNode

    title = 'It is time to answer'
    edges = (
        dict(name='next', toNode='ADDITIONAL_CONFIDENCE', title='Go to confidence'),
    )


class ADDITIONAL_CONFIDENCE(object):
    title = 'How confident are you?'
    edges = (
        dict(name='next', toNode='ADDITIONAL_GET_CONFIDENCE', title='Go to choosing your confidence'),
    )


class ADDITIONAL_GET_CONFIDENCE(object):
    def next_edge(self, edge, fsmStack, request, useCurrent=False, **kwargs):
        fsm = edge.fromNode.fsm

        if not fsmStack.next_point.content.selfeval:
            return edge.toNode

        if fsmStack.next_point.content.selfeval != 'correct':
            return fsm.get_node('ADDITIONAL_INCORRECT_ANSWER')
        elif fsmStack.next_point.content.selfeval == 'correct':
            return fsm.get_node('ADDITIONAL_CORRECT_ANSWER')
        else:
            return edge.toNode

        return edge.toNode

    title = 'Choose confidence'
    edges = (
        dict(name='next', toNode='ADDITIONAL_ASSESS', title='Go to self-assessment'),
    )


class ADDITIONAL_ASSESS(object):
    get_path = get_lesson_url
    # node specification data goes here
    title = 'Assess your answer'
    edges = (
        dict(name='next', toNode='ADDITIONAL_ASSESS_QUESTION_MESSAGE', title='Assess yourself'),
    )


class ADDITIONAL_ASSESS_QUESTION_MESSAGE(object):
    get_path = get_lesson_url
    # node specification data goes here
    title = 'Assess your answer'
    edges = (
        dict(name='next', toNode='ADDITIONAL_GET_ASSESS', title='Assess yourself'),
    )
    help = 'How close was your answer to the one shown here?'


class ADDITIONAL_GET_ASSESS(object):
    get_path = get_lesson_url
    next_edge = check_selfassess_and_next_lesson
    # node specification data goes here
    title = 'Assess your answer'
    edges = (
        dict(name='next', toNode='START', title='View Next Lesson'),
    )


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

        c_chat_context().update_one(
            {"chat_id": kwargs.get('chat').id},
            {"$set": {"need_faqs": True, "need_status": False}})

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

    def next_edge(self, edge, fsmStack, request, useCurrent=False, **kwargs):
        fsm = edge.fromNode.fsm
        if fsmStack.state.unitLesson.lesson.kind == 'orct':
            return fsm.get_node('ADDITIONAL_GET_ANSWER')
        else:
            return edge.toNode


class MESSAGE_NODE(object):
    get_path = get_lesson_url
    # node specification data goes here
    title = 'We hope this explanation helped you. How well do you feel you understand this blindspot now? If you need more clarifications, tell us.'
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
        pluginNodes=[
            START,
            START_MESSAGE,
            STUDENTERROR,
            RESOLVE,
            MESSAGE_NODE,
            NEED_HELP_MESSAGE,
            ADDITIONAL_ASK,
            GET_RESOLVE,
            ADDITIONAL_GET_ANSWER,
            ADDITIONAL_CONFIDENCE,
            ADDITIONAL_GET_CONFIDENCE,
            ADDITIONAL_ASSESS,
            ADDITIONAL_ASSESS_QUESTION_MESSAGE,
            ADDITIONAL_GET_ASSESS,
            GREAT_MESSAGE,
            HOPENESS_MESSAGE,
            ADDITIONAL_CORRECT_ANSWER,
            ADDITIONAL_INCORRECT_ANSWER,
            ADDITIONAL_INCORRECT_CHOICE,
            ADDITIONAL_GRADING,
            ORCT_LETS_START_MESSAGE,
            END],
    )
    return (spec,)
