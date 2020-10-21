import pytest
from django.contrib.auth.models import User

from ct.models import Lesson, UnitLesson
from ..creators import ThreadBuilder


@pytest.mark.django_db(transaction=True)
def test_intro(unit, intro_data):
    author = User.objects.create(username="Ilona")

    builder = ThreadBuilder(unit)
    thread = builder.build(intro_data)

    assert thread.id
    assert thread.order == 0
    assert thread.kind == UnitLesson.COMPONENT
    assert thread.addedBy == author == thread.lesson.addedBy
    assert thread.lesson.kind == Lesson.BASE_EXPLANATION
    assert thread.lesson.title == intro_data["title"]
    assert thread.lesson.text == intro_data["message"]


@pytest.mark.django_db(transaction=True)
def test_intro_no_existing_user(unit, intro_data):
    builder = ThreadBuilder(unit)
    thread = builder.build(intro_data)

    assert thread.id
    assert thread.order == 0
    assert thread.kind == UnitLesson.COMPONENT
    assert thread.addedBy == unit.addedBy == thread.lesson.addedBy
    assert thread.lesson.kind == Lesson.BASE_EXPLANATION
    assert thread.lesson.title == intro_data["title"]
    assert thread.lesson.text == intro_data["message"]


@pytest.mark.django_db(transaction=True)
def test_intro_no_author(unit, intro_data):
    del intro_data["author"]

    builder = ThreadBuilder(unit)
    thread = builder.build(intro_data)

    assert thread.id
    assert thread.order == 0
    assert thread.kind == UnitLesson.COMPONENT
    assert thread.addedBy == unit.addedBy == thread.lesson.addedBy
    assert thread.lesson.kind == Lesson.BASE_EXPLANATION
    assert thread.lesson.title == intro_data["title"]
    assert thread.lesson.text == intro_data["message"]


@pytest.mark.django_db(transaction=True)
def test_question(unit, orct_data):
    author = User.objects.create(username="Ilona")

    builder = ThreadBuilder(unit)
    thread = builder.build(orct_data)

    assert thread.id
    assert thread.order == 0
    assert thread.kind == UnitLesson.COMPONENT
    assert thread.lesson.kind == Lesson.ORCT_QUESTION
    assert thread.lesson.title == orct_data["title"]
    assert thread.lesson.text == orct_data["question"]
    _answer = thread.get_answers().first().lesson
    assert _answer.title == "Answer"
    assert _answer.text == orct_data["answer"]

    assert thread.addedBy == author == thread.lesson.addedBy == _answer.addedBy


@pytest.mark.django_db(transaction=True)
def test_question_no_existing_user(unit, orct_data):
    builder = ThreadBuilder(unit)
    thread = builder.build(orct_data)

    assert thread.id
    assert thread.order == 0
    assert thread.kind == UnitLesson.COMPONENT
    assert thread.lesson.kind == Lesson.ORCT_QUESTION
    assert thread.lesson.title == orct_data["title"]
    assert thread.lesson.text == orct_data["question"]
    _answer = thread.get_answers().first().lesson
    assert _answer.title == "Answer"
    assert _answer.text == orct_data["answer"]

    assert thread.addedBy == unit.addedBy == thread.lesson.addedBy == _answer.addedBy


@pytest.mark.django_db(transaction=True)
def test_question_no_author(unit, orct_data):
    del orct_data["author"]

    builder = ThreadBuilder(unit)
    thread = builder.build(orct_data)

    assert thread.id
    assert thread.order == 0
    assert thread.kind == UnitLesson.COMPONENT
    assert thread.lesson.kind == Lesson.ORCT_QUESTION
    assert thread.lesson.title == orct_data["title"]
    assert thread.lesson.text == orct_data["question"]
    _answer = thread.get_answers().first().lesson
    assert _answer.title == "Answer"
    assert _answer.text == orct_data["answer"]

    assert thread.addedBy == unit.addedBy == thread.lesson.addedBy == _answer.addedBy
