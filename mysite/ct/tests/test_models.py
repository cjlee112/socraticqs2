import pytest

from .models import Lesson

from core.common.utils import get_onboarding_status_with_settings
from core.common.onboarding import CREATE_THREAD
from mysite.helpers import base64_to_file


@pytest.mark.django_db
def test_get_canvas_html(lesson_question_canvas, base64_gif_image):
    assert lesson_question_canvas.attachment is not None

    attachment = base64_to_file('data:image/gif;base64,{}'.format(base64_gif_image))

    lesson_question_canvas.attachment.save('image.gif', attachment, save=True)
    assert lesson_question_canvas.attachment.url is not None

    assert lesson_question_canvas.get_html().find(lesson_question_canvas.attachment.url) > -1


@pytest.mark.django_db
@pytest.mark.parametrize("kind, updated", [
    (Lesson.BASE_EXPLANATION, True),
    (Lesson.EXPLANATION, True),
    (Lesson.ORCT_QUESTION, False),
    (Lesson.ANSWER, True),
])
def test_onboarding_step_5_update(unique_instructor, kind, updated):
    Lesson(title='Lesson test', kind=kind, addedBy=unique_instructor).save()
    assert get_onboarding_status_with_settings(unique_instructor.id).get(CREATE_THREAD).get('done') == updated


@pytest.mark.django_db
@pytest.mark.parametrize("data, commit", [
    ({
        "students_number": 100500,
        "misconceptions_per_day": 500,
        "wrong_field": "wrong_value",
        "title": "New title"
    },
    False),
    ({
        "students_number": 100500,
        "misconceptions_per_day": 500,
        "wrong_field": "wrong_value",
        "title": "New title"
    },
    True)
])
def test_course_apply_from(mocker, course, data, commit):
    save = mocker.patch('ct.models.models.Model.save')
    save.reset_mock()
    title = 'Original title'
    course.title = title; course.students_number = 200
    result = course.apply_from(data, commit=commit)

    assert isinstance(result, type(course))
    assert not hasattr(course, 'wrong_field')
    assert course.students_number == 100500
    assert course.misconceptions_per_day == 500
    assert course.title == title

    save.assert_called_once() if commit else save.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("data, commit", [
    ({
        "exam_name": 'Midterm 4',
        "follow_up_assessment_date": '24/12/2019',
        "follow_up_assessment_grade": 50,
        "question_parts": 50,
        "average_score": 50,
        "graded_assessment_value": 50,
        "courselet_deadline": '24/12/2019',
        "courselet_days": 50,
        "error_resolution_days": 50,
        "courselet_completion_credit": 50,
        "late_completion_penalty": 50,
        "wrong_field": "wrong_value",
        "title": "New title"
    },
    False),
    ({
        "exam_name": 'Midterm 4',
        "follow_up_assessment_date": '24/12/2019',
        "follow_up_assessment_grade": 50,
        "question_parts": 50,
        "average_score": 50,
        "graded_assessment_value": 50,
        "courselet_deadline": '24/12/2019',
        "courselet_days": 50,
        "error_resolution_days": 50,
        "courselet_completion_credit": 50,
        "late_completion_penalty": 50,
        "wrong_field": "wrong_value",
        "title": "New title"
    },
    True)
])
def test_courselet_apply_from(mocker, unit, data, commit):
    save = mocker.patch('ct.models.models.Model.save')
    save.reset_mock()
    title = 'Original title'
    unit.title = title
    result = unit.apply_from(data, commit=commit)

    assert isinstance(result, type(unit))
    assert not hasattr(unit, 'wrong_field')
    assert unit.exam_name == 'Midterm 4'
    assert unit.follow_up_assessment_date == '24/12/2019'
    assert unit.follow_up_assessment_grade == 50
    assert unit.question_parts == 50
    assert unit.average_score == 50
    assert unit.graded_assessment_value == 50
    assert unit.courselet_deadline == '24/12/2019'
    assert unit.courselet_days == 50
    assert unit.error_resolution_days == 50
    assert unit.courselet_completion_credit == 50
    assert unit.late_completion_penalty == 50
    assert unit.title == title

    save.assert_called_once() if commit else save.assert_not_called()
