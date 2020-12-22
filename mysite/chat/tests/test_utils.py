import pytest
import random
from itertools import permutations, combinations_with_replacement
from dateutil import tz

from django.utils import timezone

from chat.utils import update_activity, c_chat_context, is_end_update_node, status_min, Status


@pytest.mark.integration
def test_update_activity(mocker):
    chat_id = random.randint(9999, 999999)
    actual_unit_lesson_id = random.randint(9999, 999999)
    unit_lesson_id = random.randint(9999, 999999)
    current_time = timezone.now()

    c_chat_context().update_one(
        {"chat_id": chat_id},
        {"$set": {
            "actual_ul_id": actual_unit_lesson_id,
            "thread_id": unit_lesson_id,
            f"activity.{unit_lesson_id}": current_time,
            "need_faqs": False
        }},
        upsert=True
    )

    update_activity(chat_id)

    context = c_chat_context().find_one({"chat_id": chat_id})
    updated_activity_time = context.get('activity').get(f'{unit_lesson_id}').replace(tzinfo=tz.tzutc())
    actual_ul_id = context.get('actual_ul_id')

    assert updated_activity_time != current_time
    assert actual_ul_id == actual_unit_lesson_id


@pytest.mark.unittest
@pytest.mark.parametrize(
    'node_name_is_one_of, fsm_name_is_one_of, result',
    [[x, y, x & y] for x, y in
        set(list(permutations([True, False], 2)) + list(combinations_with_replacement([True, False], 2)))]
)
def test_is_end_update_node(mocker, node_name_is_one_of, fsm_name_is_one_of, result):
    state = mocker.Mock()
    node = mocker.Mock()
    state.fsmNode = node

    node.node_name_is_one_of = mocker.Mock(return_value=node_name_is_one_of)
    node.fsm.fsm_name_is_one_of = mocker.Mock(return_value=fsm_name_is_one_of)

    assert is_end_update_node(state) is result


@pytest.mark.unittest
@pytest.mark.parametrize(
    "status1, status2, result",
    [
        ["help",   "review", Status(name="help")],
        ["help",   "done",   Status(name="help")],
        ["review", "done",   Status(name="review")],
        ["done",   "review", Status(name="review")],
        ["done",   "help",   Status(name="help")],
        ["review", "help",   Status(name="help")],
        ["help",   "help",   Status(name="help")],
        ["review", "review", Status(name="review")],
        ["done",   "done",   Status(name="done")],
    ]
)
def test_status_min(status1, status2, result):
    assert status_min(status1, status2) == result
