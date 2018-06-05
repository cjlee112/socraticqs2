import pytest

from ct.forms import (
    ResponseForm,
    SelfAssessForm,
    ReorderForm,
    NextLikeForm,
    NextForm,
    LaunchFSMForm,
    UnitTitleForm,
    CourseTitleForm,
    ConceptForm,
    NewConceptForm,
    ConceptLinkForm,
    ConceptGraphForm,
    NewErrorForm,
    SearchFormBase,
    LogoutForm,
    CancelForm,
    AnswerLessonForm, NewLessonForm)
from ct.models import Lesson


def test_response_form_positive():
    data = {'text': 'test answer', 'confidence': 'guess'}
    form = ResponseForm(data=data)
    assert form.is_valid() == True


def test_response_form_negative():
    data = {'text': 'test answer', 'confidence': ''}
    form = ResponseForm(data=data)
    assert form.is_valid() == False


def test_self_assess_form_positive():
    data = {'selfeval': 'correct', 'status': 'review'}
    form = SelfAssessForm(data=data)
    assert form.is_valid() == True


def test_self_assess_form_negative():
    data = {'selfeval': 'correct', 'status': 'false_status'}
    form = SelfAssessForm(data=data)
    assert form.is_valid() == False


def test_reorder_form_positive():
    data = {'newOrder': '0', 'oldOrder': '1'}
    form = ReorderForm(0, 2, data)
    assert form.is_valid() == True


def test_reorder_form_negative():
    data = {'newOrder': 'false1', 'oldOrder': 'false2'}
    form = ReorderForm(0, 2, data)
    assert form.is_valid() == False


def test_next_like_form_positive():
    form = NextLikeForm(data={'liked': 'on'})
    assert form.is_valid() == True


def test_next_like_form_negative():
    form = NextLikeForm()
    assert form.is_valid() == False


def test_next_form_positive():
    form = NextForm(data={'fsmtask': 'launch'})
    assert form.is_valid() == True


def test_next_form_negative():
    form = NextForm(data={'fsmtask_false': 'launch'})
    assert form.is_valid() == False


def test_launch_form_positive():
    form = LaunchFSMForm('fsmname', 'fsmlabel', data={'fsmName': 'fsmname', 'fsmtask': 'fsmtask'})
    assert form.is_valid() == True


def test_launch_form_negative():
    form = LaunchFSMForm('fsmname', 'fsmlabel')
    assert form.is_valid() == False


def test_unit_title_form_positive():
    form = UnitTitleForm(data={'title': 'test_title'})
    assert form.is_valid() == True


def test_unit_title_form_negative():
    form = UnitTitleForm(data={'title_false': 'test_title'})
    assert form.is_valid() == False


def test_course_title_form_positive():
    form = CourseTitleForm(data={'title': 'test_title', 'access': 'public', 'description': 'test_description'})
    assert form.is_valid() == True


def test_course_title_form_negative():
    form = CourseTitleForm(data={'title': 'test_title'})
    assert form.is_valid() == False


def test_concept_form_positive():
    form = ConceptForm(data={'title': 'test_title'})
    assert form.is_valid() == True


def test_concept_form_negative():
    form = ConceptForm(data={'title_false': 'test_title'})
    assert form.is_valid() == False


def test_new_concept_form_positive():
    form = NewConceptForm(data={'title': 'test_title', 'description': 'test_description', 'submitLabel': 'label'})
    assert form.is_valid() == True


def test_new_concept_form_negative():
    form = NewConceptForm(data={'title': 'test_title'})
    assert form.is_valid() == False


def test_concept_link_form_positive():
    form = ConceptLinkForm(data={'relationship': 'defines'})
    assert form.is_valid() == True


def test_concept_link_form_negative():
    form = ConceptLinkForm(data={'relationship': 'false_rel'})
    assert form.is_valid() == False


def test_concept_graph_form_positive():
    form = ConceptGraphForm(data={'relationship': 'depends'})
    assert form.is_valid() == True


def test_concept_graph_form_negative():
    form = ConceptGraphForm(data={'relationship': 'false_rel'})
    assert form.is_valid() == False


def test_new_error_form_positive():
    form = NewErrorForm(data={'title': 'test_title', 'text': 'test_text'})
    assert form.is_valid() == True


def test_new_error_form_negative():
    form = NewErrorForm(data={'title_false': 'test_title', 'text': 'test_text'})
    assert form.is_valid() == False


def test_search_form_positive():
    """
    Base Form.
    """
    form = SearchFormBase(data={})
    assert form.is_valid() == True


def test_logout_form():
    form = LogoutForm(data={'task': 'task_name'})
    assert form.is_valid() == True


def test_cancel_form():
    form = CancelForm(data={'task': 'task_name'})
    assert form.is_valid() == True


def test_answerlesson_form_without_sub_kind():
    """Test case when no sub_kind passed to AnswerLessonForm no raises error."""
    form = AnswerLessonForm(data={
        'title': 'Answer',
        'text': 'some answer',
        'number_value': '0',
        'number_min_value': '0',
        'number_max_value': '0',
        'medium': Lesson.READING,
        'url': '',
        'changeLog': '',
        'sub_kind': '',
    })
    assert form.is_valid() == True

@pytest.mark.django_db
def test_lesson_answer_attachment_form(base64_gif_image, lesson_answer_canvas):
    attachment = 'data:image/gif;base64,{}'.format(base64_gif_image)
    form = AnswerLessonForm(
        instance=lesson_answer_canvas.lesson,
        data={'attachment': attachment, 'title': 'test_title', 'text': '',
        'medium': Lesson.READING, 'sub_kind': 'canvas',
        'number_value': '0', 'number_min_value': '0', 'number_max_value': '0',
        'url': '', 'changeLog': ''}
    )
    assert form.is_valid() == True

    lesson_answer = form.save(commit=True)
    assert lesson_answer == lesson_answer_canvas.lesson
    assert lesson_answer.attachment.url is not None
