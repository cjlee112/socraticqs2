import pytest

from mysite.helpers import base64_to_file


@pytest.mark.django_db
def test_get_canvas_html(lesson_question_canvas, base64_gif_image):
    assert lesson_question_canvas.attachment is not None

    attachment = base64_to_file('data:image/gif;base64,{}'.format(base64_gif_image))

    lesson_question_canvas.attachment.save('image.gif', attachment, save=True)
    assert lesson_question_canvas.attachment.url is not None

    assert lesson_question_canvas.get_html().find(lesson_question_canvas.attachment.url) > -1
