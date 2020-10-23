import json
from io import BytesIO
import random
from collections import namedtuple

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.files.uploadedfile import InMemoryUploadedFile

from chat.models import Chat, Message, UnitError, EnrollUnitCode
from ct.models import Lesson, Concept, Course, Unit, UnitLesson, CourseUnit, Response
from fsm.fsm_base import FSMStack
from fsm.models import FSM
from mysite.helpers import base64_to_file
from api.v0.service import LessonProvider
from api.v0.lesson_providers.multichoice import MultiChoiceProviderBuilder
from api.v0.lesson_providers.intro import IntroProviderBuilder
from api.v0.lesson_providers.question import QuestionProviderBuilder
from api.v0.lesson_providers.cfg import Provider


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


@pytest.fixture(scope="function")
def image_file():
    thumb_io = BytesIO()
    thumb_file = InMemoryUploadedFile(thumb_io, None, 'img.png', 'image/jpeg', thumb_io.getbuffer().nbytes, None)
    return thumb_file


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
def lesson_question_parametrized(request, user, concept, image_file):
    instance = Lesson(
        title='ugh', text='brr', addedBy=user,
        kind=Lesson.ORCT_QUESTION, sub_kind=request.param,
        concept=concept, attachment=image_file
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


@pytest.fixture(scope='function')
def updates():
    """
    Baseline for Thread updates.
    """
    UPDATES_DATA = {
        'em_resolutions': [
            {
                "em_id": 1,
                "em_title": "EM title 1",
                "em_text": "EM text 1",
                "resolutions": [
                    {'id': 1, 'title': 'Resolution 1', "text": "Resolution text 1"},
                    {'id': 2, 'title': 'Resolution 2', "text": "Resolution text 2"},
                ]
            },
            {
                "em_id": 2,
                "em_title": "EM title 2",
                "em_text": "EM text 2",
                "resolutions": [
                    {'id': 3, 'title': 'Resolution 3', "text": "Resolution text 3"},
                    {'id': 4, 'title': 'Resolution 4', "text": "Resolution text 4"},
                ]
            },
        ],
        'faq_answers': [
            {
                "faq_id": 1,
                "faq_title": "FAQ title 1",
                "faq_text": "FAQ text 1",
                "answers": [
                    {"id": 1, "title": "Title 1", "text": "Answer text 1"},
                    {"id": 2, "title": "Title 2", "text": "Answer text 2"},
                ]
            },
            {
                "faq_id": 2,
                "faq_title": "FAQ title 2",
                "faq_text": "FAQ text 2",
                "answers": [
                    {"id": 3, "title": "Title 3", "text": "Answer text 3"},
                    {"id": 4, "title": "Title 4", "text": "Answer text 4"},
                ]
            }
        ],
        'new_ems': [
            {
                "em_id": 1,
                "em_title": "EM title 1",
            },
            {
                "em_id": 2,
                "em_title": "EM title 2",
            }
        ],
        'new_faqs': [
            {
                "faq_id": 1,
                "faq_title": "FAQ title 1",
                "faq_text": "FAQ text 1",
            },
            {
                "faq_id": 2,
                "faq_title": "FAQ title 2",
                "faq_text": "FAQ text 2",
            }
        ]
    }
    return UPDATES_DATA


@pytest.fixture(scope="function")
def intro_data():
    """
    Fixture for the Threads API.
    """
    return {
        "title": "Ukraine population.",
        "message": "Ukraine has a population of about 42 million.",
        "kind": "intro",
        "author": "Ilona"
    }


@pytest.fixture(scope="function")
def orct_data():
    """
    Fixture for the Threads API.
    """
    return {
        "title": "ORCT Ukraine population.",
        "question": "What population of Ukraine?",
        "answer": "Ukraine has a population of about 42 million.",
        "kind": "question",
        "author": "Ilona"
    }


@pytest.fixture(scope="function")
def multichoice_data():
    """
    Fixture for the Threads API to gen multichoice post data.
    """
    return {
        "title": "Brick weight.",
        "question": "Which set of bricks is less heavier?",
        "choices": [
            {
                "text": "Blue",
                "correct": False
            },
            {
                "text": "Red",
                "correct": False
            },
            {
                "text": "Green",
                "correct": True
            },
            {
                "text": "Yellow",
                "correct": False
            }
        ],
        "answer": "Green\n. The green set of bricks is the least heavy because it contains the least number of circles.",
        "kind": "multichoice"
    }


@pytest.fixture(scope='function')
def lesson_factory():
    """
    Unregister providers for test purposes.
    """
    factory = LessonProvider()
    factory.register_builder(Provider.MULTICHOICE, MultiChoiceProviderBuilder())
    factory.register_builder(Provider.INTRO, IntroProviderBuilder())
    factory.register_builder(Provider.QUESTION, QuestionProviderBuilder())

    yield factory

    factory.unregister_builder(Provider.MULTICHOICE)
    factory.unregister_builder(Provider.INTRO)
    factory.unregister_builder(Provider.QUESTION)
