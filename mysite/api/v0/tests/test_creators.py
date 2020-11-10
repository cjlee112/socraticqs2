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
def test_intro_w_image(unit, intro_data_w_image):
    author = User.objects.create(username="Ilona")

    builder = ThreadBuilder(unit)
    thread = builder.build(intro_data_w_image)

    assert thread.id
    assert thread.order == 0
    assert thread.kind == UnitLesson.COMPONENT
    assert thread.addedBy == author == thread.lesson.addedBy
    assert thread.lesson.kind == Lesson.BASE_EXPLANATION
    assert base64.b64encode(thread.lesson.attachment.read()) == intro_data_w_image["image"].encode()
    assert thread.lesson.title == intro_data_w_image["title"]
    assert thread.lesson.text == intro_data_w_image["message"]


@pytest.mark.django_db
def test_intro_w_image_wo_message(unit, intro_data_w_image):
    del intro_data_w_image["message"]
    author = User.objects.create(username="Ilona")

    builder = ThreadBuilder(unit)
    thread = builder.build(intro_data_w_image)

    assert thread.id
    assert thread.order == 0
    assert thread.kind == UnitLesson.COMPONENT
    assert thread.addedBy == author == thread.lesson.addedBy
    assert thread.lesson.kind == Lesson.BASE_EXPLANATION
    assert base64.b64encode(thread.lesson.attachment.read()) == intro_data_w_image["image"].encode()
    assert thread.lesson.title == intro_data_w_image["title"]
    assert thread.lesson.text == ""


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
def test_question_w_images(unit, orct_data_w_images):
    builder = ThreadBuilder(unit)
    thread = builder.build(orct_data_w_images)

    assert thread.id
    assert thread.order == 0
    assert thread.kind == UnitLesson.COMPONENT
    assert thread.lesson.kind == Lesson.ORCT_QUESTION
    assert base64.b64encode(thread.lesson.attachment.read()) == orct_data_w_images["image"].encode()
    assert thread.lesson.title == orct_data_w_images["title"]
    assert thread.lesson.text == orct_data_w_images['question']
    _answer = thread.get_answers().first().lesson
    assert _answer.title == "Answer"
    assert _answer.text == orct_data_w_images["answer"]
    assert base64.b64encode(_answer.attachment.read()) == orct_data_w_images["answerImg"].encode()

    assert thread.addedBy == unit.addedBy == thread.lesson.addedBy == _answer.addedBy


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
    assert base64.b64encode(thread.lesson.attachment.read()) == multichoice_data["image"].encode()
    assert thread.lesson.sub_kind == Lesson.MULTIPLE_CHOICES
    assert thread.lesson.title == multichoice_data["title"]
    assert thread.lesson.text == correct_text
    _answer = thread.get_answers().first().lesson
    assert _answer.title == "Answer"
    assert _answer.text == multichoice_data["answer"]
    assert base64.b64encode(_answer.attachment.read()) == multichoice_data["answerImg"].encode()

    assert thread.addedBy == unit.addedBy == thread.lesson.addedBy == _answer.addedBy


@pytest.mark.django_db
def test_question_multichoice_img(unit, multichoice_img_data):
    builder = ThreadBuilder(unit)
    thread = builder.build(multichoice_img_data)

    correct_text = f"{multichoice_img_data['question']}\r\n\r\n[choices]\r\n"

    for choice in multichoice_img_data["choices"]:
        if choice['correct']:
            correct_text += "(*) " + f' <img src="{choice.get("img")}">' + \
                f"\r\n{multichoice_img_data['answer']}\r\n"
        else:
            correct_text += "() " + f' <img src="{choice.get("img")}">' + "\r\n"

    assert thread.id
    assert thread.order == 0
    assert thread.kind == UnitLesson.COMPONENT
    assert thread.lesson.kind == Lesson.ORCT_QUESTION
    assert thread.lesson.sub_kind == Lesson.MULTIPLE_CHOICES
    assert thread.lesson.title == multichoice_img_data["title"]
    assert thread.lesson.text == correct_text
    _answer = thread.get_answers().first().lesson
    assert _answer.title == "Answer"
    assert _answer.text == multichoice_img_data["answer"]

    assert thread.addedBy == unit.addedBy == thread.lesson.addedBy == _answer.addedBy


