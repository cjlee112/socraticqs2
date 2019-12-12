import pytest
import random
from dateutil import tz

from django.utils import timezone

from chat.utils import update_activity, c_chat_context


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
