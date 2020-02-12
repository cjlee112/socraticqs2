import datetime
import re

import pytest
from django.urls import reverse
from django.utils import timezone

from chat.models import EnrollUnitCode
from ct.models import CourseUnit


@pytest.mark.django_db
def test_message_canvas(message_canvas):
    html = message_canvas.get_html()
    assert re.search(r'<svg([^>]+)>[\s\S]*?</svg>', html) is not None
    assert '<img src="{}" alt=""/>'.format(message_canvas.content.lesson.attachment.url) not in html


@pytest.mark.django_db
def test_message_html(message_parametrized):
    assert message_parametrized.content.lesson.attachment is not None
    html = message_parametrized.get_html()
    assert '<img src="{}" alt=""/>'.format(message_parametrized.content.lesson.attachment.url) in html
    assert re.search(r'<svg([^>]+)>[\s\S]*?</svg>', html) is None


@pytest.mark.django_db
def test_enroll_code(enroll_unit_code, course_unit, course, unit, chat):
    # test hex len
    assert len(enroll_unit_code.enrollCode) == 32
    assert EnrollUnitCode.get_code(course_unit) == enroll_unit_code.enrollCode

    # course unit without EnrollUnitCode
    new_course_unit = CourseUnit.objects.create(course=course, unit=unit, order=0, addedBy=course_unit.addedBy)
    assert len(EnrollUnitCode.get_code(new_course_unit)) == 32

    # EnrollUnitCode with chat
    enroll_unit_code = EnrollUnitCode.get_code_for_user_chat(
        course_unit=chat.enroll_code.courseUnit,
        user=new_course_unit.addedBy,
        is_live=True,
    )
    assert len(enroll_unit_code.enrollCode) == 32

    # EnrollUnitCode without chat
    enroll_unit_code = EnrollUnitCode.get_code_for_user_chat(
        course_unit=course_unit,
        user=new_course_unit.addedBy,
        is_live=True,
    )
    assert len(enroll_unit_code.enrollCode) == 32


@pytest.mark.django_db
def test_chat(chat, message, course_unit, fsm_state):
    chat.next_point = message
    assert len(chat.get_options()) > 0

    # CourseUnit from chat
    assert chat.get_course_unit() == course_unit

    # CourseUnit from state
    chat.state = fsm_state
    assert chat.get_course_unit() == course_unit

    # without message update time
    message.timestamp = None
    message.save()
    assert chat.get_spent_time() == datetime.timedelta(0)

    # modify message update time
    message.timestamp = timezone.now()
    message.save()
    chat.timestamp = message.timestamp
    chat.save()
    assert chat.get_spent_time() == datetime.timedelta(0)

    # modify chat update time
    chat.last_modify_timestamp = timezone.now()
    assert chat.get_spent_time() > datetime.timedelta(0)

    assert re.match(r'\d:\d{2}:\d{2}', chat.get_formatted_time_spent()) is not None


@pytest.mark.django_db
def test_message(message, unit_lesson, chat):
    assert str(message) is not None

    assert message.content == unit_lesson

    content_type = message.contenttype
    message.contenttype = 'NoneType'
    assert message.content == message.text
    message.contenttype = content_type

    chat.next_point = message
    assert message.get_next_point() == message.id
    message.chat = None
    assert message.get_next_point() is None

    assert message.get_next_input_type() is None
    message.chat = chat
    assert message.get_next_input_type() == message.input_type
    message.chat.next_point = None
    assert message.get_next_input_type() == 'custom'

    message.chat.next_point = message
    assert message.get_next_url() == reverse('chat:messages-detail', args=(message.id,))

    state = message.chat.state
    message.chat.state = None
    assert message.should_ask_confidence() is False
    message.chat.state = state

    assert message.get_sidebar_html().strip() == unit_lesson.text


@pytest.mark.django_db
def test_unit_error(unit_error):
    assert len(unit_error.get_errors()) == 0
