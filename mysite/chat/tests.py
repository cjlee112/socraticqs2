import json

from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from django.http.response import HttpResponseNotFound
from mock import patch, Mock

from ct.models import Course, Unit, Lesson, UnitLesson, CourseUnit, Role, Concept
from ct.templatetags.ct_extras import md2html
from .models import EnrollUnitCode
from .fsm_plugin.chat import get_specs, MESSAGE
from .fsm_plugin.additional import get_specs as get_specs_additional
from .fsm_plugin.resource import get_specs as get_specs_resource


class SetUpMixin(object):
    """
    Mixin to provide setUp method.
    """
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('test', 'test@test.com', 'test')
        get_specs()[0].save_graph(self.user.username)
        get_specs_additional()[0].save_graph(self.user.username)
        get_specs_resource()[0].save_graph(self.user.username)

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
        self.unitlesson = UnitLesson(
            unit=self.unit, order=0, lesson=lesson, addedBy=self.user, treeID=lesson.id
        )
        self.unitlesson.save()
        resource_lesson = Lesson(
            title='title for resource', text='text for resource', addedBy=self.user
        )
        resource_lesson.save()
        self.resource_unitlesson = UnitLesson(
            unit=self.unit, lesson=resource_lesson, addedBy=self.user, treeID=resource_lesson.id
        )
        self.resource_unitlesson.save()


class MainChatViewTests(SetUpMixin, TestCase):
    """
    Tests for main view.

    Should enroll user if not enrolled.
    Should render main_view.html template.
    """
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


class HistoryAPIViewTests(SetUpMixin, TestCase):
    """
    Tests /history API.
    """
    def test_positive_response(self):
        """
        Test positive case for /history call.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        chat_id = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code,)), follow=True
        ).context['chat_id']
        response = self.client.get(reverse('chat:history'), {'chat_id': chat_id}, follow=True)
        self.assertEquals(response.status_code, 200)

    def test_permission_denied(self):
        """
        Check that chat history can be viewed by chat author only.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        chat_id = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code,)), follow=True
        ).context['chat_id']
        self.user = User.objects.create_user('middle_man', 'test@test.com', 'test')
        self.client.login(username='middle_man', password='test')
        response = self.client.get(reverse('chat:history'), {'chat_id': chat_id}, follow=True)
        self.assertEquals(response.status_code, 403)

    def test_content(self):
        """
        Check that history content fits API documentation.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        chat_id = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code,)), follow=True
        ).context['chat_id']
        response = self.client.get(reverse('chat:history'), {'chat_id': chat_id}, follow=True)
        json_content = json.loads(response.content)
        self.assertIsInstance(json_content['input'], dict)
        self.assertIsInstance(json_content['addMessages'], list)
        self.assertEquals(len(json_content['addMessages']), 3)
        self.assertEquals(json_content['addMessages'][0]['name'], self.user.username)
        self.assertEquals(
            json_content['addMessages'][0]['html'], md2html(self.unitlesson.lesson.text)
        )
        self.assertEquals(json_content['addMessages'][1]['type'], 'message')
        self.assertEquals(json_content['addMessages'][1]['html'], MESSAGE.help)
        self.assertEquals(json_content['addMessages'][2]['type'], 'breakpoint')
        self.assertEquals(json_content['addMessages'][2]['html'], 'Courselet core lessons completed')


class ProgressAPIViewTests(SetUpMixin, TestCase):
    """
    Tests for /progress API.
    """
    def test_positive_response(self):
        """
        Test positive case for /progress call.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        chat_id = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code,)), follow=True
        ).context['chat_id']
        response = self.client.get(reverse('chat:progress'), {'chat_id': chat_id}, follow=True)
        self.assertEquals(response.status_code, 200)

    def test_permission_denied(self):
        """
        Check that chat progress can be viewed by chat author only.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        chat_id = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code,)), follow=True
        ).context['chat_id']
        self.user = User.objects.create_user('middle_man', 'test@test.com', 'test')
        self.client.login(username='middle_man', password='test')
        response = self.client.get(reverse('chat:progress'), {'chat_id': chat_id}, follow=True)
        self.assertEquals(response.status_code, 403)

    def test_content(self):
        """
        Check that history content fits API documentation.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        chat_id = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code,)), follow=True
        ).context['chat_id']
        response = self.client.get(reverse('chat:progress'), {'chat_id': chat_id}, follow=True)
        json_content = json.loads(response.content)
        self.assertIsInstance(json_content['progress'], float)
        self.assertIsInstance(json_content['breakpoints'], list)
        self.assertEquals(len(json_content['breakpoints']), 1)
        self.assertEquals(json_content['progress'], 1.0)
        self.assertEquals(json_content['breakpoints'][0]['html'], self.unitlesson.lesson.title)
        self.assertEquals(json_content['breakpoints'][0]['isDone'], True)
        self.assertEquals(json_content['breakpoints'][0]['isUnlocked'], True)


class ResourcesViewTests(SetUpMixin, TestCase):
    """
    Tests for /resources API call.
    """
    def test_positive_case(self):
        """
        Test positive case for /resources call.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        chat_id = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code,)), follow=True
        ).context['chat_id']
        response = self.client.get(reverse('chat:resources-list'), {'chat_id': chat_id}, follow=True)
        self.assertEquals(response.status_code, 200)

    def test_permission_denied(self):
        """
        Check that chat resources can be viewed by chat author only.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        chat_id = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code,)), follow=True
        ).context['chat_id']
        self.user = User.objects.create_user('middle_man', 'test@test.com', 'test')
        self.client.login(username='middle_man', password='test')
        response = self.client.get(reverse('chat:resources-list'), {'chat_id': chat_id}, follow=True)
        self.assertEquals(response.status_code, 403)

    def test_content(self):
        """
        Check that resources content fits ResourcesAPI documentation.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        chat_id = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code,)), follow=True
        ).context['chat_id']
        response = self.client.get(reverse('chat:resources-list'), {'chat_id': chat_id}, follow=True)
        json_content = json.loads(response.content)
        self.assertIsInstance(json_content['breakpoints'], list)
        self.assertEquals(len(json_content['breakpoints']), 2)
        # TODO Need to investigate why concepts also presented as Resources
        self.assertEquals(
            json_content['breakpoints'][1]['html'], self.resource_unitlesson.lesson.title
        )
        self.assertEquals(json_content['breakpoints'][1]['isDone'], False)
        self.assertEquals(json_content['breakpoints'][1]['isStarted'], False)
        self.assertEquals(json_content['breakpoints'][1]['isUnlocked'], True)

    def test_get_resources_message_by_id(self):
        """
        Test got get resources message by id from /resources response.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        chat_id = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code,)), follow=True
        ).context['chat_id']
        response = self.client.get(reverse('chat:resources-list'), {'chat_id': chat_id}, follow=True)
        json_content = json.loads(response.content)
        resource_response = self.client.get(
            reverse('chat:resources-detail', args=(json_content['breakpoints'][0]['id'],)),
            {'chat_id': chat_id}
        )
        # TODO add additional checks
        self.assertEquals(resource_response.status_code, 200)
        resource_response = self.client.get(
            reverse('chat:resources-detail', args=(json_content['breakpoints'][1]['id'],)),
            {'chat_id': chat_id}
        )
        self.assertEquals(resource_response.status_code, 200)
