# coding=utf-8

import json

from ddt import ddt, data, unpack
from django.test import TestCase, Client
from django.test.utils import override_settings
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
from ..views import ChatInitialView, CourseletPreviewView, ChatAddLessonView, CheckChatInitialView


class CustomTestCase(TestCase):
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
        lesson = Lesson(title='title', text=u'きつね', addedBy=self.user, url='/test/url/')
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
        # TODO remove this later
        self.unit_dummy = Unit(title='Test title', addedBy=self.user)
        self.unit_dummy.save()
        lesson_dummy = Lesson(title='Hope you\'ve overcame the misconception',
                              text=u'Hope you\'ve overcame the misconception',
                              addedBy=self.user, url='/test/url/')
        lesson_dummy.save()
        self.unitlesson_dummy = UnitLesson(
            unit=self.unit_dummy, lesson=lesson_dummy, addedBy=self.user, treeID=lesson_dummy.id
        )
        self.unitlesson_dummy.save()

    @staticmethod
    def compile_html(resource):
        if resource.lesson.url:
            raw_html = u'`Read more <{0}>`_ \n\n{1}'.format(
                resource.lesson.url,
                resource.lesson.text
            )
        else:
            raw_html = resource.lesson.text

        return md2html(raw_html)


@override_settings(SUSPEND_SIGNALS=True)
class MainChatViewTests(CustomTestCase):
    """
    Tests for main view.

    Should enroll user if not enrolled.
    Should render main_view.html template.
    """
    fixtures = ['chat/tests/fixtures/initial_data_enchanced.json']

    def get_course_unit(self):
        return CourseUnit.objects.get(id=1)

    def test_main_view_enroll(self):
        """
        MainView should enroll Student that comes w/ enrollCode.
        """
        course_unit = self.get_course_unit()
        enroll_code = EnrollUnitCode.get_code(course_unit)
        self.client.login(username='test', password='test')

        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        chat_id = json_content.get('id')

        response = self.client.get(reverse('chat:chat_enroll', args=(enroll_code, chat_id)), follow=True)
        self.assertTemplateUsed(response, 'chat/main_view.html')
        self.assertTrue(
            Role.objects.filter(role=Role.ENROLLED, user=self.user, course=course_unit.course).exists()
        )

    def test_not_enroll_second_time(self):
        """
        Should not enroll second time if already enrolled.
        """
        enroll_code = EnrollUnitCode.get_code(self.get_course_unit())
        self.client.login(username='test', password='test')
        role = Role(role=Role.ENROLLED, course=self.course, user=self.user)
        role.save()
        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        chat_id = json_content['id']

        response = self.client.get(reverse('chat:chat_enroll', args=(enroll_code, chat_id)), follow=True)
        self.assertEquals(
            Role.objects.filter(role=Role.ENROLLED, user=self.user, course=self.course).count(),
            1
        )

    def test_only_logged_in(self):
        """
        Only logged in users can access chat ui.
        """
        enroll_code = EnrollUnitCode.get_code(self.get_course_unit())
        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        chat_id = json_content.get('id')
        self.assertIsNone(chat_id)
        self.assertFalse(response.status_code == 404)

        response = self.client.get(reverse('chat:chat_enroll', args=(enroll_code,)), follow=True)
        self.assertTemplateUsed(response, 'psa/new_custom_login.html')

    def test_404_on_non_existent_enroll_code(self):
        """
        Should return 404 if enrollCode is not exists.
        """
        self.client.login(username='test', password='test')
        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': 'nonexistentenrollcode',
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertTrue(response.status_code == 404)

        json.loads(response.content)

        response = self.client.get(
            reverse('chat:chat_enroll', args=('nonexistentenrollcode', )), follow=True
        )
        self.assertIsInstance(response, HttpResponseNotFound)

    def test_passed_correct_variables(self):
        """
        Check that view fill template w/ correct varibles.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        chat_id = json_content['id']
        self.assertNotIsInstance(response, HttpResponseNotFound)

        response = self.client.get(reverse('chat:chat_enroll', args=(enroll_code, chat_id)), follow=True)
        variables = (
            ('course', self.course),
            ('unit', self.unit),
            ('lesson_cnt', len(self.unit.get_exercises())),
            ('duration', len(self.unit.get_exercises()) * 3),
        )
        for pair in variables:
            try:
                val_check = response.context[pair[0]]
            except KeyError:
                val_check = None
            self.assertEquals(val_check, pair[1])

        self.assertIn('fsmstate', response.context)
        self.assertIn('lessons', response.context)
        self.assertIn('chat_id', response.context)
        self.assertIn('will_learn', response.context)
        self.assertIn('need_to_know', response.context)
        self.assertIn('chat', response.context)
        self.assertIn('chat_sessions', response.context)

    def test_chat_init_api(self):
        enroll_code = EnrollUnitCode.get_code(self.courseunit)

        lesson1 = Lesson(title='title1', text=u'きつね', kind='orct', addedBy=self.user, url='/test/url/')
        lesson1.save()

        lesson2 = Lesson(title='title2', text=u'きつね', kind='orct', addedBy=self.user, url='/test/url/')
        lesson2.save()

        self.unitlesson1 = UnitLesson(
            unit=self.unit, order=1, lesson=lesson1, addedBy=self.user, treeID=lesson1.id
        )
        self.unitlesson1.save()

        self.unitlesson2 = UnitLesson(
            unit=self.unit, order=2, lesson=lesson2, addedBy=self.user, treeID=lesson2.id
        )
        self.unitlesson2.save()
        self.client.login(username='test', password='test')

        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        self.assertTrue(response.status_code == 200)
        self.assertTrue(bool(json_content['id']))
        self.assertTrue(bool(json_content['session']))

    # @patch('chat.views.ChatInitialView.next_handler.start_point', return_value=Mock())
    @patch('chat.api.InitNewChat.get_view')
    def test_next_handler_start_point_called_once(self, get_view):
        """
        Check that ChatInitialView.next_handler.start_point called once.
        """
        course_unit = self.get_course_unit()
        enroll_code = EnrollUnitCode.get_code(course_unit)

        start_point = Mock()
        view = ChatInitialView()
        view.next_handler = Mock(start_point=start_point)
        get_view.return_value = view

        self.client.login(username='test', password='test')
        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        start_point.assert_called_once()

        chat_id = json_content.get('id')

        self.assertTrue(response.status_code == 200)

        start_point.assert_called_once()

        self.client.get(reverse('chat:chat_enroll', args=(enroll_code, chat_id)), follow=True)
        response = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code, chat_id)), follow=True
        )
        start_point.assert_called_once()


@override_settings(SUSPEND_SIGNALS=True)
class MessagesViewTests(CustomTestCase):
    """
    Test for MessagesView API.
    """
    fixtures = ['chat/tests/fixtures/initial_data_enchanced.json']

    def _push_continue(self, next_url, chat_id):
        """
        Click Continue button to roll forward to the next Message.
        """
        response = self.client.put(
            next_url,
            data=json.dumps({"option": 1, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        return json_content['input']['url'], json_content

    def test_positive_case(self):
        """
        Check positive case for MessagesView response.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        chat_id = json_content['id']
        self.assertNotIsInstance(response, HttpResponseNotFound)

        response = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code, chat_id)), follow=True
        )
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
        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        chat_id = json_content['id']
        self.assertNotIsInstance(response, HttpResponseNotFound)

        response = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code, chat_id)), follow=True
        )
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
        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        chat_id = json_content['id']
        self.assertNotIsInstance(response, HttpResponseNotFound)

        response = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code, chat_id)), follow=True
        )
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
        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        chat_id = json_content['id']
        self.assertNotIsInstance(response, HttpResponseNotFound)

        response = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code, chat_id)), follow=True
        )
        response = self.client.get(
            reverse('chat:history'), {'chat_id': chat_id}, follow=True
        )
        json_content = json.loads(response.content)

        next_url = json_content['input']['url']

        next_url, _ = self._push_continue(next_url, chat_id)

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
        self.assertEquals(json_content['addMessages'][0]['html'], u'<p>My Answer</p>\n')

    def test_typical_chat_flow(self):
        """
        Check for typical chat flow.
        """
        course_unit = Course.objects.all()[0].get_course_units()[0]
        enroll_code = EnrollUnitCode.get_code(course_unit)

        self.client.login(username='test', password='test')

        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        chat_id = json_content['id']

        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        chat_id = json_content['id']
        self.assertNotIsInstance(response, HttpResponseNotFound)

        response = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code, chat_id)), follow=True
        )

        # get history
        response = self.client.get(
            reverse('chat:history'), {'chat_id': chat_id}, follow=True
        )
        json_content = json.loads(response.content)

        next_url = json_content['input']['url']

        next_url, _ = self._push_continue(next_url, chat_id)

        # post answer
        answer = 'My Answer'
        response = self.client.put(
            next_url,
            data=json.dumps({"text": answer, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        # get next message (confidence)
        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        self.assertIsNotNone(json_content['input']['options'])
        self.assertEquals(len(json_content['addMessages']), 2)

        # confidence answer
        conf = json_content['input']['options'][2]['value']
        conf_text = json_content['input']['options'][2]['text']

        response = self.client.put(
            next_url,
            data=json.dumps({"option": conf, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        self.assertEquals(json_content['addMessages'][0]['html'], conf_text)

        # self eval answer
        self_eval = json_content['input']['options'][2]['value']
        self_eval_text = json_content['input']['options'][2]['text']

        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        self.assertIsNotNone(json_content['input']['options'])
        self.assertEquals(len(json_content['addMessages']), 2)

        response = self.client.put(
            next_url,
            data=json.dumps({"option": self_eval, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        self.assertEquals(json_content['addMessages'][0]['html'], self_eval_text)

        # get next question (2)
        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        self.assertEquals(len(json_content['addMessages']), 3)
        self.assertEquals(json_content['addMessages'][0]['html'], self_eval_text)

        # post answer (2)
        response = self.client.put(
            next_url,
            data=json.dumps({"text": answer, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        # get next message (confidence) (2)
        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        # confidence answer
        conf = json_content['input']['options'][2]['value']
        conf_text = json_content['input']['options'][2]['text']

        response = self.client.put(
            next_url,
            data=json.dumps({"option": conf, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        # get next message - self eval (2)
        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        self.assertEquals(json_content['addMessages'][0]['html'], conf_text)

        self_eval = json_content['input']['options'][0]['value']

        # self eval answer (2)
        response = self.client.put(
            next_url,
            data=json.dumps({"option": self_eval, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        # get next message - error models
        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        self.assertNotIn(
            'data-selectable-value="80"', json_content['addMessages'][-1]['html']
        )

        # Lesson from fixtures
        lesson = Lesson.objects.get(id=78)
        lesson.add_unit_aborts = True
        lesson.save()

        # get the same message - error models
        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        self.assertIn(
            'data-selectable-value="80"', json_content['addMessages'][-1]['html']
        )

        next_url = json_content['input']['url']
        msg_id = json_content['input']['includeSelectedValuesFromMessages'][0]

        # TODO select error model 80 after changing the flow
        # {"selected": {msg_id: {"errorModel": ["80"]}}
        # post error model answer
        response = self.client.put(
            next_url,
            data=json.dumps({"selected": {}, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        # get next message - question (3)
        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        next_url, json_content = self._push_continue(next_url, chat_id)

        self.assertEquals(json_content['input']['type'], 'text')
        # Response should contain only DIVIDER and Question (ORCT) itself
        self.assertEquals(len(json_content['addMessages']), 2)

        # post answer (3)
        response = self.client.put(
            next_url,
            data=json.dumps({"text": answer, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        # get next message - confidence (3)
        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        # post confidence answer (3)
        conf = json_content['input']['options'][2]['value']
        conf_text = json_content['input']['options'][2]['text']

        response = self.client.put(
            next_url,
            data=json.dumps({"option": conf, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )
        json_content = json.loads(response.content)
        self.assertEquals(json_content['addMessages'][0]['html'], conf_text)

        next_url = json_content['input']['url']

        # get next message - self eval (3)
        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        self_eval = json_content['input']['options'][1]['value']

        # post self eval answer (3
        response = self.client.put(
            next_url,
            data=json.dumps({"option": self_eval, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        # get next message - error models (3)
        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']
        msg_id = json_content['input']['includeSelectedValuesFromMessages'][0]

        # post error model (3)
        response = self.client.put(
            next_url,
            data=json.dumps({"selected": {msg_id: {"errorModel": ["104"]}}, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        # TODO: what's going on after this line? WRITE COMMENTS!!!
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
            '<dl>\n<dt><strong>Re: Em1</strong></dt>\n<dd><p>Em1 description</p>\n</dd>\n</dl>\n'
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

    def test_preview_forbidden(self):
        """
        Check that ON author can't access preview page.
        """
        course_unit = Course.objects.all()[0].get_course_units()[0]

        response = self.client.login(username='test', password='test')
        enroll = EnrollUnitCode.get_code_for_user_chat(
            course_unit=course_unit,
            is_live=False,
            user=User.objects.get(username='test'),
            is_preview=True
        )

        response = self.client.get(
            reverse('chat:preview_courselet',
                    kwargs={'enroll_key': enroll.enrollCode}),
        )
        assert 'This Courselet is not published yet or you have no permisions to open it.' in response.content


class HistoryAPIViewTests(CustomTestCase):
    """
    Tests /history API.
    """
    def test_positive_response(self):
        """
        Test positive case for /history call.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')

        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        chat_id = json_content['id']

        chat_id = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code, chat_id)), follow=True
        ).context['chat_id']
        response = self.client.get(reverse('chat:history'), {'chat_id': chat_id}, follow=True)
        self.assertEquals(response.status_code, 200)

    def test_permission_denied(self):
        """
        Check that chat history can be viewed by chat author only.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        chat_id = json_content['id']

        chat_id = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code, chat_id)), follow=True
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
        lesson = self.unitlesson.lesson
        lesson.text = u'🦊'
        lesson.save()
        self.client.login(username='test', password='test')
        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        chat_id = json_content['id']

        chat_id = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code, chat_id)), follow=True
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
            json_content['addMessages'][1]['html'],
            self.compile_html(self.unitlesson)
        )
        self.assertEquals(json_content['addMessages'][2]['type'], 'message')
        # TODO need to figure out how to find action help for Node
        # self.assertEquals(json_content['addMessages'][2]['html'], CHAT_END.get_help())


@override_settings(SUSPEND_SIGNALS=True)
class NumbersTest(CustomTestCase):
    """Tests to check numbers functionality."""

    fixtures = ['chat/tests/fixtures/initial_numbers.json']

    def test_typical_chat_flow(self):
        """
        Check for typical chat flow.
        """
        course_unit = Course.objects.get(title='numbers course').get_course_units()[0]
        enroll_code = EnrollUnitCode.get_code(course_unit)

        self.client.login(username='alex', password='123')

        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        chat_id = json_content['id']

        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        chat_id = json_content['id']
        self.assertNotIsInstance(response, HttpResponseNotFound)

        response = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code, chat_id)), follow=True
        )

        # get history
        response = self.client.get(
            reverse('chat:history'), {'chat_id': chat_id}, follow=True
        )
        json_content = json.loads(response.content)
        self.assertEquals(json_content['input']['subType'], 'numbers')

        next_url = json_content['input']['url']

        # post answer
        not_correct_answer = 'SOmeText'
        answer = '1'

        response = self.client.put(
            next_url,
            data=json.dumps({"text": not_correct_answer, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        self.assertEquals({'error': 'Not correct value!'}, json_content)

        response = self.client.put(
            next_url,
            data=json.dumps({"text": answer, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        # get next message (confidence)
        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        self.assertIsNotNone(json_content['input']['options'])
        self.assertEquals(len(json_content['addMessages']), 2)

        # confidence answer
        conf = json_content['input']['options'][2]['value']
        conf_text = json_content['input']['options'][2]['text']

        response = self.client.put(
            next_url,
            data=json.dumps({"option": conf, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        self.assertEquals(json_content['addMessages'][0]['html'], conf_text)

        # self eval answer
        self_eval = json_content['input']['options'][2]['value']
        self_eval_text = json_content['input']['options'][2]['text']

        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        self.assertIsNotNone(json_content['input']['options'])
        self.assertEquals(len(json_content['addMessages']), 2)

        response = self.client.put(
            next_url,
            data=json.dumps({"option": self_eval, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        self.assertEquals(json_content['addMessages'][0]['html'], self_eval_text)

        # get next question (2)
        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        self.assertEquals(json_content['input']['subType'], 'numbers')

        self.assertEquals(len(json_content['addMessages']), 4)  # + 1 message for grading

        self.assertEquals(json_content['addMessages'][0]['html'], self_eval_text)

        grading_msg = u'Your answer is partially correct!'
        self.assertEquals(json_content['addMessages'][1]['html'], grading_msg)

        # post answer (2)
        response = self.client.put(
            next_url,
            data=json.dumps({"text": answer, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        # get next message (confidence) (2)
        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        # confidence answer
        conf = json_content['input']['options'][2]['value']
        conf_text = json_content['input']['options'][2]['text']

        response = self.client.put(
            next_url,
            data=json.dumps({"option": conf, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        # get next message - self eval (2)
        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        self.assertEquals(json_content['addMessages'][0]['html'], conf_text)

        self_eval = json_content['input']['options'][0]['value']

        # self eval answer (2)
        response = self.client.put(
            next_url,
            data=json.dumps({"option": self_eval, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        # get next message - error models
        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        self.assertNotIn(
            'data-selectable-value=""', json_content['addMessages'][-1]['html']
        )

        # Lesson from fixtures
        lesson = Lesson.objects.get(id=78)
        lesson.add_unit_aborts = True
        lesson.save()

        # get the same message - error models
        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        self.assertIn(
            'data-selectable-value="128"', json_content['addMessages'][-1]['html']
        )

        next_url = json_content['input']['url']
        msg_id = json_content['input']['includeSelectedValuesFromMessages'][0]

        # TODO select error model 80 after changing the flow
        # {"selected": {msg_id: {"errorModel": ["80"]}}
        # post error model answer
        response = self.client.put(
            next_url,
            data=json.dumps({"selected": {}, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        # # get next message - question (3)
        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )
        json_content = json.loads(response.content)
        next_url = json_content['input']['url']
        self.assertEquals(next_url, None)


class ProgressAPIViewTests(CustomTestCase):
    """
    Tests for /progress API.
    """
    def test_positive_response(self):
        """
        Test positive case for /progress call.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        chat_id = json_content['id']

        response = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code, chat_id)), follow=True
        )
        response = self.client.get(reverse('chat:progress'), {'chat_id': chat_id}, follow=True)
        self.assertEquals(response.status_code, 200)

    def test_permission_denied(self):
        """
        Check that chat progress can be viewed by chat author only.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        chat_id = json_content['id']

        response = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code, chat_id)), follow=True
        )
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
        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        chat_id = json_content['id']

        response = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code, chat_id)), follow=True
        )
        response = self.client.get(reverse('chat:progress'), {'chat_id': chat_id}, follow=True)

        json_content = json.loads(response.content)
        self.assertIsInstance(json_content['progress'], int)
        self.assertIsInstance(json_content['breakpoints'], list)
        self.assertEquals(len(json_content['breakpoints']), 1)
        self.assertEquals(json_content['progress'], 1)
        self.assertEquals(json_content['breakpoints'][0]['html'], self.unitlesson.lesson.title)
        self.assertEquals(json_content['breakpoints'][0]['isDone'], True)
        self.assertEquals(json_content['breakpoints'][0]['isUnlocked'], True)


class ResourcesViewTests(CustomTestCase):
    """
    Tests for /resources API call.
    """
    def test_positive_case(self):
        """
        Test positive case for /resources call.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        chat_id = json_content['id']

        response = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code, chat_id)), follow=True
        )
        response = self.client.get(reverse('chat:resources-list'), {'chat_id': chat_id}, follow=True)
        self.assertEquals(response.status_code, 200)

    def test_permission_denied(self):
        """
        Check that chat resources can be viewed by chat author only.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        chat_id = json_content['id']

        response = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code, chat_id)), follow=True
        )
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
        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        chat_id = json_content['id']

        response = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code, chat_id)), follow=True
        )
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
        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        chat_id = json_content['id']

        response = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code, chat_id)), follow=True
        )
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
            json_content['addMessages'][1]['html'],
            self.compile_html(self.resource_unitlesson)
        )
        self.assertEquals(json_content['addMessages'][2]['type'], 'message')
        self.assertEquals(json_content['addMessages'][2]['html'], END.help)

        self.assertIn('url', json_content['input'])
        self.assertIn('includeSelectedValuesFromMessages', json_content['input'])
        self.assertIn('html', json_content['input'])
        self.assertIn('type', json_content['input'])
        self.assertIn('options', json_content['input'])


class InternalMessageSerializerTests(CustomTestCase):
    """
    Tests for InternalMessageSerializer.
    """
    def test_serializer_data(self):
        """
        Check that InternalMessageSerializer result fits documentation.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        # no chat session yet, so we need to init it
        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        chat_id = json_content['id']
        response = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code, chat_id)), follow=True
        )
        response = self.client.get(reverse('chat:history'), {'chat_id': chat_id}, follow=True)
        json_content = json.loads(response.content)
        msg_id = json_content['addMessages'][0]['id']
        msg = Message.objects.get(id=msg_id)
        result = InternalMessageSerializer().to_representation(msg)
        attrs = ('id', 'type', 'name', 'userMessage', 'avatar', 'html')
        for attr in attrs:
            self.assertIn(attr, result)


class InputSerializerTests(CustomTestCase):
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
            'html': 'some html',
            'doWait': False
        }
        result = InputSerializer().to_representation(input_data)
        attrs = ('type', 'url', 'options', 'includeSelectedValuesFromMessages', 'html', 'doWait')
        for attr in attrs:
            self.assertIn(attr, result)


class MesasageSerializerTests(CustomTestCase):
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
        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        chat_id = json_content['id']

        response = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code, chat_id)), follow=True
        )
        response = self.client.get(reverse('chat:history'), {'chat_id': chat_id}, follow=True)
        json_content = json.loads(response.content)
        msg_id = json_content['addMessages'][0]['id']
        msg = Message.objects.get(id=msg_id)

        result = self.MessageSerializerForTest().to_representation(msg)

        attrs = ('id', 'input', 'addMessages', 'nextMessagesUrl')
        for attr in attrs:
            self.assertIn(attr, result)


class ChatProgressSerializerTests(CustomTestCase):
    """
    Tests for ChatProgressSerializer.
    """
    def test_serializer_data(self):
        """
        Check that ChatProgressSerializer result fits documentation.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        # no chat session yet, so we need to init it
        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        chat_id = json_content['id']
        response = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code, chat_id)), follow=True
        )

        result = ChatProgressSerializer().to_representation(Chat.objects.get(id=chat_id))

        attrs = ('progress', 'breakpoints')
        for attr in attrs:
            self.assertIn(attr, result)


class ChatHistorySerializerTests(CustomTestCase):
    """
    Tests for ChatHistorySerializer.
    """
    def test_serializer_data(self):
        """
        Check that ChatHistorySerializer result fits documentation.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')
        # no chat session yet, so we need to init it
        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        chat_id = json_content['id']
        response = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code, chat_id)), follow=True
        )

        result = ChatHistorySerializer().to_representation(Chat.objects.get(id=chat_id))

        attrs = ('input', 'addMessages')
        for attr in attrs:
            self.assertIn(attr, result)


class LessonSerializerTests(CustomTestCase):
    """
    Tests for LessonSerializer.
    """
    def test_serializer_data(self):
        """
        Check that LessonSerializer result fits documentation.
        """
        enroll_code = EnrollUnitCode.get_code(self.courseunit)
        self.client.login(username='test', password='test')

        # no chat session yet, so we need to init it
        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        chat_id = json_content['id']

        response = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code, chat_id)), follow=True
        )
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


@ddt
class TestChatGetBackUrls(CustomTestCase):
    """
    Test that back_url on chat pages are correct.
    Logic should be:
        - if it is usual course view - back_url should go to LMS
        - if it is course preview - back_url should go to CTMS
        - if it is add lesson by chat - back_url shout go to CTMS
        - if it is course tester - back url should go to LMS
    """
    @unpack
    @data(
        (ChatInitialView, "Course",
         lambda self: reverse(
             'lms:course_view',
             kwargs={'course_id': self.course.id})
         ),
        (CourseletPreviewView, "Return",
         lambda self: reverse(
            'ctms:courslet_view',
            kwargs={
                'course_pk': self.course.id,
                'pk': self.unit.pk
            })
        ),
        (ChatAddLessonView, "Course",
         lambda self: reverse(
             'ctms:courslet_view',
             kwargs={
                 'course_pk': self.course.id,
                 'pk': self.courseunit.id
             })
         ),
        (CheckChatInitialView, "Return",
         lambda self: reverse(
             'lms:tester_course_view',
             kwargs={'course_id': self.course.id})
         )
    )
    def test_back_url(self, cls, valid_name, url_callable):
        kwargs = {'courseUnit': self.courseunit}
        name, url = cls.get_back_url(**kwargs)
        valid_url = url_callable(self)
        self.assertEqual(name, valid_name)
        self.assertEqual(url, valid_url)


class MultipleChoiceTests(CustomTestCase):
    """
    Tests for the Multiple Choice question in the chat.

    Checks:
    - ASCII error
    - Formative flow
    - Concept inventiory flow
    - True multiple selection flow [there is no correct choice]
    """
    def setUp(self):
        super(MultipleChoiceTests, self).setUp()
        self.enroll_code = EnrollUnitCode.get_code(self.courseunit)
        lesson = self.unitlesson.lesson
        lesson.text = u'вопрос?\r\n[choices]\r\n() один\r\nобъяснение\r\n(*) два\r\n'+\
                        u'потому что потому\r\n() три\r\nобъяснение\r\n() четыре\r\nобъяснение'
        lesson.sub_kind = "choices"
        lesson.kind = "orct"
        lesson.addedBy = self.user
        lesson.save()

        lesson2 = Lesson(title='title2', text=u'два', kind='answer', addedBy=self.user)
        lesson2.save()

        self.unitlesson2 = UnitLesson(
            unit=self.unit, kind=UnitLesson.ANSWERS, lesson=lesson2, addedBy=self.user, treeID=lesson2.id,
            parent=self.unitlesson
        )
        self.unitlesson2.save()

        lesson3 = Lesson(title='title3', text=u'1', kind='orct', addedBy=self.user)
        lesson3.save()

        self.unitlesson3 = UnitLesson(
            unit=self.unit, order=1, lesson=lesson3, addedBy=self.user, treeID=lesson3.id
        )
        self.unitlesson3.save()
        self.client.login(username='test', password='test')
        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': self.enroll_code,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        self.chat_id = json_content['id']
        self.assertNotIsInstance(response, HttpResponseNotFound)

        response = self.client.get(
            reverse('chat:chat_enroll', args=(self.enroll_code, self.chat_id)), follow=True
        )

    def get_history(self):
        response = self.client.get(
            reverse('chat:history'), {'chat_id': self.chat_id}, follow=True
        )
        json_content = json.loads(response.content)

        self.assertEquals(json_content['input']['subType'], 'choices')
        next_url = json_content['input']['url']
        return json_content, next_url

    def post_answer(self, json_content, next_url, choices):
        message_id = json_content['input']['includeSelectedValuesFromMessages']
        response = self.client.put(
            next_url,
            data=json.dumps({"options": 1, "selected": {message_id[0]: {"choices": choices}}, "chat_id": self.chat_id}),
            content_type='application/json',
            follow=True
        )
        json_content = json.loads(response.content)
        next_url = json_content['input']['url']
        response = self.client.get(
            next_url, {'chat_id': self.chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']
        self.assertIsNotNone(json_content['input']['options'])
        self.assertEquals(len(json_content['addMessages']), 2)
        return json_content, next_url

    def confidence_answer(self, json_content, next_url):
        conf = json_content['input']['options'][2]['value']
        conf_text = json_content['input']['options'][2]['text']

        response = self.client.put(
            next_url,
            data=json.dumps({"option": conf, "chat_id": self.chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        self.assertEquals(json_content['addMessages'][0]['html'], conf_text)

        response = self.client.get(
            next_url, {'chat_id': self.chat_id}, follow=True
        )
        json_content = json.loads(response.content)
        next_url = json_content['input']['url']
        return json_content, next_url

    def get_and_check_next_question(self, json_content, next_url):
        response = self.client.get(
            next_url, {'chat_id': self.chat_id}, follow=True
        )
        self.assertEquals(response.status_code, 200)

    def test_ascii_valid(self):
        lesson = self.unitlesson.lesson
        lesson.text = u'вопрос?\r\n[choices]\r\n() один\r\nобъяснение\r\n(*) два\r\nпотому что потому\r\n()'+\
                        u' три\r\nобъяснение\r\n() четыре\r\nобъяснение'
        lesson.save()

        json_content, next_url = self.get_history()
        json_content, next_url = self.post_answer(json_content, next_url, [1])
        json_content, next_url = self.confidence_answer(json_content, next_url)

        answer_msg = u"You got it right, the correct answer is: два"
        explanation_msg = u"потому что потому"
        self.assertIn(answer_msg, json_content['addMessages'][1]['html'])
        self.assertIn(explanation_msg, json_content['addMessages'][1]['html'])
        self.assertIn('breakpoint', json_content['addMessages'][2]['type'])

        self.get_and_check_next_question(json_content, next_url)

    def test_ascii_invalid(self):
        lesson = self.unitlesson.lesson
        lesson.text = u'вопрос?\r\n[choices]\r\n() один\r\nобъяснение\r\n(*) два\r\nпотому что потому\r\n()'+\
                        u' три\r\nобъяснение\r\n() четыре\r\nобъяснение'
        lesson.save()

        json_content, next_url = self.get_history()
        json_content, next_url = self.post_answer(json_content, next_url, [0])
        json_content, next_url = self.confidence_answer(json_content, next_url)

        answer_msg = u"The correct answer is: два"
        explanation_msg = u"потому что потому"
        self.assertIn(answer_msg, json_content['addMessages'][1]['html'])
        self.assertIn(explanation_msg, json_content['addMessages'][1]['html'])

        answer_msg = u"You selected: один"
        self.assertIn(answer_msg, json_content['addMessages'][2]['html'])
        self.assertIn('breakpoint', json_content['addMessages'][3]['type'])

        self.get_and_check_next_question(json_content, next_url)

    def test_ascii_void_valid(self):
        lesson = self.unitlesson.lesson
        lesson.text = u'вопрос?\r\n[choices]\r\n() один\r\nобъяснение\r\n() два\r\nпотому что потому\r\n()'+\
                        u' три\r\nобъяснение\r\n() четыре\r\nобъяснение'
        lesson.save()

        json_content, next_url = self.get_history()
        json_content, next_url = self.post_answer(json_content, next_url, [])
        json_content, next_url = self.confidence_answer(json_content, next_url)

        answer_msg = u"You got it right, the correct answer is: " + self.unitlesson2.lesson.title
        explanation_msg = self.unitlesson2.lesson.text
        self.assertIn(answer_msg, json_content['addMessages'][1]['html'])
        self.assertIn(explanation_msg, json_content['addMessages'][1]['html'])
        self.assertIn('breakpoint', json_content['addMessages'][2]['type'])

        self.get_and_check_next_question(json_content, next_url)

    def test_ascii_void_invalid(self):
        lesson = self.unitlesson.lesson
        lesson.text = u'вопрос?\r\n[choices]\r\n() один\r\nобъяснение\r\n(*) два\r\nпотому что потому\r\n()'+\
                        u' три\r\nобъяснение\r\n() четыре\r\nобъяснение'
        lesson.save()

        json_content, next_url = self.get_history()
        json_content, next_url = self.post_answer(json_content, next_url, [])
        json_content, next_url = self.confidence_answer(json_content, next_url)

        answer_msg = u"The correct answer is: два"
        explanation_msg = u"потому что потому"
        self.assertIn(answer_msg, json_content['addMessages'][1]['html'])
        self.assertIn(explanation_msg, json_content['addMessages'][1]['html'])
        self.assertIn('breakpoint', json_content['addMessages'][3]['type'])

        answer_msg = u"You selected: Nothing"
        self.assertIn(answer_msg, json_content['addMessages'][2]['html'])

        self.get_and_check_next_question(json_content, next_url)
