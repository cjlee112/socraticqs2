from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from mock import patch, Mock
from ct.models import Course, Unit, CourseUnit, Role
from views import CourseView


class TestCourseView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')

    @patch('lms.views.get_object_or_404')
    @patch('lms.views.EnrollUnitCode.get_code')
    @patch('fsm.models.FSMState.find_live_sessions')
    def test_course_view(self, find_live_sessions, get_code, get_obj_or_404):
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

        course_mock = Mock()
        course_units = Mock()
        course_mock.get_course_units = course_units
        course_units.return_value = [Mock()]
        get_obj_or_404.return_value = course_mock

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
        self.course = Course(
            title='Great Course', description='the bestest', addedBy=self.user
        )
        self.course.save()

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
