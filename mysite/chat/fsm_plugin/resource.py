from ct.models import UnitStatus

from core.common.mongo import c_chat_context
from chat.models import Message


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
        chat = kwargs.get('chat')

        self._update_thread_id(chat, fsmStack.state.unitLesson.id);

        return fsmStack.state.transition(
            fsmStack, request, 'next', useCurrent=True, **kwargs
        )

    def _update_thread_id(self, chat, thread_id):
        c_chat_context().update_one(
            {"chat_id": chat.id},
            {"$set": {
                "thread_id": thread_id,
            }},
            upsert=True
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
    help = """Congratulations!  You have completed one of the resources,
              now you can try some more resources from the sidebar."""
    ultimate_help = """Good job! You have completed everything in this courselet.
                       You can always come back to review your history or start over to answer the questions again."""

    def get_help(self, node, state, request, *args, **kwargs):
        """
        Provide help messages for all views relevant to this stage.
        """
        chat = kwargs.get('chat')
        if chat and chat.resources_is_done(client=chat.state.unitLesson):
            return self.ultimate_help
        else:
            return self.help

    def get_message(self, chat, next_lesson, is_additional, *args, **kwargs) -> Message:
        _data = {
            'chat': chat,
            'owner': chat.user,
            'thread_id': chat.state.unitLesson.id,
            'text': self.get_help(kwargs.get('node'), chat.state, request=None, chat=chat),
            'input_type': 'custom',
            'kind': 'message',
            'sub_kind': 'transition',
            'is_additional': is_additional
        }
        message = Message(**_data)
        message.save()
        return message


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