@pytest.mark.django_db
def test_question_comparisons(unit, comparisons_data):
    builder = ThreadBuilder(unit)
    thread = builder.build(comparisons_data)

    correct_text = f"{comparisons_data['question']}\r\n\r\n"

    for choice in comparisons_data["comparisons"]:
        correct_text += f"- {choice['text']}\r\n\r\n"

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
def test_question_comparisons_img(unit, comparisons_data_w_img):
    builder = ThreadBuilder(unit)
    thread = builder.build(comparisons_data_w_img)

    correct_text = f"{comparisons_data_w_img['question']}\r\n\r\n"

    for choice in comparisons_data_w_img["comparisons"]:
        correct_text += f'.. image:: {choice.get("img")}\r\n'

    assert thread.id
    assert thread.order == 0
    assert thread.kind == UnitLesson.COMPONENT
    assert thread.lesson.kind == Lesson.ORCT_QUESTION
    assert thread.lesson.title == comparisons_data_w_img["title"]
    assert thread.lesson.text == correct_text
    _answer = thread.get_answers().first().lesson
    assert _answer.title == "Answer"
    assert _answer.text == comparisons_data_w_img["answer"]

    assert thread.addedBy == unit.addedBy == thread.lesson.addedBy == _answer.addedBy


@pytest.mark.django_db
def test_question_comparisons_2_img(unit, comparisons_data_w_2_img):
    builder = ThreadBuilder(unit)
    thread = builder.build(comparisons_data_w_2_img)

    correct_text = f"{comparisons_data_w_2_img['question']}\r\n\r\n"

    for choice in comparisons_data_w_2_img["comparisons"]:
        correct_text += f'.. image:: {choice.get("img")}\r\n'

    assert thread.id
    assert thread.order == 0
    assert thread.kind == UnitLesson.COMPONENT
    assert thread.lesson.kind == Lesson.ORCT_QUESTION
    assert thread.lesson.title == comparisons_data_w_2_img["title"]
    assert thread.lesson.text == correct_text
    _answer = thread.get_answers().first().lesson
    assert _answer.title == "Answer"
    assert _answer.text == comparisons_data_w_2_img["answer"]

    assert thread.addedBy == unit.addedBy == thread.lesson.addedBy == _answer.addedBy


@pytest.mark.django_db
def test_question_comparisons_img_and_text(unit, comparisons_data_w_img_and_text):
    builder = ThreadBuilder(unit)
    thread = builder.build(comparisons_data_w_img_and_text)

    correct_text = f"{comparisons_data_w_img_and_text['question']}\r\n\r\n"

    for choice in comparisons_data_w_img_and_text["comparisons"]:
        correct_text += f'- {choice.get("text", "")}\r\n\r\n.. image:: {choice.get("img")}\r\n'

    assert thread.id
    assert thread.order == 0
    assert thread.kind == UnitLesson.COMPONENT
    assert thread.lesson.kind == Lesson.ORCT_QUESTION
    assert thread.lesson.title == comparisons_data_w_img_and_text["title"]
    assert thread.lesson.text == correct_text
    _answer = thread.get_answers().first().lesson
    assert _answer.title == "Answer"
    assert _answer.text == comparisons_data_w_img_and_text["answer"]

    assert thread.addedBy == unit.addedBy == thread.lesson.addedBy == _answer.addedBy


@pytest.mark.django_db
def test_question_comparisons_w_image(unit, comparisons_data_w_images):
    builder = ThreadBuilder(unit)
    thread = builder.build(comparisons_data_w_images)

    correct_text = f"{comparisons_data_w_images['question']}\r\n\r\n"

    for choice in comparisons_data_w_images["comparisons"]:
        correct_text += f"- {choice['text']}\r\n\r\n"

    assert thread.id
    assert thread.order == 0
    assert thread.kind == UnitLesson.COMPONENT
    assert thread.lesson.kind == Lesson.ORCT_QUESTION
    assert base64.b64encode(thread.lesson.attachment.read()) == comparisons_data_w_images["image"].encode()
    assert thread.lesson.title == comparisons_data_w_images["title"]
    assert thread.lesson.text == correct_text
    _answer = thread.get_answers().first().lesson
    assert _answer.title == "Answer"
    assert _answer.text == comparisons_data_w_images["answer"]
    assert base64.b64encode(_answer.attachment.read()) == comparisons_data_w_images["answerImg"].encode()

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
