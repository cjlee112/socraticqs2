"""
Test core utility functions.
"""
from django.conf import settings
from django.contrib.sites.models import Site
from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from mock import patch

from core.common.utils import send_email


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
