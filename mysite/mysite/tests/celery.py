import datetime
from unittest import mock
import unittest
from django.utils import timezone
from unittest.mock import Mock, PropertyMock
from django.test import TestCase
from django.contrib.sessions.models import Session

# from core.tasks import send_outcome, check_anonymous
from lti.tasks import send_outcome


class CeleryTasksTest(TestCase):
    @unittest.skip("skip unless fixed")
    @mock.patch('mysite.celery.UserSession.objects.filter')
    @mock.patch('mysite.celery.User.objects.filter')
    def test_check_anonymous_user_session_no_session(self, mock_User_filter, mock_UserSession_filter):
        mock_user = Mock(id=1)
        call_mock_User_filter = [mock_user]

        mock_session = Mock(id=2)

        # user_session.session
        p = PropertyMock(return_value=3, side_effect=Session.DoesNotExist('Object Does not exist'))
        type(mock_session).session = p

        call_mock_UserSession_filter = [mock_session]

        mock_User_filter.return_value = call_mock_User_filter
        mock_UserSession_filter.return_value = call_mock_UserSession_filter

        mock_user_del = Mock()
        mock_user.delete = mock_user_del

        # response = check_anonymous()

        mock_user_del.assert_called_once_with()

        mock_User_filter.assert_called_with(groups__name='Temporary')
        mock_UserSession_filter.assert_called_with(user__groups__name='Temporary')

    @unittest.skip("skip unless fixed")
    @mock.patch('mysite.celery.UserSession.objects.filter')
    @mock.patch('mysite.celery.User.objects.filter')
    def test_check_anonymous_user_session_has_session(self, mock_User_filter, mock_UserSession_filter):
        mock_user = Mock(id=1)
        call_mock_User_filter = [mock_user]

        mock_session = Mock(id=2)

        # user_session.session
        mock_session.session.expire_date = timezone.now() - datetime.timedelta(days=1)

        sess_session_del = Mock()
        sess_user_del = Mock()

        mock_session.session.delete = sess_session_del
        mock_session.user.delete = sess_user_del
        call_mock_UserSession_filter = [mock_session]

        mock_User_filter.return_value = call_mock_User_filter
        mock_UserSession_filter.return_value = call_mock_UserSession_filter

        mock_user_del = Mock()
        mock_user.delete = mock_user_del

        # response = check_anonymous()

        sess_session_del.assert_called_once_with()
        sess_user_del.assert_called_once_with()
        mock_user_del.assert_called_once_with()

        mock_User_filter.assert_called_with(groups__name='Temporary')
        mock_UserSession_filter.assert_called_with(user__groups__name='Temporary')

    @mock.patch('lti.tasks.GradedLaunch.objects.get')
    @mock.patch('lti.tasks.send_score_update')
    def test_send_outcome(self, mock_send_score_update, mock_GradedLaunch_get):
        get_mock_ret_val = Mock()
        mock_GradedLaunch_get.return_value = get_mock_ret_val
        send_outcome('0', assignment_id=1)
        mock_GradedLaunch_get.assert_called_once_with(id=1)
        mock_send_score_update.assert_called_once_with(get_mock_ret_val, '0')
