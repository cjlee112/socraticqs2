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
    @patch('fsm.models.FSMState.find_live_sessions')
    def test_course_view(self, find_live_sessions, get_obj_or_404):
        """
        This test tests that FSMState.find_live_sessions(request.user).filter(activity__course=course).first()
        return course and this course is present in page's  context"""
        
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
        course_units.return_value = Mock()
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



