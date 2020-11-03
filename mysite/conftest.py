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


@pytest.fixture
def base64_encoded_image():
    return "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"


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
def intro_data_w_image(base64_encoded_image):
    """
    Fixture for the Threads API.
    """
    return {
        "title": "Ukraine population.",
        "message": "Ukraine has a population of about 42 million.",
        "image": base64_encoded_image,
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
        "author": "Ilona",
        "kind": "question",
    }


@pytest.fixture(scope="function")
def orct_data_w_image(base64_encoded_image):
    """
    Fixture for the Threads API.
    """
    return {
        "title": "ORCT Ukraine population.",
        "question": "What population of Ukraine?",
        "image": base64_encoded_image,
        "answer": "Ukraine has a population of about 42 million.",
        "author": "Ilona",
        "kind": "question",
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


@pytest.fixture(scope="function")
def comparisons_data():
    """
    Fixture for the Threads API to gen comparisons post data.
    """
    return {
        "title": "Largest number.",
        "question": "What would result in the largest number? Briefly explain your reasoning.",
        "comparisons": [
            {
                "text": "905 divided by 5"
            },
            {
                "text": "905 divided by 905"
            }
        ],
        "answer": "REWRITE: Dividing something by the smallest number will always give the biggest answer.",
        "kind": "question"
    }


@pytest.fixture(scope="function")
def comparisons_data_w_image(base64_encoded_image):
    """
    Fixture for the Threads API to gen comparisons post data.
    """
    return {
        "title": "Largest number.",
        "question": "What would result in the largest number? Briefly explain your reasoning.",
        "image": base64_encoded_image,
        "comparisons": [
            {
                "text": "905 divided by 5"
            },
            {
                "text": "905 divided by 905"
            }
        ],
        "answer": "REWRITE: Dividing something by the smallest number will always give the biggest answer.",
        "kind": "question"
    }


@pytest.fixture(scope="function")
def canvas_data(base64_encoded_image):
    """
    Fixture for the Threads API to gen canvas post data.
    """
    return {
        "title": "Canvas ORCT.",
        "kind": "canvas",
        "answer": "There are four squares.",
        "question": "How many squares are there? Draw your answer and briefly explain your reasoning.",
        "canvas": base64_encoded_image
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
