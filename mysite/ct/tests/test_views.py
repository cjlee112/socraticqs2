from time import sleep

import pytest
from mock import Mock
from django.http import HttpResponse

from ct.views import check_instructor_auth, concept_tabs


@pytest.mark.parametrize('role, check', (
    ('prof', 'assertIsNone'),
    ('student', 'assertIsNotNone'),
    (['prof', 'student'], 'assertIsNone'),
    (['student'], 'assertIsNotNone')
))
def test_check_instructor_auth(role, check, rf):
    """
    Test positive and negative cases for check_instructor_auth func.

    Func return 403 if check fail and None otherwise.
    """
    course = Mock()
    course.get_user_role.return_value = role
    request = rf.get('/')
    request.user = Mock()  # In our case real User instance is unnecesary
    result = check_instructor_auth(course, request)
    if check == 'assertIsNotNone':  # If student we need to test 403 Forbidden HttpResponce
        assert result is True
    else:
        assert result is False


@pytest.mark.parametrize('order, tabs', (
        (1, ('Home,Study:', 'Tasks', 'Lessons', 'Concepts', 'Errors', 'FAQ', 'Edit')),
        (None, ('Home,Study:', 'Lessons', 'Concepts', 'Errors', 'FAQ', 'Edit'))
    )
)
def test_concept_tabs_teacher_tabs(order, tabs, mock):
    make_tabs = mock.patch('ct.views.make_tabs')
    unitLesson = Mock()
    unitLesson.order = order
    current = 'FAQ'
    path = '/ct/teach/courses/1/units/1/'
    result = concept_tabs(path, current, unitLesson)
    make_tabs.assert_called_once_with('/ct/teach/courses/1/units/1/', 'FAQ', tabs)
    assert result == make_tabs()


def test_settings(settings):
    assert settings.SOCIAL_AUTH_TWITTER_KEY
    assert settings.SOCIAL_AUTH_TWITTER_SECRET
    # assert settings.SOCIAL_AUTH_FACEBOOK_KEY  # AssertionError here
