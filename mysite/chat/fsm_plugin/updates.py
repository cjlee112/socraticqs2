from django.utils import timezone

from core.common.mongo import c_chat_context
from ct.models import UnitStatus, UnitLesson
from chat.models import Message


def next_lesson_after_title(self, edge, fsmStack, request, useCurrent=False, **kwargs):
    """
    Edge method that moves us to right state for next lesson (or END).
    """
    unitStatus = fsmStack.state.get_data_attr('unitStatus')
    nextUL = unitStatus.get_lesson()
    # Update chat context
    # Don't ask
    chat = fsmStack
    c_chat_context().update_one(
        {"chat_id": chat.id},
        {"$set": {
            "thread_id": nextUL.id,
            f"activity.{nextUL.id}": timezone.now(),
            "need_faqs": False
        }},
        upsert=True
    )
    return edge.toNode


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
    # node specification data goes here
    title = 'Start This Courselet'
    edges = (
        dict(name='next', toNode='UPDATES', title='View Next Lesson'),
    )


def get_lesson_url(self, node, state, request, **kwargs):
    """
    Get URL for any lesson.
    """
    course = state.get_data_attr('course')
    unitStatus = state.get_data_attr('unitStatus')
    ul = unitStatus.get_lesson()
    return ul.get_study_url(course.pk)


class UPDATES(object):
    """
    View a lesson updates.
    """
    next_edge = next_lesson_after_title
    get_path = get_lesson_url

    def get_message(self, chat, next_lesson, is_additional, *args, **kwargs):
        _data = {
            'chat': chat,
            'text': 'Imagine updates for this thread here :)',
            'owner': chat.user,
            'input_type': 'custom',  # SUBKIND_TO_INPUT_TYPE_MAP.get(sub_kind, 'custom'),
            'kind': 'message',  # SUB_KIND_TO_KIND_MAP.get(sub_kind, next_lesson.lesson.kind),
            'is_additional': is_additional
        }
        message = Message(**_data)
        message.save()
        return message

    title = 'View updates'
    edges = (
        dict(name='next', toNode='ACT', title='Ask for acknowlegement'),
    )


class ACT(object):
    """
    Get acknowledgement.
    """
    def get_message(self, chat, next_lesson, is_additional, *args, **kwargs):
        _data = {
            'chat': chat,
            'text': 'Have you changed your mind?',
            'owner': chat.user,
            'input_type': 'custom',
            'kind': 'message',
            'is_additional': is_additional
        }
        message = Message(**_data)
        message.save()
        return message

    title = 'Check acknowlegement'
    edges = (
        dict(name='next', toNode='GET_ACT', title='Get an acknowlegement'),
    )


class GET_ACT(object):
    """
    Get acknowledgement.
    """
    def get_message(self, chat, next_lesson, is_additional, *args, **kwargs):
        _data = {
            'chat': chat,
            'text': 'Change me: change',
            'owner': chat.user,
            'input_type': 'custom',
            'kind': 'message',
            'is_additional': is_additional
        }
        message = Message(**_data)
        message.save()
        return message

    title = 'Check acknowlegement'
    edges = (
        dict(name='next', toNode='END', title='Move to the end'),
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

    def get_message(self, chat, next_lesson, is_additional, *args, **kwargs):
        _data = {
            'chat': chat,
            'text': 'Some smart last message.',
            'owner': chat.user,
            'input_type': 'custom',  # SUBKIND_TO_INPUT_TYPE_MAP.get(sub_kind, 'custom'),
            'kind': 'message',  # SUB_KIND_TO_KIND_MAP.get(sub_kind, next_lesson.lesson.kind),
            'is_additional': is_additional
        }
        message = Message(**_data)
        message.save()
        return message

    title = 'Courselet core lessons completed'


def get_specs():
    """
    Get FSM specifications stored in this file.
    """
    from fsm.fsmspec import FSMSpecification
    spec = FSMSpecification(
        name='updates',
        hideTabs=True,
        title='Present updates for a particular Thread.',
        pluginNodes=[
            START,
            UPDATES,
            ACT,
            GET_ACT,
            END
        ],

    )
    return (spec,)
