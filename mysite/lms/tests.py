import json
import datetime
from django.utils import timezone

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.test import TestCase
from mock import patch, Mock

from chat.models import Chat, EnrollUnitCode
from ct.models import Course, Unit, CourseUnit, Role, Concept, Lesson, UnitLesson


class TestCourseView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')

        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()

        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()

        self.course_unit = CourseUnit(course=self.course, unit=self.unit, order=0, addedBy=self.user)
        self.course_unit.save()

        self.role = Role(course=self.course, user=self.user, role=Role.INSTRUCTOR)
        self.role.save()

        self.enroll = EnrollUnitCode.get_code_for_user_chat(self.course_unit, True, self.user)

        self.history_live_chat = Chat(
            user=self.user,
            is_live=True,
            enroll_code=self.enroll
        )
        self.history_live_chat.save()


    @patch('lms.views.ChatProgressSerializer')
    @patch('lms.views.get_object_or_404')
    @patch('lms.views.EnrollUnitCode.get_code')
    @patch('fsm.models.FSMState.find_live_sessions')
    @patch('chat.models.Chat.objects.filter')
    def test_course_view(self, chatFilterMock, find_live_sessions, get_code, get_obj_or_404, ChatProgressSerializer):
        """
        This test tests that:
         - query FSMState.find_live_sessions(request.user).filter(activity__course=course).first()
           return live session and this live session is present in page's context
        """
        filter_mock = Mock()
        filter_mock.filter = Mock()

        find_live_sessions.return_value = filter_mock

        first_mock = Mock()
        filter_mock.filter.return_value = first_mock
        first_mock.first = Mock()
        first_mock.first.return_value = Mock()
        first_mock.first.return_value.id = 1

        unit = Mock()
        unit.unit.get_exercises.return_value=[Mock()]
        course_mock = Mock()
        course_units = Mock()
        course_mock.get_course_units = course_units
        course_units.return_value = [unit]
        get_obj_or_404.return_value = course_mock

        chatFilterMock = Mock()
        chatFilterMock.return_value = [Mock()]

        ChatProgressSerializer.data.get.return_value = 0

        response = self.client.get(reverse('lms:course_view', kwargs={'course_id': 1}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(filter_mock.filter.call_count, 1)
        self.assertEqual(first_mock.first.call_count, 1)
        self.assertEqual(get_obj_or_404.call_count, 1)

        self.assertTemplateUsed(response, 'lms/course_page.html')
        # context should contain these keys: course, liveSession, courslets
        self.assertIn('course', response.context)
        self.assertIn('liveSession', response.context)
        self.assertIn('courslets', response.context)

    def test_course_view_negative(self):
        """
        This test tests case when teacher not yet (opened) joined live session and
        student opens course page.
        Student should not see 'Join Live Session' button on the top of the page.
        """
        response = self.client.get(
            reverse('lms:course_view', kwargs={'course_id': self.course.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lms/course_page.html')
        self.assertIn('course', response.context)
        self.assertIn('liveSession', response.context)
        self.assertIn('courslets', response.context)
        self.assertEqual(response.context['liveSession'], None)
        self.assertFalse(response.context['liveSession'])

    #TODO: write test when teacher really creates Course and Courslets inside of the course and student open page.
    #TODO: user should see 'Join' button.


    @patch('chat.models.Chat.get_spent_time')
    def test_live_chat_history_time_spent(self, get_spent_time):
        get_spent_time.return_value = datetime.timedelta(days=1, hours=1)
        response = self.client.get(reverse('lms:course_view', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lms/course_page.html')
        self.assertIn('livesessions', response.context)
        self.assertNotEquals(response.context['livesessions'], [])
        self.assertEqual(response.context['livesessions'][0].get_formatted_time_spent(), '1 day, 1:00:00')


