import json
import os
import random
from collections import namedtuple
from tempfile import NamedTemporaryFile

import pytest
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.files import File

from chat.models import Chat, Message, UnitError, EnrollUnitCode
from ct.models import Lesson, Concept, Course, Unit, UnitLesson, CourseUnit, Response
from fsm.fsm_base import FSMStack
from fsm.models import FSM
from mysite.helpers import base64_to_file


def pytest_addoption(parser):
    parser.addoption('--run-slow', action='store_true',
                     default=False,
                     help="Run slow tests")


def pytest_runtest_setup(item):
    if ('slowtest' in item.keywords and
            (not item.config.getoption('--run-slow'))):
        pytest.skip('Need --run-slow to run')


@pytest.fixture
def base64_gif_image():
    return 'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'


@pytest.fixture
def user():
    return User.objects.create_user(username='admin', password='test_admin')


@pytest.fixture
def fsm(user):
    call_command('fsm_deploy')
    return FSM.objects.get(
        name='chat',
        addedBy=user,
    )


@pytest.fixture
def fsm_state(user, fsm, course, unit, unit_lesson_canvas):
    request_data = {'session': {}, 'user': user}
    request = namedtuple('Request', list(request_data.keys()))(*list(request_data.values()))
    stateData = {
        'course': course,
        'unit': unit,
    }
    stack = FSMStack(request)
    stack.push(request, fsm.name, stateData, unitLesson=unit_lesson_canvas)
    return stack.state


@pytest.fixture
def concept(user):
    return Concept.objects.create(title='test title', addedBy=user)


@pytest.fixture
def course(user):
    return Course.objects.create(title='test title', addedBy=user)


@pytest.fixture
def unit(user):
    return Unit.objects.create(title='test unit title', addedBy=user)


@pytest.fixture
def course_unit(course, unit, user):
    return CourseUnit.objects.create(course=course, unit=unit, addedBy=user, order=0)


@pytest.fixture
def lesson_question(user, concept):
    instance = Lesson(
        title='ugh', text='brr', addedBy=user, kind=Lesson.ORCT_QUESTION, concept=concept
    )
    instance.save_root(concept)
    return instance


@pytest.fixture(scope='function')
def temp_image():
    media_dir = settings.MEDIA_ROOT
    if not os.path.exists(media_dir):
        os.makedirs(media_dir)
    temp = NamedTemporaryFile(suffix='.jpeg', dir=media_dir)
    temp.write(bytes(base64_gif_image(), 'utf-8'))
    yield File(temp)


@pytest.fixture
def lesson_question_canvas(user, concept, base64_gif_image):
    instance = Lesson(
        title='ugh', text='brr', addedBy=user,
        kind=Lesson.ORCT_QUESTION, sub_kind=Lesson.CANVAS,
        concept=concept, attachment=base64_to_file('data:image/gif;base64,{}'.format(base64_gif_image)),
    )
    instance.save_root(concept)
    return instance


@pytest.fixture(params=[Lesson.MULTIPLE_CHOICES, Lesson.NUMBERS, Lesson.EQUATION])
def lesson_question_parametrized(request, user, concept, temp_image):
    instance = Lesson(
        title='ugh', text='brr', addedBy=user,
        kind=Lesson.ORCT_QUESTION, sub_kind=request.param,
        concept=concept, attachment=temp_image
    )
    instance.save_root(concept)
    return instance


@pytest.fixture
def unit_lesson(user, unit, lesson_question):
    return UnitLesson.objects.create(
        unit=unit, lesson=lesson_question, addedBy=user, treeID=lesson_question.id, order=1
    )


@pytest.fixture
def unit_lesson_canvas(user, unit, lesson_question_canvas):
    return UnitLesson.objects.create(
        unit=unit, lesson=lesson_question_canvas, addedBy=user,
        treeID=lesson_question_canvas.id, order=0,
    )


@pytest.fixture
def unit_lesson_parametrized(user, unit, lesson_question_parametrized):
    return UnitLesson.objects.create(
        unit=unit, lesson=lesson_question_parametrized, addedBy=user,
        treeID=lesson_question_parametrized.id, order=0,
    )


@pytest.fixture
def lesson_answer(unit, lesson_question):
    return UnitLesson.create_from_lesson(unit=unit, lesson=lesson_question, addAnswer=True, order=1)


@pytest.fixture
def lesson_answer_canvas(unit, lesson_question_canvas):
    return UnitLesson.create_from_lesson(unit=unit, lesson=lesson_question_canvas, addAnswer=True)


@pytest.fixture
def enroll_unit_code(course_unit, user):
    enroll = EnrollUnitCode.get_code_for_user_chat(
        course_unit=course_unit,
        is_live=False,
        user=user,
    )
    return enroll


@pytest.fixture
def chat(enroll_unit_code, user):
    return Chat.objects.create(
        enroll_code=enroll_unit_code,
        user=user,
    )


@pytest.fixture
def response(lesson_question, unit_lesson, course, user):
    return Response.objects.create(
        lesson=lesson_question,
        unitLesson=unit_lesson,
        course=course,
        text='test response',
        author=user,
    )


@pytest.fixture
def unit_error(unit, response):
    return UnitError.objects.create(
        unit=unit,
        response=response,
    )


@pytest.fixture
def message(chat, user, unit_lesson):
    return Message.objects.create(
        chat=chat,
        contenttype='unitlesson',
        content_id=unit_lesson.id,
        owner=user,
        type='message',
        lesson_to_answer=unit_lesson,
    )


@pytest.fixture
def message_canvas(chat, user, unit_lesson_canvas):
    return Message.objects.create(
        chat=chat,
        contenttype='unitlesson',
        content_id=unit_lesson_canvas.id,
        owner=user,
        type='message',
        lesson_to_answer=unit_lesson_canvas,
    )


@pytest.fixture
def message_parametrized(chat, user, unit_lesson_parametrized):
    return Message.objects.create(
        chat=chat,
        contenttype='unitlesson',
        content_id=unit_lesson_parametrized.id,
        owner=user,
        type='message',
        lesson_to_answer=unit_lesson_parametrized,
    )


@pytest.fixture(scope='function')
def unique_instructor():
    # Create User and hope there is no user with such id
    # This is hack for mongo onboarding issue
    instructor = User(username='test_instructor', id=random.randint(9999, 999999))
    instructor.save()
    yield instructor
    instructor.delete()


def load_from_json(file_dir):
    with open(file_dir) as res_file:
        input_data = json.load(res_file)
    return input_data


@pytest.fixture(params=load_from_json('api/v0/bp_calculation_data.json'), ids=lambda param: str(param.get("data")))
def input_data(request):
    return request.param
