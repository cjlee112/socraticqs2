import pytest

from core.tasks import faq_notify_instructors, faq_notify_students


testdata = [
    (['test@example.com', 'test2@example.com'], 'dummy_link', 2),
    (['test@example.com', 'test2@example.com'], '', 0),
    ([], 'dummy_link', 0),
    ([], '', 0),
]


@pytest.mark.parametrize("students,faq_link,expected", testdata)
def test_faq_notify_students(students, faq_link, expected, mocker):
    send_mail = mocker.patch('core.utils.send_mail')
    faq_notify_students.delay(
        faq_link=faq_link,
        faq_title='Тестовий тайт факу / Test FAQ title',
        faq_text='Тестовий текст факу / Test FAQ text',
        course_title='Курс тайтл / Course title',
        courselet_title='Тайтл курслєту / Courselet title',
        parent_faq_title='Тайтл батьківського курслєту / Courselet parent title',
        students=students
    )
    assert send_mail.call_count == expected


@pytest.mark.parametrize("instructors,faq_link,expected", testdata)
def test_faq_notify_instructors(instructors, faq_link, expected, mocker):
    send_mail = mocker.patch('core.utils.send_mail')
    faq_notify_instructors.delay(
        faq_link=faq_link,
        faq_title='Тестовий тайт факу / Test FAQ title',
        faq_text='Тестовий текст факу / Test FAQ text',
        course_title='Курс тайтл / Course title',
        courselet_title='Тайтл курслєту / Courselet title',
        instructors=instructors
    )
    assert send_mail.call_count == expected
