"""
Test core utility functions.
"""
import mock  # FIXME move to unittest.mock
from unittest import skip
from ddt import ddt, data, unpack
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail
from django.test import TestCase
from django.shortcuts import reverse
from django.utils import timezone

from accounts.models import Instructor
from chat.models import EnrollUnitCode, Chat
from core.common.utils import send_email, get_onboarding_percentage
from core.common import onboarding
from core.common.utils import ONBOARDING_STEPS_DEFAULT_TEMPLATE, \
    get_onboarding_status_with_settings, get_redirect_url
from ct.models import Course, CourseUnit, Unit, Role
from ctms.models import Invite


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
        ({onboarding.STEP_1: 0, onboarding.STEP_2: 0, onboarding.STEP_3: 0, onboarding.STEP_4: 0, onboarding.STEP_5: 0, onboarding.STEP_6: 0, onboarding.STEP_7: 0}, 0),
        ({onboarding.STEP_1: 1, onboarding.STEP_2: 0, onboarding.STEP_3: 0, onboarding.STEP_4: 0, onboarding.STEP_5: 0, onboarding.STEP_6: 0, onboarding.STEP_7: 0}, 14.0),
        ({onboarding.STEP_1: 0, onboarding.STEP_2: 1, onboarding.STEP_3: 0, onboarding.STEP_4: 0, onboarding.STEP_5: 0, onboarding.STEP_6: 1, onboarding.STEP_7: 1}, 43.0),
        ({onboarding.STEP_1: 0, onboarding.STEP_2: 0, onboarding.STEP_3: 1, onboarding.STEP_4: 1, onboarding.STEP_5: 1, onboarding.STEP_6: 1, onboarding.STEP_7: 0}, 57.0),
        ({onboarding.STEP_1: 1, onboarding.STEP_2: 0, onboarding.STEP_3: 1, onboarding.STEP_4: 1, onboarding.STEP_5: 1, onboarding.STEP_6: 1, onboarding.STEP_7: 1}, 86.0),
        ({onboarding.STEP_1: 1, onboarding.STEP_2: 1, onboarding.STEP_3: 1, onboarding.STEP_4: 1, onboarding.STEP_5: 1, onboarding.STEP_6: 1, onboarding.STEP_7: 1}, 100.0)
    )
    def test_percentage_of_done(self, steps, result, mock):
        _mock = mock.return_value
        _mock.find_one.return_value = steps
        self.assertEqual(get_onboarding_percentage(1), result)

    @mock.patch('core.common.utils.get_onboarding_percentage')
    @mock.patch('core.common.utils.waffle')
    def test_get_redirect_url(self, waffle_mock, percentage_mock):
        student = User.objects.create_user('student', 'student@test.com', '123123')



        # user has instructor and onboarding is enabled and equals 100

        waffle_mock.switch_is_active.return_value = True
        percentage_mock.return_value = 100

        Instructor.objects.create(
            user=student,
        )
        self.assertEqual(get_redirect_url(student), reverse('ctms:my_courses'))
        # FIXME examine upgrade to unittest.mock issue
        waffle_mock.assert_called()
        percentage_mock.assert_called()

        # user has instructor and onboarding is enabled and equals less than 100

        waffle_mock.reset_mock()
        percentage_mock.reset_mock()
        waffle_mock.switch_is_active.return_value = True
        percentage_mock.return_value = 70
        self.assertEqual(get_redirect_url(student), reverse('ctms:onboarding'))
        waffle_mock.assert_called()
        percentage_mock.assert_called()

        # user has instructor and onboarding is disabled

        waffle_mock.reset_mock()
        percentage_mock.reset_mock()
        waffle_mock.switch_is_active.return_value = False
        self.assertEqual(get_redirect_url(student), reverse('ctms:my_courses'))
        waffle_mock.assert_called()
        percentage_mock.assert_called()

    def test_get_redirect_url_with_invite(self):
        student = User.objects.create_user('student', 'student@test.com', '123123')
        instructor_user = User.objects.create_user('instructor', 'instructor@test.com', '123123')
        Instructor.objects.create(
            user=instructor_user,

        )

        course = Course.objects.create(title='Test title',
                        description='test description',
                        access='Public',
                        enrollCode='111',
                        lockout='222',
                        addedBy=instructor_user)
        unit = Unit.objects.create(title='Test title', addedBy=instructor_user)
        courseunit = CourseUnit.objects.create(
            unit=unit, course=course,
            order=0, addedBy=instructor_user, releaseTime=timezone.now()
        )
        enroll_unit_code = EnrollUnitCode.get_code(courseunit, give_instance=True)

        # create invite
        Invite.create_new(True, course, instructor_user.instructor, student.email, 'student', enroll_unit_code)

        # simulate student has come in chat but haven't started it yet

        Role.objects.create(
            user=student,
            course=course,
            role=Role.ENROLLED
        )

        self.assertEqual(get_redirect_url(student), reverse('lms:course_view', kwargs={'course_id': course.id}))  # to lms/course from role

        course_2 = Course.objects.create(
            title='Test title2',
            description='test description2',
            access='Public',
            enrollCode='1112',
            lockout='2222',
            addedBy=instructor_user
        )

        unit_2 = Unit.objects.create(title='Test title 2', addedBy=instructor_user)

        courseunit_2 = CourseUnit.objects.create(
            unit=unit_2, course=course_2,
            order=1, addedBy=instructor_user, releaseTime=timezone.now()
        )

        enroll_unit_code_2 = EnrollUnitCode.get_code(courseunit_2, give_instance=True)
        Chat.objects.create(
            user=student,
            instructor=instructor_user,
            enroll_code=enroll_unit_code_2
        )

        self.assertEqual(get_redirect_url(student), reverse('lms:course_view', kwargs={'course_id': course_2.id}))  # to lms/course from role
