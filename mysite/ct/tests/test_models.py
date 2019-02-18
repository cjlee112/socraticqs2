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
