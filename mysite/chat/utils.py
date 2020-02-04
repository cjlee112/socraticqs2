from uuid import uuid4

from django.utils import timezone

from core.common.mongo import c_chat_context
from ct.models import UnitLesson


def enroll_generator():
    """
    Generate a random key
    """
    return uuid4().hex


def update_activity(chat_id: int) -> None:
    """
    Update chat context for a currently active thread.
    """
    context = c_chat_context().find_one({"chat_id": chat_id})
    if context and context.get('thread_id'):
        thread_id = context.get('thread_id')
        c_chat_context().update_one(
            {"chat_id": chat_id},
            {"$set": {
                f"activity.{thread_id}": timezone.now()
            }},
        )


def is_last_main_transition_wo_updates(state):
    """
    Return True if there are no updates and it is a last Lesson.
    """
    node = state.fsmNode

    has_update = 'next_update' in state.load_json_data() and \
        state.get_data_attr('next_update') and \
        state.get_data_attr('next_update').get('thread_id')

    last_thread = node.node_name_is_one_of('TRANSITION') and \
        node.fsm.fsm_name_is_one_of('chat') and \
        not state.get_data_attr('unitStatus').get_next_lesson()

    return last_thread and not has_update


def is_update_transition_wo_updates_w_last_main(state, chat):
    """
    Return True if there are no updates and an update with last main Lesson.

    Return True if no parent at all - updates from history mode.
    """
    if not state.fsmNode.fsm.fsm_name_is_one_of('updates'):
        return False

    if not state.fsmNode.node_name_is_one_of('TRANSITION'):
        return False

    threads = chat.enroll_code.courseUnit.unit.unitlesson_set.filter(order__isnull=False).order_by('order')

    has_update = False
    for thread in threads:
        if thread.updates_count(chat) > 0:
            has_update = True
            break

    parent = state.parentState

    if not parent:
        return True

    while parent and not parent.fsmNode.fsm.fsm_name_is_one_of('chat'):
        parent = parent.parentState

    main_thread = parent.fsmNode.fsm.fsm_name_is_one_of('chat')
    last_thread = main_thread and not parent.get_data_attr('unitStatus').get_next_lesson()

    return (not main_thread and not has_update) or (last_thread and not has_update)


def has_updates(state):
    """
    Return True if state has updates.
    """
    has_update = 'next_update' in state.load_json_data() and \
        state.get_data_attr('next_update') and \
        state.get_data_attr('next_update').get('thread_id')

    return has_update


def is_last_thread(state):
    """
    Return True if current thread is last.
    """
    node = state.fsmNode

    last_thread = node.node_name_is_one_of('TRANSITION', 'VIEWUPDATES') and \
        node.fsm.fsm_name_is_one_of('chat') and \
        not state.get_data_attr('unitStatus').get_next_lesson()

    return last_thread
