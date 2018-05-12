import pytest
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from chat.models import Chat, ChatDivider, Message
from ct.models import Lesson, Concept, Course, Unit, UnitLesson


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
    return User.objects.create_user(username='test', password='test')


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
def lesson_question(user, concept):
    instance = Lesson(
        title='ugh', text='brr', addedBy=user, kind=Lesson.ORCT_QUESTION, concept=concept
    )
    instance.save_root(concept)
    return instance


@pytest.fixture
def lesson_question_canvas(user, concept):
    instance = Lesson(
        title='ugh', text='brr', addedBy=user,
        kind=Lesson.ORCT_QUESTION, sub_kind=Lesson.CANVAS,
        concept=concept,
    )
    instance.save_root(concept)
    return instance


@pytest.fixture
def unit_lesson(user, unit, lesson_question):
    return UnitLesson.objects.create(
        unit=unit, lesson=lesson_question, addedBy=user, treeID=lesson_question.id
    )


@pytest.fixture
def unit_lesson_canvas(user, unit, lesson_question_canvas):
    return UnitLesson.objects.create(
        unit=unit, lesson=lesson_question_canvas, addedBy=user, treeID=lesson_question_canvas.id,
    )


@pytest.fixture
def lesson_answer(unit, lesson_question):
    return UnitLesson.create_from_lesson(unit=unit, lesson=lesson_question, addAnswer=True)


@pytest.fixture
def lesson_answer_canvas(unit, lesson_question_canvas):
    return UnitLesson.create_from_lesson(unit=unit, lesson=lesson_question_canvas, addAnswer=True)


@pytest.fixture
def chat(user):
    return Chat.objects.create(user=user)


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
