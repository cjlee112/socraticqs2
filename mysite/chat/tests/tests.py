import json

from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from django.http.response import HttpResponseNotFound
from mock import patch, Mock
import injections

from ct.models import Course, Unit, Lesson, UnitLesson, CourseUnit, Role, Concept
from ct.templatetags.ct_extras import md2html
from ..models import EnrollUnitCode, Message
from ..serializers import (
    InternalMessageSerializer,
    InputSerializer,
    MessageSerializer,
    ChatProgressSerializer,
    ChatHistorySerializer,
    LessonSerializer,
)
from ..services import TestHandler
from ..models import Chat
from ..fsm_plugin.chat import get_specs, END as CHAT_END
from ..fsm_plugin.additional import get_specs as get_specs_additional
from ..fsm_plugin.resource import END, get_specs as get_specs_resource


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
        self.assertIn('will_learn', response.context)
        self.assertIn('need_to_know', response.context)

    @patch('chat.views.ChatInitialView.next_handler.start_point', return_value=Mock())
    def test_next_handler_start_point_called_once(self, mocked_start_point):
        """
        Check that ChatInitialView.next_handler.start_point called once.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        self.client.get(reverse('chat:chat_enroll', args=(enroll_code,)), follow=True)
        response = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code,)), follow=True
        )
        mocked_start_point.assert_called_once()
        self.assertEquals(response.context['next_point'], mocked_start_point.return_value)


class MessagesViewTests(SetUpMixin, TestCase):
    """
    Test for MessagesView API.
    """
    fixtures = ['chat/tests/fixtures/initial_data_enchanced.json']

    def test_positive_case(self):
        """
        Check positive case for MessagesView response.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        chat_id = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code,)), follow=True
        ).context['chat_id']
        response = self.client.get(reverse('chat:history'), {'chat_id': chat_id}, follow=True)
        json_content = json.loads(response.content)
        msg_id = json_content['addMessages'][1]['id']
        response = self.client.get(
            reverse('chat:messages-detail', args=(msg_id,)),
            {'chat_id': chat_id},
            follow=True
        )
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(json.loads(response.content)['addMessages']), 3)

    def test_permission_denied(self):
        """
        Check for permissions check.

        User from request should be the same as message owner.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        chat_id = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code,)), follow=True
        ).context['chat_id']
        response = self.client.get(reverse('chat:history'), {'chat_id': chat_id}, follow=True)
        json_content = json.loads(response.content)
        msg_id = json_content['addMessages'][1]['id']

        self.user = User.objects.create_user('middle_man', 'test@test.com', 'test')
        self.client.login(username='middle_man', password='test')

        response = self.client.get(
            reverse('chat:messages-detail', args=(msg_id,)),
            {'chat_id': chat_id},
            follow=True
        )
        self.assertEquals(response.status_code, 403)

    def test_inappropriate_message_put(self):
        """
        Check for inappropriate PUT request.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        chat_id = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code,)), follow=True
        ).context['chat_id']
        response = self.client.get(reverse('chat:history'), {'chat_id': chat_id}, follow=True)
        json_content = json.loads(response.content)
        msg_id = json_content['addMessages'][1]['id']
        msg_data = json_content['addMessages'][1]
        msg_data['text'] = 'test text'
        msg_data['chat_id'] = chat_id

        response = self.client.put(
            reverse('chat:messages-detail', args=(msg_id,)),
            data=json.dumps(msg_data),
            content_type='application/json',
            follow=True
        )

        self.assertEquals(response.status_code, 200)
        json_content = json.loads(response.content)
        self.assertNotIn('text', json_content['addMessages'][0])

    def test_valid_message_put(self):
        """
        Test a valid case when Student puts `text` to add `Response`.
        """
        course_unit = Course.objects.all()[0].get_course_units()[0]
        enroll_code = EnrollUnitCode.get_code(course_unit)

        self.client.login(username='test', password='test')
        chat_id = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code,)), follow=True
        ).context['chat_id']
        response = self.client.get(
            reverse('chat:history'), {'chat_id': chat_id}, follow=True
        )
        json_content = json.loads(response.content)

        next_url = json_content['input']['url']

        answer = 'My Answer'
        response = self.client.put(
            next_url,
            data=json.dumps({"text": answer, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )
        self.assertEquals(response.status_code, 200)
        json_content = json.loads(response.content)

        self.assertIn('html', json_content['addMessages'][0])
        self.assertEquals(json_content['addMessages'][0]['html'], answer)

    def test_typical_chat_flow(self):
        """
        Check for typical chat flow.
        """
        course_unit = Course.objects.all()[0].get_course_units()[0]
        enroll_code = EnrollUnitCode.get_code(course_unit)

        self.client.login(username='test', password='test')
        chat_id = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code,)), follow=True
        ).context['chat_id']
        response = self.client.get(
            reverse('chat:history'), {'chat_id': chat_id}, follow=True
        )
        json_content = json.loads(response.content)

        next_url = json_content['input']['url']

        answer = 'My Answer'
        response = self.client.put(
            next_url,
            data=json.dumps({"text": answer, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        self.assertIsNotNone(json_content['input']['options'])
        self.assertEquals(len(json_content['addMessages']), 2)

        self_eval = json_content['input']['options'][2]['value']
        self_eval_text = json_content['input']['options'][2]['text']

        response = self.client.put(
            next_url,
            data=json.dumps({"option": self_eval, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        self.assertEquals(json_content['addMessages'][0]['html'], self_eval_text)

        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        self.assertEquals(len(json_content['addMessages']), 3)
        self.assertEquals(json_content['addMessages'][0]['html'], self_eval_text)

        response = self.client.put(
            next_url,
            data=json.dumps({"text": answer, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        self_eval = json_content['input']['options'][0]['value']

        response = self.client.put(
            next_url,
            data=json.dumps({"option": self_eval, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']
        msg_id = json_content['input']['includeSelectedValuesFromMessages'][0]

        response = self.client.put(
            next_url,
            data=json.dumps({"selected": {msg_id: {"errorModel": ["80"]}}, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        self.assertEquals(json_content['input']['type'], 'text')
        self.assertEquals(len(json_content['addMessages']), 4)

        response = self.client.put(
            next_url,
            data=json.dumps({"text": answer, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        self_eval = json_content['input']['options'][1]['value']

        response = self.client.put(
            next_url,
            data=json.dumps({"option": self_eval, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']
        msg_id = json_content['input']['includeSelectedValuesFromMessages'][0]

        response = self.client.put(
            next_url,
            data=json.dumps({"selected": {msg_id: {"errorModel": ["104"]}}, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        response = self.client.put(
            next_url,
            data=json.dumps({"option": 1, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        response = self.client.put(
            next_url,
            data=json.dumps({"option": 1, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        self.assertEquals(
            json_content['addMessages'][0]['html'],
            '<dl>\n<dt><strong>Em1</strong></dt>\n<dd><p>Em1 description</p>\n</dd>\n</dl>\n'
        )

        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        status_msg = json_content['input']['options'][0]['text']
        status_value = json_content['input']['options'][0]['value']

        response = self.client.put(
            next_url,
            data=json.dumps({"option": status_value, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        self.assertEquals(len(json_content['addMessages']), 4)
        self.assertEquals(json_content['addMessages'][0]['html'], status_msg)


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
        self.assertEquals(len(json_content['addMessages']), 4)
        self.assertEquals(json_content['addMessages'][0]['name'], self.unitlesson.addedBy.username)
        self.assertEquals(json_content['addMessages'][0]['html'], self.unitlesson.lesson.title)
        self.assertEquals(json_content['addMessages'][1]['type'], 'message')
        self.assertEquals(
            json_content['addMessages'][1]['html'], md2html(self.unitlesson.lesson.text)
        )
        self.assertEquals(json_content['addMessages'][2]['type'], 'message')
        # TODO need to figure out how to find action help for Node
        # self.assertEquals(json_content['addMessages'][2]['html'], CHAT_END.get_help())


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
        Test get resources message by id from /resources response.

        Checks that returned content fits resources API documentation.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        chat_id = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code,)), follow=True
        ).context['chat_id']
        response = self.client.get(reverse('chat:resources-list'), {'chat_id': chat_id}, follow=True)
        json_content = json.loads(response.content)
        resource_response = self.client.get(
            reverse('chat:resources-detail', args=(json_content['breakpoints'][0]['ul'],)),
            {'chat_id': chat_id}
        )
        self.assertEquals(resource_response.status_code, 200)
        resource_response = self.client.get(
            reverse('chat:resources-detail', args=(json_content['breakpoints'][1]['ul'],)),
            {'chat_id': chat_id}
        )
        self.assertEquals(resource_response.status_code, 200)
        json_content = json.loads(resource_response.content)
        self.assertIsInstance(json_content['input'], dict)
        self.assertIsInstance(json_content['addMessages'], list)
        self.assertEquals(len(json_content['addMessages']), 3)

        self.assertIn('nextMessagesUrl', json_content)
        self.assertIsNone(json_content['nextMessagesUrl'])
        self.assertIn('id', json_content)

        self.assertEquals(json_content['addMessages'][0]['name'], self.resource_unitlesson.addedBy.username)
        self.assertEquals(json_content['addMessages'][0]['type'], 'breakpoint')
        self.assertEquals(json_content['addMessages'][0]['html'], self.resource_unitlesson.lesson.title)
        self.assertEquals(json_content['addMessages'][1]['type'], 'message')
        self.assertEquals(
            json_content['addMessages'][1]['html'], md2html(self.resource_unitlesson.lesson.text)
        )
        self.assertEquals(json_content['addMessages'][2]['type'], 'message')
        self.assertEquals(json_content['addMessages'][2]['html'], END.help)

        self.assertIn('url', json_content['input'])
        self.assertIn('includeSelectedValuesFromMessages', json_content['input'])
        self.assertIn('html', json_content['input'])
        self.assertIn('type', json_content['input'])
        self.assertIn('options', json_content['input'])


class InternalMessageSerializerTests(SetUpMixin, TestCase):
    """
    Tests for InternalMessageSerializer.
    """
    def test_serializer_data(self):
        """
        Check that InternalMessageSerializer result fits documentation.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        chat_id = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code,)), follow=True
        ).context['chat_id']
        response = self.client.get(reverse('chat:history'), {'chat_id': chat_id}, follow=True)
        json_content = json.loads(response.content)
        msg_id = json_content['addMessages'][0]['id']
        msg = Message.objects.get(id=msg_id)
        result = InternalMessageSerializer().to_representation(msg)
        attrs = ('id', 'type', 'name', 'userMessage', 'avatar', 'html')
        for attr in attrs:
            self.assertIn(attr, result)


class InputSerializerTests(SetUpMixin, TestCase):
    """
    Tests for InputSerializer.
    """
    def test_serializer_data(self):
        """
        Check that InputSerializer result fits documentation.
        """
        input_data = {
            'type': 'custom',
            'url': None,
            'options': ['option1', 'option2'],
            'includeSelectedValuesFromMessages': [],
            'html': 'some html'
        }
        result = InputSerializer().to_representation(input_data)
        attrs = ('type', 'url', 'options', 'includeSelectedValuesFromMessages', 'html')
        for attr in attrs:
            self.assertIn(attr, result)


class MesasageSerializerTests(SetUpMixin, TestCase):
    """
    Tests for MessageSerializer.
    """
    def setUp(self):
        inj = injections.Container()
        inj['next_handler'] = TestHandler()
        self.MessageSerializerForTest = inj.inject(MessageSerializer)
        super(MesasageSerializerTests, self).setUp()

    def test_serializer_data(self):
        """
        Check that MessageSerializer result fits documentation.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        chat_id = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code,)), follow=True
        ).context['chat_id']
        response = self.client.get(reverse('chat:history'), {'chat_id': chat_id}, follow=True)
        json_content = json.loads(response.content)
        msg_id = json_content['addMessages'][0]['id']
        msg = Message.objects.get(id=msg_id)

        result = self.MessageSerializerForTest().to_representation(msg)

        attrs = ('id', 'input', 'addMessages', 'nextMessagesUrl')
        for attr in attrs:
            self.assertIn(attr, result)


class ChatProgressSerializerTests(SetUpMixin, TestCase):
    """
    Tests for ChatProgressSerializer.
    """
    def test_serializer_data(self):
        """
        Check that ChatProgressSerializer result fits documentation.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        chat_id = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code,)), follow=True
        ).context['chat_id']

        result = ChatProgressSerializer().to_representation(Chat.objects.get(id=chat_id))

        attrs = ('progress', 'breakpoints')
        for attr in attrs:
            self.assertIn(attr, result)


class ChatHistorySerializerTests(SetUpMixin, TestCase):
    """
    Tests for ChatHistorySerializer.
    """
    def test_serializer_data(self):
        """
        Check that ChatHistorySerializer result fits documentation.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        chat_id = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code,)), follow=True
        ).context['chat_id']

        result = ChatHistorySerializer().to_representation(Chat.objects.get(id=chat_id))

        attrs = ('input', 'addMessages')
        for attr in attrs:
            self.assertIn(attr, result)


class LessonSerializerTests(SetUpMixin, TestCase):
    """
    Tests for LessonSerializer.
    """
    def test_serializer_data(self):
        """
        Check that LessonSerializer result fits documentation.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        chat_id = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code,)), follow=True
        ).context['chat_id']
        response = self.client.get(reverse('chat:history'), {'chat_id': chat_id}, follow=True)
        json_content = json.loads(response.content)
        msg_id = json_content['addMessages'][1]['id']
        msg = Message.objects.get(id=msg_id)

        result = LessonSerializer().to_representation(msg.content)

        attrs = (
            'id',
            'html',
            'isUnlocked',
            'isDone'
        )
        for attr in attrs:
            self.assertIn(attr, result)

        self.assertEquals(result['id'], msg_id)
        self.assertEquals(result['html'], msg.content.lesson.title)
