from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from django.http.response import HttpResponseNotFound
from mock import patch, Mock

from ct.models import Course, Unit, Lesson, UnitLesson, CourseUnit, Role, Concept
from .models import EnrollUnitCode


class MainChatViewTests(TestCase):
    """
    Tests for main view.

    Should enroll user if not enrolled.
    Should render main_view.html template.
    """
    def setUp(self):
        from chat.fsm_plugin.chat import get_specs
        from chat.fsm_plugin.additional import get_specs as get_specs_additional
        self.client = Client()
        self.user = User.objects.create_user('test', 'test@test.com', 'test')
        get_specs()[0].save_graph(self.user.username)
        get_specs_additional()[0].save_graph(self.user.username)

        self.unit = Unit(title='Test title', addedBy=self.user)
        self.unit.save()
        self.course = Course(title='Test title',
                             description='test description',
                             access='Public',
                             enrollCode='111',
                             lockout='222',
                             addedBy=self.user)
        self.course.save()

        self.courseunit = CourseUnit(
            unit=self.unit, course=self.course,
            order=0, addedBy=self.user, releaseTime=timezone.now()
        )
        self.courseunit.save()
        self.concept = Concept.new_concept('bad', 'idea', self.unit, self.user)
        lesson = Lesson(title='title', text='text', addedBy=self.user)
        lesson.save()
        unitlesson = UnitLesson(
            unit=self.unit, order=0, lesson=lesson, addedBy=self.user, treeID=lesson.id
        )
        unitlesson.save()

    def test_main_view_enroll(self):
        """
        MainView should enroll Student that comes w/ enrollCode.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        response = self.client.get(reverse('chat:chat_enroll', args=(enroll_code,)), follow=True)
        self.assertTemplateUsed(response, 'chat/main_view.html')
        self.assertTrue(
            Role.objects.filter(role=Role.ENROLLED, user=self.user, course=self.course).exists()
        )

    def test_not_enroll_second_time(self):
        """
        Should not enroll second time if already enrolled.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        role = Role(role=Role.ENROLLED, course=self.course, user=self.user)
        role.save()
        response = self.client.get(reverse('chat:chat_enroll', args=(enroll_code,)), follow=True)
        self.assertEquals(
            Role.objects.filter(role=Role.ENROLLED, user=self.user, course=self.course).count(),
            1
        )

    def test_only_logged_in(self):
        """
        Only logged in users can access chat ui.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        response = self.client.get(reverse('chat:chat_enroll', args=(enroll_code,)), follow=True)
        self.assertTemplateUsed(response, 'psa/custom_login.html')

    def test_404_on_non_existent_enroll_code(self):
        """
        Should return 404 if enrollCode is not exists.
        """
        self.client.login(username='test', password='test')
        response = self.client.get(
            reverse('chat:chat_enroll', args=('nonexistentenrollcode',)), follow=True
        )
        self.assertIsInstance(response, HttpResponseNotFound)

    def test_passed_correct_variables(self):
        """
        Check that view fill template w/ correct varibles.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        response = self.client.get(reverse('chat:chat_enroll', args=(enroll_code,)), follow=True)
        variables = (
            ('course', self.course),
            ('unit', self.unit),
            ('lesson_cnt', len(self.unit.get_exercises())),
            ('duration', len(self.unit.get_exercises()) * 3),
        )
        for pair in variables:
            self.assertEquals(response.context.get(pair[0]), pair[1])

        self.assertIn('fsmstate', response.context)
        self.assertIn('next_point', response.context)
        self.assertIn('lessons', response.context)
        self.assertIn('chat_id', response.context)
        self.assertIn('concepts', response.context)

    @patch('chat.views.ChatInitialView.next_handler.start_point', return_value=Mock())
    def test_next_handler_start_point_called_once(self, mocked_start_point):
        """
        Check that ChatInitialView.next_handler.start_point called once.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        self.client.get(reverse('chat:chat_enroll', args=(enroll_code,)), follow=True)
        response = self.client.get(reverse('chat:chat_enroll', args=(enroll_code,)), follow=True)
        mocked_start_point.assert_called_once()
        self.assertEquals(response.context['next_point'], mocked_start_point.return_value)
