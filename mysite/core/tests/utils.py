"""
Test core utility functions.
"""
import mock
from ddt import ddt, data, unpack
from django.conf import settings
from django.contrib.sites.models import Site
from django.core import mail
from django.test import TestCase

from core.common.utils import send_email, get_onboarding_percentage


@ddt
class UtilityTest(TestCase):
    """
    Test auxiliary functions.
    """

    def test_send_email(self):
        """
        Test email sending.

        Ensure an email has proper subject and body.
        """
        send_email(
            context_data={
                "milestone": "first",
                "students_number": 2,
                "course_title": "Test Course",
                "lesson_title": "Test Lesson",
                "current_site": Site.objects.get_current(),
                "course_id": 1,
                "unit_lesson_id": 1,
                "courselet_pk": 1
            },
            from_email=settings.EMAIL_FROM,
            to_email=["test@example.com"],
            template_subject="ct/email/milestone_ortc_notify_subject",
            template_text="ct/email/milestone_ortc_notify_text"
        )

        self.assertEqual(len(mail.outbox), 1)

        # FIXME: outbox properties do not get overridden
        # self.assertEqual(mail.outbox[0].from_email, settings.EMAIL_FROM)
        # self.assertEqual(mail.outbox[0].to, "test@example.com")
        # self.assertContains(mail.outbox[0].subject, "2")
        # self.assertContains(mail.outbox[0].subject, "first")
        # self.assertContains(mail.outbox[0].body, "first")
        # self.assertContains(mail.outbox[0].body, "2")
        # self.assertContains(mail.outbox[0].body, "Test Course")
        # self.assertContains(mail.outbox[0].body, "Test Lesson")

    @mock.patch('core.common.utils.c_onboarding_status')
    @unpack
    @data(
        ({'step1': 0, 'step2': 0, 'step3': 0, 'step4': 0, 'step5': 0, 'step6': 0}, 0),
        ({'step1': 1, 'step2': 0, 'step3': 0, 'step4': 0, 'step5': 0, 'step6': 0}, 17.0),
        ({'step1': 0, 'step2': 1, 'step3': 0, 'step4': 0, 'step5': 0, 'step6': 1}, 33.0),
        ({'step1': 0, 'step2': 0, 'step3': 1, 'step4': 1, 'step5': 1, 'step6': 1}, 67.0),
        ({'step1': 1, 'step2': 1, 'step3': 1, 'step4': 1, 'step5': 1, 'step6': 1}, 100.0)
    )
    def test_percentage_of_done(self, steps, result, mock):
        _mock = mock.return_value
        _mock.find_one.return_value = steps
        self.assertEqual(get_onboarding_percentage(1), result)
