import base64

import pytest
from django.contrib.auth.models import User

from ct.models import Lesson, UnitLesson
from ..creators import ThreadBuilder


@pytest.mark.django_db
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


@pytest.mark.django_db
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


@pytest.mark.django_db
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


@pytest.mark.django_db
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


@pytest.mark.django_db
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


@pytest.mark.django_db
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


@pytest.mark.django_db
def test_question_multichoice(unit, multichoice_data):
    builder = ThreadBuilder(unit)
    thread = builder.build(multichoice_data)

    correct_text = f"{multichoice_data['question']}\r\n\r\n[choices]\r\n"

    for choice in multichoice_data["choices"]:
        if choice['correct']:
            correct_text += "(*) " + choice['text'] + f"\r\n{multichoice_data['answer']}\r\n"
        else:
            correct_text += "() " + choice['text'] + "\r\n"

    assert thread.id
    assert thread.order == 0
    assert thread.kind == UnitLesson.COMPONENT
    assert thread.lesson.kind == Lesson.ORCT_QUESTION
    assert thread.lesson.sub_kind == Lesson.MULTIPLE_CHOICES
    assert thread.lesson.title == multichoice_data["title"]
    assert thread.lesson.text == correct_text
    _answer = thread.get_answers().first().lesson
    assert _answer.title == "Answer"
    assert _answer.text == multichoice_data["answer"]

    assert thread.addedBy == unit.addedBy == thread.lesson.addedBy == _answer.addedBy


@pytest.mark.django_db
def test_question_comparisons(unit, comparisons_data):
    builder = ThreadBuilder(unit)
    thread = builder.build(comparisons_data)

    correct_text = f"{comparisons_data['question']}\r\n\r\n"

    for choice in comparisons_data["comparisons"]:
        correct_text += f"- {choice['text']}\r\n"

    assert thread.id
    assert thread.order == 0
    assert thread.kind == UnitLesson.COMPONENT
    assert thread.lesson.kind == Lesson.ORCT_QUESTION
    assert thread.lesson.title == comparisons_data["title"]
    assert thread.lesson.text == correct_text
    _answer = thread.get_answers().first().lesson
    assert _answer.title == "Answer"
    assert _answer.text == comparisons_data["answer"]

    assert thread.addedBy == unit.addedBy == thread.lesson.addedBy == _answer.addedBy


@pytest.mark.django_db
def test_question_canvas(unit, canvas_data):
    builder = ThreadBuilder(unit)
    thread = builder.build(canvas_data)

    assert thread.id
    assert thread.order == 0
    assert thread.kind == UnitLesson.COMPONENT
    assert thread.lesson.kind == Lesson.ORCT_QUESTION
    assert thread.lesson.sub_kind == Lesson.CANVAS
    assert base64.b64encode(thread.lesson.attachment.read()) == canvas_data["canvas"].encode()
    assert thread.lesson.title == canvas_data["title"]
    assert thread.lesson.text == canvas_data['question']
    _answer = thread.get_answers().first().lesson
    assert _answer.title == "Answer"
    assert _answer.text == canvas_data["answer"]

    assert thread.addedBy == unit.addedBy == thread.lesson.addedBy == _answer.addedBy
